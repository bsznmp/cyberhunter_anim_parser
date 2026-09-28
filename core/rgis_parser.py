# -*- coding: utf-8 -*-
"""
core/rgis_parser.py

Parser para o formato RGIS (common.gis / dongzuoku.gis).
Manifesto do rig: carregado UMA VEZ por sessão.

LAYOUT CONFIRMADO (investigação binária 2026-03-24)
====================================================

  [0x00-0x03]  magic         = b"RGIS"  (0x52474953)
  [0x04-0x07]  version       uint32  (ignorar)
  [0x08-0x0B]  file_version  uint32  (ignorar)
  [0x0C-0x0F]  file_version_mask  uint32  (ignorar)
  [0x10-0x13]  anim_count    uint32
  [0x14-0x17]  bone_count    uint32  ← uint32, diferente do child (uint16)
  [0x18 ...]   bone_entries  bone_count × 64B
                 [0:32]  name ASCII null-padded
                 [32:64] INVESTIGAR: parent_index + extra? ou só padding?
  [...]        bone_trans    bone_count × 40B
                 [0:12]  pos   (3 × float32 LE)
                 [12:28] rot   (4 × float32 LE, XYZW)
                 [28:40] scale (3 × float32 LE)
  [...]        separate_storage  uint32
                 0 = PRS inline nos blocos anim abaixo
                 ≠0 = PRS em arquivos child .gis separados
  [...]        anim_index    anim_count × metadados de clipe
                 ← INVESTIGAR: layout exato quando separate_storage≠0

DIFERENÇAS vs child .gis
=========================
  - Magic bytes presentes (child não tem magic)
  - bone_count como uint32 (child usa uint16 @ 0x60)
  - bone_entry = 64B (child = 32B)
  - bone_trans presente (child não tem)
  - Contém anim_count entradas (child = sempre 1 clipe)
  - Per-bone key_count por canal (child usa key_count global)
"""
from __future__ import annotations

import struct
import logging
from typing import Optional

from core.dto import RGisDTO, AnimIndexEntry, BoneTransform
from core.exceptions import FormatError, EOFError

log = logging.getLogger("RGisParser")

_RGIS_MAGIC = b"RGIS"   # 0x52474953


# ---------------------------------------------------------------------------
# Helpers de leitura sequencial
# ---------------------------------------------------------------------------

def _safe_read(data: bytes, pos: int, n: int, label: str = "") -> bytes:
    end = pos + n
    if end > len(data):
        raise EOFError(
            "RGIS truncado ao ler '{0}'".format(label),
            context={"offset": pos, "expected": n, "remaining": len(data) - pos}
        )
    return data[pos:end]


def _u8(data, pos):  return struct.unpack_from("B", data, pos)[0]
def _u16(data, pos): return struct.unpack_from("<H", data, pos)[0]
def _u32(data, pos): return struct.unpack_from("<I", data, pos)[0]
def _f32(data, pos): return struct.unpack_from("<f", data, pos)[0]


def _read_str(data: bytes, pos: int, length: int) -> str:
    raw = data[pos:pos + length]
    return raw.split(b"\x00")[0].decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Detecção de formato
# ---------------------------------------------------------------------------

def is_rgis(path: str) -> bool:
    """Retorna True se o arquivo começa com magic b'RGIS'."""
    try:
        with open(path, "rb") as fh:
            return fh.read(4) == _RGIS_MAGIC
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Parser principal
# ---------------------------------------------------------------------------

