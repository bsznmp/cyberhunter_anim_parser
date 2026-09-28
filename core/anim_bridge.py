# -*- coding: utf-8 -*-
"""
core/anim_bridge.py

A Ponte Universal (Adapter Otimizado).
Lê os bytes Crus da Engenharia Reversa e formata instantaneamente pro padrao NeoX
sem sobrecarregar a CPU, criando o DTO usado no Blender e na Tela 3D.

Pipeline em duas camadas:
  Camada 1 (sessão): RGisDTO de common.gis / dongzuoku.gis
    → bind pose canônica (bone_trans)
    → tabela de nomes (bone_names)
    → índice de clipes (anim_index)
  Camada 2 (sob demanda): child .gis individual
    → PRS stream do clipe específico
    → AnimClipDTO consumido por AnimSequenceWrapper
"""

from core.dto import AnimClipDTO, BoneTrackDTO


def _build_track_times(global_times, fps, target_len):
    """
    Constrói timeline compatível com a quantidade de samples da track.

    Regras:
      - target_len <= 0: []
      - target_len == 1: [0.0]
      - target_len == len(global_times): reutiliza timeline global
      - caso contrário: timeline sintética uniforme no mesmo intervalo total
    """
    if target_len <= 0:
        return []
    if target_len == 1:
        return [0.0]

    if global_times and len(global_times) == target_len:
        return list(global_times)

    if global_times and len(global_times) > 1:
        duration = float(global_times[-1])
    else:
        duration = (target_len - 1) / float(fps if fps > 0.0 else 30.0)

    if duration <= 0.0:
        return [i / float(fps if fps > 0.0 else 30.0) for i in range(target_len)]

    step = duration / float(target_len - 1)
    return [i * step for i in range(target_len)]


def load_and_align_animation(gis_path, rgis_dto=None):
    """
    Carrega e converte um child .gis para AnimClipDTO.

    rgis_dto: RGisDTO opcional (common.gis / dongzuoku.gis já carregado).
      Se fornecido:
        - o nome do clipe é consultado no índice do RGIS para validação
        - AnimClipDTO.rgis_bone_trans é populado com o bind pose canônico
          (útil para compute_cpu_skinning usar em vez do bind do .mesh)
    """
    import os

    if not os.path.exists(gis_path):
        return None

    from core.read_neox_sub_animation import read_gis

    # 1. Parsing Bruto Intacto
    raw_result = read_gis(gis_path)

    # FPS com fallback robusto
    fps = float(getattr(raw_result, "fps", 0.0))
    fps_inherited = getattr(raw_result, "fps_inherited", False)
    if fps <= 0.0 or fps_inherited:
        fps = 30.0

    # 2. Constrói o Contrato Universal
    clip_name = (
        getattr(raw_result, "anim_name", None)
        or os.path.splitext(os.path.basename(gis_path))[0]
    )
    clip_dto = AnimClipDTO(name=clip_name, fps=int(round(fps)))
    # Atachar a variante para o render saber se aplica compensação de eixos
    clip_dto.variant = getattr(raw_result, "variant", "B")

    # 2b. Injetar contexto do RGIS quando disponível
    # AnimClipDTO recebe dois atributos extras (não declarados em __slots__ pois
    # AnimClipDTO usa list — compatível com setattr dinâmico):
    #   .rgis_bone_names : list[str]         — tabela canônica de nomes
    #   .rgis_bone_trans : list[BoneTransform] — bind pose do RGIS
    if rgis_dto is not None:
        clip_dto.rgis_bone_names = rgis_dto.bone_names
        clip_dto.rgis_bone_trans = rgis_dto.bone_trans
        # Validar via índice: se o clipe consta no RGIS, logar metadados
        index_entry = rgis_dto.find_clip(clip_name)
        if index_entry:
            import logging

            logging.getLogger("anim_bridge").info(
                "Clipe '%s' encontrado no RGIS: fps=%d bc=%d kc=%d pack=%d",
                clip_name,
                index_entry.fps,
                index_entry.bone_count,
                index_entry.key_count,
                index_entry.pack_prs_flags,
            )
    else:
        clip_dto.rgis_bone_names = []
        clip_dto.rgis_bone_trans = []

    raw_tracks = getattr(raw_result, "tracks", None)
    if not raw_tracks:
        return clip_dto

    key_count = int(getattr(raw_result, "key_count", 0))

    # Herança Zero-Copy dos tempos originais pré-computados
    raw_times = getattr(raw_result, "key_times", [])

    # Detecta se os tempos são válidos (não garbage)
    times_valid = len(raw_times) > 0 and all(
        isinstance(t, (int, float)) and -1e6 < t < 1e6 for t in raw_times[:3]
    )

    if times_valid:
        last_t = raw_times[-1]
        # Se os tempos são em milissegundos (acima de 100 indica isso)
        if last_t > 100.0:
            clip_times = [t * 0.001 for t in raw_times]
        else:
            clip_times = list(raw_times)
    else:
        # Gerar timeline sintética baseada no key_count e fps conhecidos
        clip_times = [i / fps for i in range(key_count)] if key_count > 0 else []

    for raw_track in raw_tracks:
        b_name_raw = getattr(raw_track, "name", "Unknown")
        # Limpar lixo binário (\0, \r, \n) e caracteres de controle
        import re

        b_name = re.sub(r"[\x00-\x1F\x7F-\x9F]", "", b_name_raw).strip()

        track_dto = BoneTrackDTO(b_name)

        pos_keys = (
            list(raw_track.pos_keys)
            if hasattr(raw_track, "pos_keys") and raw_track.pos_keys is not None
            else []
        )
        rot_keys = (
            list(raw_track.rot_keys)
            if hasattr(raw_track, "rot_keys") and raw_track.rot_keys is not None
            else []
        )
        scale_keys = (
            list(raw_track.scale_keys)
            if hasattr(raw_track, "scale_keys") and raw_track.scale_keys is not None
            else []
        )

        if pos_keys:
            track_dto.positions = pos_keys
        if rot_keys:
            track_dto.rotations = rot_keys
        if scale_keys:
            track_dto.scales = scale_keys

        # Layout E pode carregar key_count local por bone. Evita mismatch de
        # índices entre track.times e values no sampler.
        dynamic_lengths = [
            len(track_dto.positions),
            len(track_dto.rotations),
            len(track_dto.scales),
        ]
        dynamic_lengths = [n for n in dynamic_lengths if n > 1]
        track_len = max(dynamic_lengths) if dynamic_lengths else 1
        track_dto.times = _build_track_times(clip_times, fps, track_len)

        clip_dto.bone_tracks.append(track_dto)

    return clip_dto
