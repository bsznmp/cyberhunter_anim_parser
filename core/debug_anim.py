# -*- coding: utf-8 -*-
"""
core/debug_anim.py

Debug de eixos e skinning. Ative com DEBUG_ANIM = True no app.py ou diretamente.
Imprime os valores críticos de cada estágio do pipeline de animação:

  Estágio A — Raw PRS do GIS (saída do parser, antes de qualquer transform)
  Estágio B — local_matrix por bone (após BoneTran.to_matrix + .T)
  Estágio C — skin_matrix = global * inv_bind (o que realmente deforma o vértice)
  Estágio D — sample de vértice antes/depois do skinning

Uso:
    from core.debug_anim import dump_raw_prs, dump_skin_matrices, dump_vertex_sample
"""
import numpy as np

_SEP = "─" * 60


def dump_raw_prs(raw_result, max_bones=3):
    """
    Estágio A: PRS bruto do SubAnimResult (saída do read_gis).
    Chame em anim_bridge.py logo após raw_result = read_gis(gis_path).
    """
    print("\n" + _SEP)
    print(f"[DEBUG-A] RAW PRS do GIS  —  layout={getattr(raw_result,'layout','?')}"
          f"  codec={getattr(raw_result,'rot_codec','?')}"
          f"  fps={getattr(raw_result,'fps','?')}")
    tracks = getattr(raw_result, 'tracks', [])
    for i, t in enumerate(tracks[:max_bones]):
        p0 = t.pos_keys[0]   if t.pos_keys   else None
        r0 = t.rot_keys[0]   if t.rot_keys   else None
        s0 = t.scale_keys[0] if t.scale_keys else None
        print(f"  bone[{i}] '{t.name}'")
        print(f"    P[0] = {_fmt(p0)}")
        print(f"    R[0] = {_fmt(r0)}  (XYZW)")
        print(f"    S[0] = {_fmt(s0)}")
    if len(tracks) > max_bones:
        print(f"  ... (+{len(tracks)-max_bones} bones omitidos)")
    print(_SEP)


def dump_skin_matrices(skel_bones, local_matrices, global_matrices, skin_matrices,
                       bone_idx_map, max_bones=3):
    """
    Estágio B+C: matrizes por bone.
    Chame em compute_cpu_skinning após montar local_matrices e skin_matrices.

    Nota: para global_matrices passe o dict {bone_index: 4x4} preenchido por get_global_mat.
    """
    print("\n" + _SEP)
    print("[DEBUG-B/C] MATRIZES DE SKINNING por bone")
    for bone in list(skel_bones)[:max_bones]:
        bi = bone.index
        lm = local_matrices.get(bi)
        gm = global_matrices.get(bi)
        sm = skin_matrices[bi] if bi < len(skin_matrices) else None
        bm = bone.bind_matrix

        print(f"\n  bone[{bi}] '{bone.name}'  parent={bone.parent_index}")
        print(f"  bind_matrix (raw do mesh):\n{_mat(bm)}")
        print(f"  bind_matrix.T:\n{_mat(bm.T)}")
        print(f"  local_matrix (anim ou bind fallback):\n{_mat(lm)}")
        print(f"  global_matrix:\n{_mat(gm)}")
        print(f"  skin_matrix (global @ inv_bind):\n{_mat(sm)}")

        # Diagnóstico: se skin_matrix == Identity na bind pose está correto
        if sm is not None:
            diff = np.abs(sm - np.eye(4)).max()
            print(f"  → desvio da identidade na bind pose: {diff:.6f}"
                  f"  {'OK' if diff < 0.01 else '<<< SUSPEITO'}")
    print(_SEP)


def dump_vertex_sample(mesh_dto, verts_skinned, bone_mapping, indices=(0, 1, 2)):
    """
    Estágio D: compara vértices originais vs skinned para detectar explosão/flip de eixo.
    Chame em compute_cpu_skinning antes de retornar v_final[:, :3].
    """
    print("\n" + _SEP)
    print("[DEBUG-D] SAMPLE DE VÉRTICES  —  original(NeoX) vs skinned(NeoX)")
    orig = np.array(mesh_dto.positions, dtype='f4')
    for i in indices:
        if i >= len(orig):
            continue
        o = orig[i]
        s = verts_skinned[i] if verts_skinned is not None and i < len(verts_skinned) else None
        delta = np.array(s) - o if s is not None else None
        print(f"  vert[{i}]  orig=({o[0]:+.4f}, {o[1]:+.4f}, {o[2]:+.4f})"
              + (f"  skin=({s[0]:+.4f}, {s[1]:+.4f}, {s[2]:+.4f})"
                 f"  Δ=({delta[0]:+.4f}, {delta[1]:+.4f}, {delta[2]:+.4f})"
                 if s is not None else "  skin=None"))
    print(_SEP)


def dump_bone_poses(bone_poses, max_bones=3):
    """
    Estágio 2.5: dict {bone_name: {P,R,S}} produzido por sample_all_channels.
    Chame em app.py _on_slider_changed logo após bone_poses = ...sample_all_channels(t).
    """
    print("\n" + _SEP)
    print("[DEBUG-2.5] BONE POSES (sample_all_channels output)")
    for i, (name, prs) in enumerate(list(bone_poses.items())[:max_bones]):
        if name.startswith('_'):
            continue
        print(f"  '{name}'")
        print(f"    P = {_fmt(prs.get('P'))}")
        print(f"    R = {_fmt(prs.get('R'))}  (XYZW)")
        print(f"    S = {_fmt(prs.get('S'))}")
    print(_SEP)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _fmt(v):
    if v is None:
        return "None"
    return "({})".format(", ".join(f"{x:+.5f}" for x in v))

def _mat(m):
    if m is None:
        return "    None"
    arr = np.array(m)
    rows = []
    for row in arr:
        rows.append("    [" + "  ".join(f"{v:+.4f}" for v in row) + "]")
    return "\n".join(rows)
