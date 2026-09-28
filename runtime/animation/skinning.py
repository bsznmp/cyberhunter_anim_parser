# -*- coding: utf-8 -*-
"""
runtime/animation/skinning.py
O Motor Matemático de CPU Skinning.
Inclui normalização agressiva de nomes para garantir o máximo de matches.
"""

import logging

import numpy as np

_SKINNING_DEBUG_DONE = False  # reset ao reiniciar o app
_ROOT_INJECT_ROTATION = False
_ROOT_TRACK_ROTATION = False
_PRINT_AUDIT = False
_PRINT_DEBUG_MATRICES = False

logger = logging.getLogger("runtime.skinning")


def _build_trs_matrix_col(P, R, S):
    """Matriz TRS em convenção coluna (translação na última coluna)."""
    px, py, pz = P
    qx, qy, qz, qw = R
    sx, sy, sz = S

    rot = np.array(
        [
            [
                1 - 2 * (qy * qy + qz * qz),
                2 * (qx * qy - qz * qw),
                2 * (qx * qz + qy * qw),
                0.0,
            ],
            [
                2 * (qx * qy + qz * qw),
                1 - 2 * (qx * qx + qz * qz),
                2 * (qy * qz - qx * qw),
                0.0,
            ],
            [
                2 * (qx * qz - qy * qw),
                2 * (qy * qz + qx * qw),
                1 - 2 * (qx * qx + qy * qy),
                0.0,
            ],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype="f4",
    )
    scale = np.diag([sx, sy, sz, 1.0]).astype("f4")
    trans = np.eye(4, dtype="f4")
    trans[0, 3] = px
    trans[1, 3] = py
    trans[2, 3] = pz
    return np.dot(np.dot(trans, rot), scale)


def get_canonical_name(name: str) -> str:
    """Normalização unificada com suporte a sinônimos."""
    import re

    if not name:
        return ""
    res = name.lower()
    # 1. Remoção de prefixos e sujeira
    res = re.sub(
        r"^(bip\d*|ik|wp|slot|mount|cam|biped|bone|mount|dummy)[_\.\s]?", "", res
    )
    res = re.sub(r"[^a-z0-9]", "", res)

    # 2. Tabela de Sinônimos (Mapeamento Léxico)
    synonyms = {
        "pelvis": "hips",
        "hip": "hips",
        "spine01": "spine",
        "neck01": "neck",
        "thigh": "leg",
        "calf": "leg_lower",
        "clavicle": "shoulder",
    }
    return synonyms.get(res, res)


def build_bone_mapping(skel_bones, anim_tracks):
    """
    Constrói um mapa de Bone Index -> Track Name com Auditoria de Erros.
    """
    bone_map = {}
    exact_matches = []
    heuristic_matches = []
    failed_mesh_bones = []

    gis_names = [t.bone_name for t in anim_tracks]

    # 2. Cache do GIS por chave canônica (mantém ambiguidade explícita).
    gis_map = {}
    for name in gis_names:
        key = get_canonical_name(name)
        gis_map.setdefault(key, []).append(name)

    # 3. Processamento de Match
    for bone in skel_bones:
        b_name = bone.name

        # Match Exato
        if b_name in gis_names:
            bone_map[bone.index] = b_name
            exact_matches.append(b_name)
            continue

        # Match Canônico Unificado
        c_name = get_canonical_name(b_name)
        targets = gis_map.get(c_name, [])

        if len(targets) == 1:
            target = targets[0]
            bone_map[bone.index] = target
            heuristic_matches.append(f"{b_name} -> {target}")
        elif len(targets) > 1:
            # Evita bind incorreto por colisão de nome canônico.
            failed_mesh_bones.append(f"{b_name} [ambiguous:{'|'.join(targets[:3])}]")
        else:
            failed_mesh_bones.append(b_name)

    # 4. Report de Auditoria
    mapped_targets = set(bone_map.values())
    lost_gis = [name for name in gis_names if name not in mapped_targets]

    if _PRINT_AUDIT:
        print("\n" + "=" * 50)
        print(" [SKINNING AUDIT] Resumo de Binding")
        print("-" * 50)
        print(f"  Matches Exatos:       {len(exact_matches)}")
        print(f"  Matches Heuristicos:  {len(heuristic_matches)}")
        print(f"  Nao Animados (MESH):  {len(failed_mesh_bones)}")
        print(f"  Tracks GIS Perdidas:  {len(lost_gis)}")
        if failed_mesh_bones:
            sample = ", ".join(failed_mesh_bones[:20])
            if len(failed_mesh_bones) > 20:
                sample += "..."
            print(f"    -> Bones estaticos: {sample}")
        if 0 < len(lost_gis) < 40:
            print(f"    -> GIS perdidos: {', '.join(lost_gis)}")
        print("=" * 50 + "\n")
    else:
        logger.debug(
            "Bone mapping: exact=%d heuristic=%d unmapped_mesh=%d lost_gis=%d",
            len(exact_matches),
            len(heuristic_matches),
            len(failed_mesh_bones),
            len(lost_gis),
        )
    return bone_map


def safe_inv(m):
    """Inversão de matriz segura contra singularidade."""
    try:
        if abs(np.linalg.det(m)) < 1e-12:
            return np.identity(4, dtype="f4")
        return np.linalg.inv(m)
    except:
        return np.identity(4, dtype="f4")


def compute_cpu_skinning(mesh_dto, bone_poses_dict, mapping_cache=None):
    """
    Deforma os vértices originais na CPU.
    mapping_cache: Dicionário {bone_index: anim_track_name} gerencial do bind.
    """
    skel = mesh_dto.skeleton
    if not skel or not mapping_cache:
        return None

    num_verts = len(mesh_dto.positions)
    indices_tmp = np.array(mesh_dto.joint_indices, dtype="i4")
    max_b = max(b.index for b in skel.bones) if skel.bones else 0
    safe_size = max(max_b, indices_tmp.max()) + 1

    skin_matrices = np.zeros((safe_size, 4, 4), dtype="f4")
    for i in range(safe_size):
        skin_matrices[i] = np.eye(4, dtype="f4")

    local_matrices = {}
    bone_idx_map = {b.index: b for b in skel.bones}

    # Contexto opcional vindo do app/AnimClipDTO para retarget de base (RGIS -> mesh).
    rgis_names = bone_poses_dict.get("_rgis_bone_names") or []
    rgis_trans = bone_poses_dict.get("_rgis_bone_trans") or []
    rgis_local_by_name = {}
    if rgis_names and rgis_trans and len(rgis_names) == len(rgis_trans):
        for i, n in enumerate(rgis_names):
            bt = rgis_trans[i]
            try:
                rgis_local_by_name[n] = _build_trs_matrix_col(bt.pos, bt.rot, bt.scale)
            except Exception:
                continue

    mesh_local_bind = {}
    for bone in skel.bones:
        child_g_bind = bone.bind_matrix.T
        if bone.parent_index >= 0:
            parent_g_bind = bone_idx_map[bone.parent_index].bind_matrix.T
            mesh_local_bind[bone.index] = np.dot(safe_inv(parent_g_bind), child_g_bind)
        else:
            mesh_local_bind[bone.index] = child_g_bind

    # 2. Computar Matrizes Locais para este frme
    for bone in skel.bones:
        anim_key = mapping_cache.get(bone.index)
        pose = bone_poses_dict.get(anim_key) if anim_key else None

        if pose:
            P, R, S = (
                pose.get("P", (0, 0, 0)),
                pose.get("R", (0, 0, 0, 1)),
                pose.get("S", (1, 1, 1)),
            )

            # Em alguns rigs, a rotação do bone raiz no GIS está em base diferente
            # do bind da malha. Nesse caso, forçamos root em T-only para evitar
            # personagem deitado durante o playback.
            is_root_like = bone.parent_index == -1
            if not is_root_like and bone.parent_index in bone_idx_map:
                parent_name = (bone_idx_map[bone.parent_index].name or "").lower()
                if parent_name == "dummy_root":
                    is_root_like = True

            if is_root_like and not _ROOT_TRACK_ROTATION:
                R = (0.0, 0.0, 0.0, 1.0)
                S = (1.0, 1.0, 1.0)

            # PROTEÇÃO 1: Clamping de Escala (Evita Overflow)
            S = (
                max(0.001, min(10.0, S[0])),
                max(0.001, min(100.0, S[1])),
                max(0.001, min(100.0, S[2])),
            )

            # PROTEÇÃO 2: Verificação de Sanidade Facial/Corrupção
            if (
                not all(np.isfinite(P))
                or not all(np.isfinite(R))
                or not all(np.isfinite(S))
            ):
                pose = None  # Forçar fallback para bind pose se houver NaN/Inf nos dados brutos
            else:
                anim_local = _build_trs_matrix_col(P, R, S)

                # Retarget opcional: converte do bind local RGIS para o bind local da mesh.
                # Reduz rotação oposta/torção quando a base do rig do clipe diverge da mesh.
                rgis_local = rgis_local_by_name.get(anim_key)
                mesh_bind_local = mesh_local_bind.get(bone.index)
                if rgis_local is not None and mesh_bind_local is not None:
                    a = np.dot(
                        np.dot(anim_local, safe_inv(rgis_local)), mesh_bind_local
                    )
                    b = np.dot(
                        np.dot(mesh_bind_local, safe_inv(rgis_local)), anim_local
                    )
                    da = float(np.linalg.norm(a - mesh_bind_local))
                    db = float(np.linalg.norm(b - mesh_bind_local))
                    local_matrices[bone.index] = a if da <= db else b
                else:
                    local_matrices[bone.index] = anim_local

        if not pose:
            # FALLBACK RIGOROSO: Local Bind Pose (Posição relativa ao pai no .mesh)
            # Isso é vital para arquivos truncados (Graceful Recovery)
            local_matrices[bone.index] = mesh_local_bind[bone.index]

    # Injetar GIS 'root' nos bones raiz do mesh (Layout A: 'root' no GIS não existe no mesh)
    # Cobre tanto has_dummy_root=True (pre-multiplica dummy) quanto has_dummy_root=False
    # (pre-multiplica o único root, ex: 'biped').
    _root_pose = bone_poses_dict.get("root")
    _root_unmapped = "root" not in mapping_cache.values()
    if _root_pose is not None and _root_unmapped:
        _rP = _root_pose.get("P")
        _rR = _root_pose.get("R")
        _rS = _root_pose.get("S", (1.0, 1.0, 1.0))
        if (
            _rP is not None
            and _rR is not None
            and all(np.isfinite(_rP))
            and all(np.isfinite(_rR))
        ):
            if not _ROOT_INJECT_ROTATION:
                _rR = (0.0, 0.0, 0.0, 1.0)
                _rS = (1.0, 1.0, 1.0)
            _root_mat = _build_trs_matrix_col(_rP, _rR, _rS)
            _roots_injected = []
            for _b in skel.bones:
                if _b.parent_index == -1:
                    local_matrices[_b.index] = np.dot(
                        _root_mat, local_matrices[_b.index]
                    )
                    _roots_injected.append(_b.name)
            mode = "TRS" if _ROOT_INJECT_ROTATION else "T-only"
            logger.debug("Root injection mode=%s roots=%s", mode, _roots_injected)

    # 2. Acumular Hierarquia Mundial
    global_matrices = {}

    def get_global_mat(b_idx):
        if b_idx in global_matrices:
            return global_matrices[b_idx]
        local_mat = local_matrices[b_idx]
        parent_idx = bone_idx_map[b_idx].parent_index

        # 1. Obter matriz do pai
        if parent_idx >= 0:
            p_mat = get_global_mat(parent_idx)
            # Acúmulo
            global_mat = np.dot(p_mat, local_mat)
        else:
            global_mat = local_mat

        # 2. PROTEÇÃO ANTAL-EXPLOSÃO (Scale/Math Check)
        # Se os dados do GIS estiverem corrompidos, a matriz global pode explodir.
        if not np.all(np.isfinite(global_mat)):
            # Se explodiu, forçamos a Bind Pose (Identidade no espaço mundial seria errado,
            # mas aqui global_mat é usado para skinning, então vamos resetar para Bind Pose do pai * bind local)
            global_mat = np.identity(4, dtype="f4")

        global_matrices[b_idx] = global_mat
        return global_mat

    # 3. Gerar Matrizes de Skinning
    for bone in skel.bones:
        g_mat = get_global_mat(bone.index)

        # Se a matriz mundial calculada for identidade (devido a erro),
        # a matriz de skinning (g_mat * inv_bind) fará o osso ir para o centro (0,0,0).
        # É preferível que o osso fique na Bind Pose (Skinning Matrix = Identidade).
        if np.array_equal(g_mat, np.identity(4, dtype="f4")):
            skin_matrices[bone.index] = np.identity(4, dtype="f4")
        else:
            inv_bind = safe_inv(bone.bind_matrix.T)
            skin_matrices[bone.index] = np.dot(g_mat, inv_bind)

    # DEBUG B/C opcional: roda uma vez (frame 0)
    global _SKINNING_DEBUG_DONE
    if _PRINT_DEBUG_MATRICES and not _SKINNING_DEBUG_DONE:
        _SKINNING_DEBUG_DONE = True
        _SEP = "-" * 60
        print(
            f"\n{_SEP}\n[DEBUG-B/C] MATRIZES DE SKINNING (primeiros 3 bones, frame 0)"
        )
        for _bone in skel.bones[:3]:
            _bi = _bone.index
            _lm = local_matrices.get(_bi)
            _gm = global_matrices.get(_bi)
            _sm = skin_matrices[_bi]
            _bm = _bone.bind_matrix
            _diff = float(np.abs(_sm - np.eye(4)).max())
            print(f"\n  bone[{_bi}] '{_bone.name}'  parent={_bone.parent_index}")
            print(f"  bind_matrix raw:\n{_bm}")
            print(f"  bind_matrix.T:\n{_bm.T}")
            print(f"  local_matrix:\n{_lm}")
            print(f"  global_matrix:\n{_gm}")
            print(f"  skin_matrix:\n{_sm}")
            print(
                f"  desvio da identidade: {_diff:.6f}  "
                f"{'OK' if _diff < 0.01 else '<<< SUSPEITO'}"
            )
        print(_SEP)
    # 4. CPU Linear Blending Skinning via Numpy (Vectorized)
    v_orig = np.array(mesh_dto.positions, dtype="f4")
    v_orig_4d = np.hstack([v_orig, np.ones((num_verts, 1), dtype="f4")])
    v_final = np.zeros_like(v_orig_4d)

    indices = np.array(mesh_dto.joint_indices, dtype="i4")
    weights = np.array(mesh_dto.joint_weights, dtype="f4")

    # Aplicar os 4 pesos de influência
    for i in range(4):
        b_idx = indices[:, i]
        b_wgt = weights[:, i].reshape(-1, 1)
        # Matmul otimizada por vértice
        v_final += b_wgt * np.einsum("nij,nj->ni", skin_matrices[b_idx], v_orig_4d)

    return v_final[:, :3]