def parse_rgis(path: str) -> RGisDTO:
    """
    Parseia um arquivo RGIS e retorna RGisDTO com bind pose + índice de clipes.

    Campos confirmados: magic, header, bone_count, bone_names, bone_trans,
    separate_storage, anim_count.

    anim_index: populado com nome + fps + bone_count quando possível.
    Layout exato do bloco anim (separate_storage≠0) ainda em investigação
    — ver TODO abaixo.
    """
    with open(path, "rb") as fh:
        raw = fh.read()

    if raw[:4] != _RGIS_MAGIC:
        raise FormatError(
            "Magic inválido — arquivo não é RGIS",
            context={"path": path, "got": raw[:4].hex()}
        )

    dto = RGisDTO()
    dto.source_path = path

    pos = 0

    # ── Header (16B) ────────────────────────────────────────────────────────
    pos += 4                          # magic
    pos += 4                          # version       (ignorar)
    pos += 4                          # file_version  (ignorar)
    pos += 4                          # file_version_mask (ignorar)

    # ── Contagens ────────────────────────────────────────────────────────────
    anim_count = _u32(raw, pos);  pos += 4
    bone_count = _u32(raw, pos);  pos += 4
    dto.anim_count = anim_count
    dto.bone_count = bone_count

    log.info("[%s] anim_count=%d  bone_count=%d", path, anim_count, bone_count)

    # ── Bone entries (bone_count × 64B) ──────────────────────────────────────
    # [0:32]  = nome ASCII null-padded  (CONFIRMADO)
    # [32:64] = INVESTIGAR: parent_index(1B) + extra(31B)?
    #           Por ora lemos apenas o nome e pulamos os 32B extras.
    bone_names = []
    for i in range(bone_count):
        _safe_read(raw, pos, 64, "bone_entry[{0}]".format(i))
        name = _read_str(raw, pos, 32)
        # TODO: os bytes [32:64] de cada bone_entry podem conter:
        #   - parent_index (uint8 ou uint16?)
        #   - flags de bone (IK, câmera, física?)
        #   Investigar com tpose.gis (254 bones × 64B) comparando com mesh skeleton.
        pos += 64
        bone_names.append(name)

    dto.bone_names = bone_names
    log.info("bone_names[0]=%r  bone_names[-1]=%r", bone_names[0] if bone_names else "", bone_names[-1] if bone_names else "")

    # ── bone_trans (bone_count × 40B) — bind pose local ─────────────────────
    # pos + rot + scale = 3×4 + 4×4 + 3×4 = 40B por bone
    bone_trans = []
    for i in range(bone_count):
        _safe_read(raw, pos, 40, "bone_trans[{0}]".format(i))
        px = _f32(raw, pos);     py = _f32(raw, pos+4);   pz = _f32(raw, pos+8)
        rx = _f32(raw, pos+12);  ry = _f32(raw, pos+16);  rz = _f32(raw, pos+20);  rw = _f32(raw, pos+24)
        sx = _f32(raw, pos+28);  sy = _f32(raw, pos+32);  sz = _f32(raw, pos+36)
        pos += 40
        bt = BoneTransform(
            pos   = (px, py, pz),
            rot   = (rx, ry, rz, rw),
            scale = (sx, sy, sz),
        )
        bone_trans.append(bt)

    dto.bone_trans = bone_trans
    log.info("bone_trans[0].pos=%r", bone_trans[0].pos if bone_trans else None)

    # ── separate_storage ────────────────────────────────────────────────────
    separate_storage = _u32(raw, pos);  pos += 4
    dto.separate_storage = separate_storage
    log.info("separate_storage=%d", separate_storage)

    # ── Índice de animações ──────────────────────────────────────────────────
    # TODO: o layout exato do bloco anim quando separate_storage≠0 não está
    # totalmente confirmado. A investigação binária de common.gis é necessária.
    #
    # Hipótese baseada em animation_format.txt:
    #   Cada entrada contém nome (variável) + sample_fps + loop + has_scaled +
    #   prs_flags + accum_flags + pack_prs_flags + bone_separate_flags +
    #   bone_count + key_count.
    #   Quando separate_storage≠0, keys_data pode estar ausente ou apenas
    #   ter key_count sem os keyframes.
    #
    # Por ora: best-effort parsing — lê o que conseguir e para sem crash.
    anim_index = []
    try:
        anim_index = _parse_anim_index(raw, pos, anim_count, separate_storage)
    except Exception as e:
        log.warning("anim_index parse incompleto: %s", e)
        log.warning("Posição ao falhar: 0x%X  Remaining: %d", pos, len(raw) - pos)

    dto.anim_index = anim_index
    log.info("anim_index: %d/%d entradas lidas", len(anim_index), anim_count)

    return dto


# ---------------------------------------------------------------------------
# _parse_anim_index — best-effort, não quebra se formato mudar
# ---------------------------------------------------------------------------

def _parse_anim_index(raw: bytes, pos: int, anim_count: int, separate_storage: int):
    """
    Tenta ler anim_count entradas de metadados de clipe do RGIS.

    INVESTIGAÇÃO PENDENTE: o layout exato das entradas quando separate_storage≠0
    não está confirmado. Este parser implementa a hipótese mais provável baseada
    em animation_format.txt e no layout do child .gis.

    Campos esperados por entrada (hipótese):
      name:               32B ASCII null-padded
      anim_root_name:     32B ASCII null-padded
      bone_count:         uint32
      sample_fps:         uint32
      loop:               uint8
      has_scaled:         uint8
      prs_flags:          uint16
      accum_flags:        uint32
      pack_prs_flags:     uint8
      bone_separate_flags: uint8
      key_count:          uint16
      [SE separate_storage=0: key_times + key_data completos]
      [SE separate_storage≠0: apenas os campos acima, sem PRS]
    """
    entries = []
    for i in range(anim_count):
        if pos + 82 > len(raw):   # mínimo para ler os campos de metadados
            log.warning("EOF antes de ler entrada %d/%d", i, anim_count)
            break

        name           = _read_str(raw, pos, 32);      pos += 32
        _anim_root     = _read_str(raw, pos, 32);      pos += 32   # ignorar (como no child)
        bc             = _u32(raw, pos);               pos += 4
        fps            = _u32(raw, pos);               pos += 4
        loop           = _u8(raw, pos);                pos += 1
        _has_scaled    = _u8(raw, pos);                pos += 1
        _prs_flags     = _u16(raw, pos);               pos += 2
        _accum_flags   = _u32(raw, pos);               pos += 4
        pack_prs_flags = _u8(raw, pos);                pos += 1
        _bone_sep_f    = _u8(raw, pos);                pos += 1
        key_count      = _u16(raw, pos);               pos += 2

        # Se PRS inline (separate_storage=0): pular key_times + key_data
        # Isso ainda precisa de investigação para calcular o tamanho correto
        if separate_storage == 0:
            # key_times: key_count × float32
            pos += key_count * 4
            # key_data: bc entradas × (4B flags + 6B per-bone counts + data)
            # TODO: calcular tamanho exato baseado em per-bone key_counts
            # Por ora, tentativa sem pular key_data — vai falhar para inline
            log.debug("separate_storage=0: pular key_data não implementado para entrada %d", i)

        entry = AnimIndexEntry(
            name           = name,
            fps            = fps if fps > 0 else 30,
            bone_count     = bc,
            key_count      = key_count,
            pack_prs_flags = pack_prs_flags,
            loop           = bool(loop),
        )
        entries.append(entry)

    return entries
