#
# read_neox_sub_animation.py
# By analogy with zeno_animation.cpp (zhouhang, 2024/3/28)
#
# Parser resiliente para todos os layouts .gis conhecidos do engine NeoX.
# O layout correto é detectado automaticamente a partir dos bytes do arquivo.
#
# ─── LAYOUTS CONHECIDOS ──────────────────────────────────────────────────────
#
#  Layout A  SubAnim corpo, variante root@0x40
#            Arquivos: cyberpunk_f, gedou_spawn, baoli_spawn, cannon_01_crouch_reload, ...
#            Discriminante: 0x40-0x5F contém "root"; pack_prs_flags=4; bone_sep=0
#            Codec rot: float32 (4×f32 = 16B/frame)
#            Nota: root@0x40 é atalho de lookup — o root JÁ É bone[-1] na tabela.
#                  O PRS itera exatamente bone_count vezes, nunca bone_count+1.
#
#  Layout B  SubAnim corpo, variante sem root
#            Arquivos: elang_spawn, ...
#            Discriminante: 0x40-0x5F são zeros; pack_prs_flags=4; bone_sep=0
#            Codec rot: float32 (4×f32 = 16B/frame)
#            Nota: root ainda é o último bone da tabela — apenas o campo 0x40 fica vazio.
#
#  Layout C  SubAnim face/especial
#            Arquivos: face_idle, face_start, ...
#            Discriminante: pack_prs_flags=6; fps=0xFFFFFFFF (sentinel "herdar")
#            Codec rot: half_quat IEEE-754 (4×f16 = 8B/frame)
#            Extras: has_scale animado, eye_l/r, ik_foot_*, wp_* na tabela
#
#  Layout D  RGIS container (índice de animações + bind pose)
#            Arquivos: common.gis, dongzuoku.gis
#            Discriminante: magic bytes[0:4] == b'RGIS'
#            Conteúdo: bind pose (N×40B) + N_anim × 1140B de metadados
#            NÃO contém PRS animado — é um índice que referencia outros .gis
#            RGIS pai dos Layout E: common.gis (217 sub-anims, bone_count=254)
#            Os 1140B por sub-anim contêm:
#              - 98B header (3×32B strings + u16 bone_count)
#              - 1020B bloco misto:
#                  +0..+211   (212B) dado global constante do rig
#                  +212..+592 (381B) bitmask fixo por bone_count subset
#                             (254 bones × 12 bits = 381B exatos; mesmo padrão
#                              em common.gis e dongzuoku.gis para o mesmo bc)
#                  +593..+1015 dado variável por sub-anim (curve metadata)
#                  +1016..+1019 (4B) padding
#              - 14B AnimInfo
#              Nota: kc no AnimInfo do RGIS é não-inicializado (0xAAAB).
#                    O kc real vem do .gis externo correspondente.
#
#  Layout E  SubAnim bone_sep=1 — NÃO MAPEADO
#            Arquivos: feixing_spawn_idle, huaban_spawn_idle, e ~29 outros spawn_idle
#            RGIS pai: common.gis (bc=223, pack=4, bone_sep=1 confirmados)
#            Discriminante: bone_separate_flags (AnimInfo+13) != 0
#            pack_prs_flags=260 (float32+bone_sep=1) ou 262 (half_quat+bone_sep=1)
#            Status: PRS usa estrutura diferente; nenhuma hipótese fechou o stream.
#                    Todas as variações testadas:
#                      codec (float32/half_quat/smallest-3), stride alternativo,
#                      SoA por canal, bitmask, padding, bc reduzido/aumentado,
#                      bind pose omitida, PRS_START deslocado ±32B.
#                    Nenhuma fecha o prs_size=350606B do huaban_spawn_idle.
#                    O R1 (381B) do RGIS é idêntico entre bone_sep=0 e bone_sep=1
#                    para o mesmo bc — não contém os flags inline de animação.
#                    Necessário FBX de referência ou engine source para mapear.
#                    Ação: warning no console + M4/M5 tentam ancorar; se falhar,
#                          retorna None.
#
#  DDS falso  Textura com extensão .gis trocada
#             Arquivos: ar09.gis, smg06.gis
#             Discriminante: magic bytes[0:4] == b'DDS '
#             Ação: erro explícito no console — não tentar parsear.
#
# ─── pack_prs_flags: campo uint16 com semântica de produto cartesiano ─────────
#
#  O campo AnimInfo+12 é um uint16 LE onde:
#    byte_low  (AnimInfo+12) = codec:    4=float32  6=half_quat
#    byte_high (AnimInfo+13) = bone_sep: 0=normal   1=Layout E
#
#  Os 4 valores possíveis:
#    4   (0x0004) = float32   + bone_sep=0 → Layouts A/B
#    6   (0x0006) = half_quat + bone_sep=0 → Layout C
#    260 (0x0104) = float32   + bone_sep=1 → Layout E variante float32
#    262 (0x0106) = half_quat + bone_sep=1 → Layout E variante half_quat
#
#  O parser lê os dois bytes separadamente (pack_prs e bone_separate_flags),
#  o que é correto — são os mesmos bytes, apenas com semântica combinada.
#
# ─── bone_count: subconjuntos do rig (rig completo = 254 bones) ───────────────
#
#  O bone_count de cada .gis representa um subconjunto funcional fixo do rig:
#    254 = rig completo (tpose, lobby_emotion)
#    252 = swim/car (2 bones de referência ausentes)
#    223 = personagem std — exclui biped_add01..add09_bone* (roupa/cabelo)
#    220 = armas smg/pistola — inclui eye_l/r, ik_foot_*, mas sem add_bones
#    210 = armas cannon — sem nenhum add_bone
#  A bone table é ordenada alfabeticamente. O índice local do bone em cada
#  arquivo é específico daquele arquivo — usar nome para lookup, nunca índice.
#
# ─── DIVERGÊNCIAS VS zeno_animation.cpp ──────────────────────────────────────
#
#  CPP: rot = read_half_quat (4×float16, 8B)  ← Layout C usa isso ✓
#  CPP: rot = read_half_quat mas arquivo usa float32 (16B) ← Layouts A/B
#  Discriminante correto: pack_prs_flags byte_low (4=float32, 6=half_quat)
#
#  CPP: bone_count imediatamente após anim_root_name (uint16@0x40)
#  Real: 0x40 pode ter "root"(32B) antes do bone_count@0x60
#
#  Manual (Sec.4): fps=uint16; Real: fps=uint32 (4B)
#  Manual (Sec.6): rot=smallest-3; Real: float32 (pack=4) ou half_quat (pack=6)
#  Manual (Sec.7): bloco Havok separado + ghost bones; Real: EOF limpo com 1B
#                  padding após os bone_count bones declarados. Sem ghost bones.
#
# ─── MUDANÇAS NESTA REVISÃO ───────────────────────────────────────────────────
#
#  M1  DDS guard em read_gis(): erro explícito ao encontrar textura falsa.
#
#  M2  Bug "root duplicado" corrigido: loop PRS itera bone_count vezes (não +1).
#      O root@0x40 é metadado — o PRS nunca tem uma entrada extra por causa dele.
#      Impacto: cannon_01_crouch_reload, smg_stand_drop_other e similares agora
#      fecham corretamente sem consumir o byte 0x00 de padding como "bone estático".
#
#  M3  Guard bone_sep != 0 (Layout E): warning sem bloqueio imediato.
#      O M4/M5 tentam ancorar o PRS; se falhar, retorna None com log do drift.
#      31 arquivos confirmados — todos em common.gis com bc=223, pack=4.
#
#  M4  Validação em duas passagens: _validate_prs_stream() roda um parse leve
#      antes do parse completo. Se o stream não fechar em EOF-1, loga o drift.
#
#  M5  Ancoragem reversa condicional: ativada quando M4 detecta drift.
#      Tenta PRS_START ± 32B em steps de 2B. Cobre futuros arquivos com
#      campos extras de alinhamento ou versões ligeiramente diferentes do AnimInfo.
#
#  M6  Discriminante A vs B documentado corretamente nos comentários.
#

from __future__ import annotations

import csv
import json
import logging
import math
import os
import struct
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np

logging.basicConfig(format="%(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger("neox_gis")

# ─── Tipos ───────────────────────────────────────────────────────────────────

Vec3 = Tuple[float, float, float]
Vec4 = Tuple[float, float, float, float]
Mat4 = List[List[float]]
Layout = Literal["A", "B", "C", "D", "E"]
RotCodec = Literal["float32", "half_quat"]


# ─── BinaryReader ─────────────────────────────────────────────────────────────
# Leitura ESTRITAMENTE sequencial — sem seek() no parse principal.
# Princípio "Stream Cego Serializado": nunca assuma offsets fixos.


class BinaryReader:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    def current(self) -> int:
        return self._pos

    def remaining(self) -> int:
        return len(self._data) - self._pos

    def size(self) -> int:
        return len(self._data)

    def peek_bytes(self, n: int) -> bytes:
        return self._data[self._pos : self._pos + n]

    def skip(self, n: int) -> None:
        self._pos += n

    def read_u8(self) -> int:
        v = self._data[self._pos]
        self._pos += 1
        return v

    def read_u16(self) -> int:
        v = struct.unpack_from("<H", self._data, self._pos)[0]
        self._pos += 2
        return v

    def read_u32(self) -> int:
        v = struct.unpack_from("<I", self._data, self._pos)[0]
        self._pos += 4
        return v

    def read_i16(self) -> int:
        v = struct.unpack_from("<h", self._data, self._pos)[0]
        self._pos += 2
        return v

    def read_f32(self) -> float:
        v = struct.unpack_from("<f", self._data, self._pos)[0]
        self._pos += 4
        return v

    def read_vec3(self) -> Vec3:
        v = struct.unpack_from("<3f", self._data, self._pos)
        self._pos += 12
        return v

    def read_quat_f32(self) -> Vec4:
        v = struct.unpack_from("<4f", self._data, self._pos)
        self._pos += 16
        return v

    def read_string(self, length: int) -> str:
        raw = self._data[self._pos : self._pos + length]
        self._pos += length
        return raw.split(b"\x00")[0].decode("utf-8", errors="replace")


# ─── Codecs de rotação ────────────────────────────────────────────────────────


def _ieee_half_to_float(h: int) -> float:
    """glm::detail::toFloat32(int16_t) — IEEE-754 float16 → float32."""
    h = int(h) & 0xFFFF
    sign = (h >> 15) & 0x1
    exp = (h >> 10) & 0x1F
    mant = h & 0x3FF
    if exp == 0:
        val = (mant / 1024.0) * (2.0**-14) if mant else 0.0
    elif exp == 31:
        val = float("inf") if mant == 0 else float("nan")
    else:
        val = (1.0 + mant / 1024.0) * (2.0 ** (exp - 15))
    return -val if sign else val


def _read_half3(reader: BinaryReader) -> Vec3:
    """3 × IEEE-754 float16 = 6B. Codec de escala em todos os layouts."""
    return (
        _ieee_half_to_float(reader.read_i16()),
        _ieee_half_to_float(reader.read_i16()),
        _ieee_half_to_float(reader.read_i16()),
    )


def _read_half_quat(reader: BinaryReader) -> Vec4:
    """4 × IEEE-754 float16 = 8B. Codec de rotação do Layout C (pack_prs=6)."""
    return (
        _ieee_half_to_float(reader.read_i16()),
        _ieee_half_to_float(reader.read_i16()),
        _ieee_half_to_float(reader.read_i16()),
        _ieee_half_to_float(reader.read_i16()),
    )


def _read_rot(reader: BinaryReader, codec: RotCodec) -> Vec4:
    """Despacha para o codec correto baseado em pack_prs."""
    if codec == "half_quat":
        return _read_half_quat(reader)
    return reader.read_quat_f32()


ROT_FRAME_SIZE: Dict[RotCodec, int] = {"float32": 16, "half_quat": 8}


# ─── AnimInfo ─────────────────────────────────────────────────────────────────


@dataclass
class AnimInfo:
    fps: int = 0
    is_loop: int = 0
    has_scaled: int = 0
    prs_flags: int = 0
    accum_flags: int = 0
    pack_prs_flags: int = 0
    bone_separate_flags: int = 0

    FPS_INHERIT = 0xFFFFFFFF  # sentinel: fps herdado do contexto externo (Layout C)

    def read_from_reader(self, reader: BinaryReader) -> None:
        self.fps = reader.read_u32()  # uint32, não uint16
        self.is_loop = reader.read_u8()
        self.has_scaled = reader.read_u8()
        self.prs_flags = reader.read_u16()
        self.accum_flags = reader.read_u32()
        self.pack_prs_flags = reader.read_u8()
        self.bone_separate_flags = reader.read_u8()  # ← Layout E quando != 0

    @property
    def rot_codec(self) -> RotCodec:
        """pack_prs=4 → float32 | pack_prs=6 → half_quat."""
        return "half_quat" if self.pack_prs_flags == 6 else "float32"

    @property
    def fps_inherited(self) -> bool:
        return self.fps == self.FPS_INHERIT


# ─── BoneTran + matrix math ───────────────────────────────────────────────────


@dataclass
class BoneTran:
    pos: Vec3 = (0.0, 0.0, 0.0)
    rot: Vec4 = (0.0, 0.0, 0.0, 1.0)
    scale: Vec3 = (1.0, 1.0, 1.0)

    def snap(self, eps: float = 0.001) -> "BoneTran":
        """Snap near-zero/near-one values — idêntico ao bloco de snapping do cpp."""
        self.pos = tuple(0.0 if abs(v) < eps else v for v in self.pos)
        self.scale = tuple(1.0 if abs(v - 1) < eps else v for v in self.scale)
        self.rot = tuple(
            0.0 if abs(v) < eps else (1.0 if abs(v - 1) < eps else v) for v in self.rot
        )
        return self

    def to_matrix(self) -> np.ndarray:
        """glm::translate(pos) * glm::toMat4(rot) * glm::scale(scale)."""
        tx, ty, tz = self.pos
        qx, qy, qz, qw = self.rot
        sx, sy, sz = self.scale
        R = np.array(
            [
                [
                    1 - 2 * (qy * qy + qz * qz),
                    2 * (qx * qy + qw * qz),
                    2 * (qx * qz - qw * qy),
                    0,
                ],
                [
                    2 * (qx * qy - qw * qz),
                    1 - 2 * (qx * qx + qz * qz),
                    2 * (qy * qz + qw * qx),
                    0,
                ],
                [
                    2 * (qx * qz + qw * qy),
                    2 * (qy * qz - qw * qx),
                    1 - 2 * (qx * qx + qy * qy),
                    0,
                ],
                [0, 0, 0, 1],
            ],
            dtype=np.float64,
        ).T
        T = np.eye(4, dtype=np.float64)
        T[3, 0] = tx
        T[3, 1] = ty
        T[3, 2] = tz
        S = np.diag([sx, sy, sz, 1.0])
        return T @ R @ S


FLIP_X = np.diag([-1.0, 1.0, 1.0, 1.0])  # flip NeoX → Blender


# ─── BoneTrack ────────────────────────────────────────────────────────────────


@dataclass
class BoneTrack:
    name: str
    has_pos_keys: int
    has_rot_keys: int
    has_scale_keys: int
    rot_codec: RotCodec
    pos_keys: List[Vec3] = field(default_factory=list)
    rot_keys: List[Vec4] = field(default_factory=list)
    scale_keys: List[Vec3] = field(default_factory=list)

    def pos_at(self, fi: int) -> Vec3:
        return self.pos_keys[fi if self.has_pos_keys else 0]

    def rot_at(self, fi: int) -> Vec4:
        return self.rot_keys[fi if self.has_rot_keys else 0]

    def scale_at(self, fi: int) -> Vec3:
        return self.scale_keys[fi if self.has_scale_keys else 0]

    def tran_at(self, fi: int) -> BoneTran:
        return BoneTran(self.pos_at(fi), self.rot_at(fi), self.scale_at(fi)).snap()

    def quat_norms(self) -> List[float]:
        return [math.sqrt(sum(v * v for v in q)) for q in self.rot_keys]


# ─── Resultados de parse ──────────────────────────────────────────────────────


@dataclass
class SubAnimResult:
    """Resultado de um arquivo .gis de sub-animação (Layouts A, B, C)."""

    layout: Layout
    anim_name: str
    fps: int
    fps_inherited: bool
    key_count: int
    key_times: List[float]
    rot_codec: RotCodec
    tracks: List[BoneTrack]
    file_size: int
    bytes_read: int

    @property
    def duration_ms(self) -> float:
        return self.key_times[-1] if self.key_times else 0.0

    @property
    def bytes_remaining(self) -> int:
        return self.file_size - self.bytes_read


@dataclass
class RgisSubAnimMeta:
    """Metadados de uma sub-animação dentro de um container RGIS."""

    index: int
    anim_name: str
    bone_count: int
    fps: int
    fps_inherited: bool
    key_count: int
    rot_codec: RotCodec
    is_loop: int
    has_scaled: int


@dataclass
class RgisResult:
    """Resultado de um arquivo RGIS container (Layout D)."""

    layout: Layout
    bone_count: int
    sub_anim_count: int
    sub_anim_stride: int
    bind_pose: List[Tuple[Vec3, Vec4, Vec3]]  # (pos, rot, scale) por bone
    bone_names: List[str]
    sub_anims: List[RgisSubAnimMeta]
    file_size: int
    bytes_verified: bool


# ─── World matrix ─────────────────────────────────────────────────────────────


def _search(
    ci: int,
    matrices: List[np.ndarray],
    c2p: Dict[int, int],
    result: Dict[int, np.ndarray],
) -> None:
    """Composição recursiva pai→filho — equivalente direto ao cpp."""
    if ci in result:
        return
    if ci not in c2p:
        result[ci] = matrices[ci]
    else:
        pi = c2p[ci]
        if pi not in result:
            _search(pi, matrices, c2p, result)
        result[ci] = result[pi] @ matrices[ci]


def compute_world_matrices(
    result: SubAnimResult,
    frame: int,
    c2p: Optional[Dict[int, int]] = None,
) -> Dict[int, np.ndarray]:
    """Calcula matrizes world para um frame sem reler o arquivo."""
    fi = max(0, min(frame, result.key_count - 1))
    local = [t.tran_at(fi).to_matrix() for t in result.tracks]
    world: Dict[int, np.ndarray] = {}
    if c2p:
        for ci in range(len(result.tracks)):
            _search(ci, local, c2p, world)
    else:
        world = {i: m for i, m in enumerate(local)}
    return {i: FLIP_X @ m for i, m in world.items()}


# ─── M4: Validação leve do PRS stream (primeira passagem) ─────────────────────


def _validate_prs_stream(
    data: bytes,
    prs_start: int,
    bone_count: int,
    key_count: int,
    rot_sz: int,
) -> Tuple[bool, int, Optional[str]]:
    """
    Passagem leve sobre o PRS: só lê flags e acumula strides, sem decodificar dados.
    Retorna (ok, pos_final, mensagem_de_erro).

    ok=True significa que todos os bones têm flags em {0,1} e o stream termina
    exatamente em len(data)-1 (o byte 0x00 de padding do EOF).

    Usado como guard antes do parse completo e como diagnóstico de drift.
    """
    pos = prs_start
    n = len(data)
    for bi in range(bone_count):
        if pos + 4 > n:
            return False, pos, f"EOF prematuro no bone {bi}"
        hp = data[pos]
        hr = data[pos + 1]
        hsc = data[pos + 2]
        pos += 4
        if hp > 1 or hr > 1 or hsc > 1:
            return (
                False,
                pos - 4,
                (f"flags inválidas bone {bi}: hp={hp} hr={hr} hsc={hsc}"),
            )
        pos += (key_count if hp else 1) * 12
        pos += (key_count if hr else 1) * rot_sz
        pos += (key_count if hsc else 1) * 6
    remain = n - pos
    return remain == 1, pos, None


def _detect_optional_timeline_block(
    data: bytes,
    pos: int,
    key_count: int,
    max_extra_keys: int = 0,
) -> int:
    """
    Layout E: alguns bones trazem timeline local após os dados PRS do bone.

    Retorna o comprimento total do bloco (2 + n*4) quando detectado,
    ou 0 quando não há bloco de timeline na posição atual.
    """
    n = len(data)
    if pos + 2 > n:
        return 0

    local_count = struct.unpack_from("<H", data, pos)[0]
    if local_count <= 0 or local_count > (key_count + max_extra_keys):
        return 0

    end = pos + 2 + local_count * 4
    if end > n:
        return 0

    t0 = struct.unpack_from("<f", data, pos + 2)[0]
    if abs(t0) > 1e-3:
        return 0

    if local_count >= 2:
        t1 = struct.unpack_from("<f", data, pos + 6)[0]
        tl = struct.unpack_from("<f", data, end - 4)[0]
        if t1 <= t0 or tl < t1 or tl > 200000.0:
            return 0

    return 2 + local_count * 4


def _detect_bone_sep_timeline_header(
    data: bytes,
    pos: int,
    bone_count: int,
) -> int:
    """
    Detecta header de timeline local usado no Layout E.

    Formato observado no stream:
      u16 local_key_count + local_key_count*f32 (timestamps)

    Retorna 0 quando não há header válido na posição atual.
    """
    n = len(data)
    if pos + 2 > n:
        return 0

    local_count = struct.unpack_from("<H", data, pos)[0]
    if local_count <= 1 or local_count > 512:
        return 0

    end = pos + 2 + local_count * 4
    if end > n:
        return 0

    t0 = struct.unpack_from("<f", data, pos + 2)[0]
    if abs(t0) > 1e-3:
        return 0

    sample = min(local_count, 8)
    vals = [struct.unpack_from("<f", data, pos + 2 + 4 * i)[0] for i in range(sample)]
    for i in range(1, len(vals)):
        if vals[i] <= vals[i - 1] or vals[i] > 200000.0:
            return 0

    # Guard anti-falso-positivo: contagens acima de bone_count são raras e
    # aparecem em alguns clipes; nesses casos exigimos passo inicial não nulo.
    if local_count > bone_count and len(vals) >= 2 and vals[1] < 1.0:
        return 0

    return 2 + local_count * 4


def _is_valid_track_flags(data: bytes, pos: int) -> bool:
    """True quando os 3 flags de canal são bool válidos (0/1)."""
    if pos + 4 > len(data):
        return False
    return data[pos] <= 1 and data[pos + 1] <= 1 and data[pos + 2] <= 1


def _channel_key_count(has_keys: int, active_key_count: int) -> int:
    return active_key_count if has_keys else 1


def _track_data_size(
    has_pos: int,
    has_rot: int,
    has_scale: int,
    active_key_count: int,
    rot_sz: int,
) -> int:
    n_p = _channel_key_count(has_pos, active_key_count)
    n_r = _channel_key_count(has_rot, active_key_count)
    n_s = _channel_key_count(has_scale, active_key_count)
    return n_p * 12 + n_r * rot_sz + n_s * 6


def _consume_bone_sep_timeline_headers(
    data: bytes,
    pos: int,
    bone_count: int,
    active_key_count: int,
    max_headers: int = 8,
) -> Tuple[bool, int, int]:
    """
    Consome zero ou mais headers de timeline local antes do bone atual.

    Retorna (ok, nova_pos, novo_active_key_count).
    """
    header_guard = 0
    while True:
        tl_len = _detect_bone_sep_timeline_header(data, pos, bone_count)
        if not tl_len:
            return True, pos, active_key_count
        active_key_count = struct.unpack_from("<H", data, pos)[0]
        pos += tl_len
        header_guard += 1
        if header_guard > max_headers:
            return False, pos, active_key_count


def _read_track_samples(
    reader: BinaryReader,
    codec: RotCodec,
    has_pos: int,
    has_rot: int,
    has_scale: int,
    active_key_count: int,
) -> Tuple[List[Vec3], List[Vec4], List[Vec3]]:
    n_p = _channel_key_count(has_pos, active_key_count)
    pos_keys = [reader.read_vec3() for _ in range(n_p)]

    n_r = _channel_key_count(has_rot, active_key_count)
    rot_keys = [_read_rot(reader, codec) for _ in range(n_r)]

    n_s = _channel_key_count(has_scale, active_key_count)
    scale_keys = [_read_half3(reader) for _ in range(n_s)]

    return pos_keys, rot_keys, scale_keys


def _solve_bone_sep_experimental_path(
    data: bytes,
    prs_start: int,
    bone_count: int,
    key_count: int,
    rot_sz: int,
    max_delta: int = 96,
    max_states: int = 4096,
) -> Optional[List[Tuple[int, bool]]]:
    """
    Resolve um caminho de parse para Layout E half_quat com resync local.

    Retorna lista por bone de (flag_pos, has_local_timeline).
    """
    n = len(data)
    states: Dict[int, int] = {prs_start: 0}  # pos -> custo (bytes skip)
    parents: List[Dict[int, Tuple[int, int, bool]]] = []

    for bi in range(bone_count):
        expected = prs_start + int((bi + 1) * (n - prs_start - 1) / max(1, bone_count))
        next_states: Dict[int, int] = {}
        next_parent: Dict[int, Tuple[int, int, bool]] = {}

        for prev_pos, prev_cost in states.items():
            for delta in range(max_delta + 1):
                flag_pos = prev_pos + delta
                if not _is_valid_track_flags(data, flag_pos):
                    continue

                hp = data[flag_pos]
                hr = data[flag_pos + 1]
                hs = data[flag_pos + 2]

                pos_after = (
                    flag_pos + 4 + _track_data_size(hp, hr, hs, key_count, rot_sz)
                )

                if pos_after > n:
                    continue

                candidates: List[Tuple[int, bool]] = [(pos_after, False)]
                tl_len = _detect_optional_timeline_block(
                    data, pos_after, key_count, max_extra_keys=32
                )
                if tl_len:
                    candidates.append((pos_after + tl_len, True))

                for next_pos, has_tl in candidates:
                    if next_pos > n:
                        continue
                    new_cost = prev_cost + delta
                    old = next_states.get(next_pos)
                    if old is None or new_cost < old:
                        next_states[next_pos] = new_cost
                        next_parent[next_pos] = (prev_pos, flag_pos, has_tl)

        if not next_states:
            return None

        if len(next_states) > max_states:
            ranked = sorted(
                next_states.items(),
                key=lambda kv: (kv[1], abs(kv[0] - expected)),
            )[:max_states]
            keep = {pos for pos, _ in ranked}
            next_states = {pos: cost for pos, cost in ranked}
            next_parent = {pos: rec for pos, rec in next_parent.items() if pos in keep}

        parents.append(next_parent)
        states = next_states

    finals = [(pos, cost) for pos, cost in states.items() if (n - pos) == 1]
    if not finals:
        return None

    end_pos = min(finals, key=lambda kv: kv[1])[0]
    path: List[Tuple[int, bool]] = []
    cur = end_pos
    for bi in range(bone_count - 1, -1, -1):
        prev_pos, flag_pos, has_tl = parents[bi][cur]
        path.append((flag_pos, has_tl))
        cur = prev_pos
    path.reverse()
    return path


def _validate_prs_stream_bone_sep(
    data: bytes,
    prs_start: int,
    bone_count: int,
    key_count: int,
    rot_sz: int,
) -> Tuple[bool, int, Optional[str]]:
    """
    Validação de Layout E (bone_sep=1).

    Modelo observado em arquivos reais:
      - bloco PRS por bone similar ao layout clássico (flags + dados)
      - timeline local opcional após o bloco do bone (u16 count + count*f32)
    """
    pos = prs_start
    n = len(data)
    active_key_count = key_count

    for bi in range(bone_count):
        ok_h, pos, active_key_count = _consume_bone_sep_timeline_headers(
            data, pos, bone_count, active_key_count
        )
        if not ok_h:
            return False, pos, f"loop de timeline header no bone {bi}"

        if pos + 4 > n:
            return False, pos, f"EOF prematuro no bone {bi}"

        hp = data[pos]
        hr = data[pos + 1]
        hsc = data[pos + 2]
        pos += 4

        if hp > 1 or hr > 1 or hsc > 1:
            return (
                False,
                pos - 4,
                (f"flags inválidas bone {bi}: hp={hp} hr={hr} hsc={hsc}"),
            )

        pos += _track_data_size(hp, hr, hsc, active_key_count, rot_sz)

    remain = n - pos
    return remain == 1, pos, None


# ─── M5: Ancoragem reversa (ativada quando M4 detecta drift) ─────────────────


def _anchor_prs_start(
    data: bytes,
    prs_start: int,
    bone_count: int,
    key_count: int,
    rot_sz: int,
    label: str,
) -> Optional[int]:
    """
    Tenta corrigir prs_start varrendo ±32B em steps de 2B.
    Retorna o offset corrigido se encontrar, ou None se falhar.

    A ancoragem funciona porque o arquivo sempre termina com 1B de padding 0x00,
    tornando o EOF uma âncora confiável independente do formato.
    """
    ok, end_pos, err = _validate_prs_stream(
        data, prs_start, bone_count, key_count, rot_sz
    )
    if ok:
        return prs_start  # já estava correto

    drift = end_pos - (len(data) - 1)
    log.warning(
        "[%s] PRS não fecha: drift=%+dB  (%s). Tentando ancoragem reversa.",
        label,
        drift,
        err or "remain!=1",
    )

    for delta in range(-32, 33, 2):
        if delta == 0:
            continue
        candidate = prs_start + delta
        if candidate < 0 or candidate >= len(data):
            continue
        ok2, _, _ = _validate_prs_stream(data, candidate, bone_count, key_count, rot_sz)
        if ok2:
            log.info(
                "[%s] PRS_START corrigido: delta=%+dB (0x%05X -> 0x%05X)",
                label,
                delta,
                prs_start,
                candidate,
            )
            return candidate

    log.warning(
        "[%s] Ancoragem reversa falhou em ±32B — formato não reconhecido. "
        "Arquivo ignorado.",
        label,
    )
    return None


def _anchor_prs_start_bone_sep(
    data: bytes,
    prs_start: int,
    bone_count: int,
    key_count: int,
    rot_sz: int,
    label: str,
) -> Optional[int]:
    """Variante de ancoragem para Layout E (bone_sep=1)."""
    ok, end_pos, err = _validate_prs_stream_bone_sep(
        data, prs_start, bone_count, key_count, rot_sz
    )
    if ok:
        return prs_start

    drift = end_pos - (len(data) - 1)
    log.warning(
        "[%s] PRS bone_sep não fecha: drift=%+dB  (%s). Tentando ancoragem.",
        label,
        drift,
        err or "remain!=1",
    )

    for delta in range(-32, 33, 2):
        if delta == 0:
            continue
        candidate = prs_start + delta
        if candidate < 0 or candidate >= len(data):
            continue

        ok2, _, _ = _validate_prs_stream_bone_sep(
            data, candidate, bone_count, key_count, rot_sz
        )
        if ok2:
            log.info(
                "[%s] PRS_START bone_sep corrigido: delta=%+dB (0x%05X -> 0x%05X)",
                label,
                delta,
                prs_start,
                candidate,
            )
            return candidate

    log.warning(
        "[%s] Ancoragem bone_sep falhou em ±32B — formato não reconhecido. "
        "Arquivo ignorado.",
        label,
    )
    return None


# ─── Parse layouts A/B/C ──────────────────────────────────────────────────────


def _parse_subanim(path: str) -> Optional[SubAnimResult]:
    """
    Parseia um .gis de sub-animação (Layouts A, B, C).

    Retorna None se o arquivo usar um formato não mapeado (Layout E, bone_sep!=0)
    ou se o stream PRS não puder ser ancorado pelo EOF.
    """
    with open(path, "rb") as fh:
        data = fh.read()

    label = os.path.basename(path)
    reader = BinaryReader(data)

    # 1. Header — 3 × read_string(32), leitura estritamente sequencial
    anim_name = reader.read_string(32)  # 0x00-0x1F
    _anim_root = reader.read_string(32)  # 0x20-0x3F  (ignorado como no cpp)
    root_bone_str = reader.read_string(32)  # 0x40-0x5F

    # M6 — Discriminante A vs B:
    # root@0x40 preenchido = Layout A. Zeros = Layout B.
    # Em ambos os casos o root JA E bone[-1] na tabela de nomes.
    # has_root distingue A de B apenas — não adiciona entrada ao PRS.
    has_root = bool(root_bone_str)

    # 2. Bone table
    bone_count = reader.read_u16()  # 0x60-0x61

    # M2 — bone_names lido como bone_count entradas (sem prepend do root@0x40).
    # O PRS itera exatamente bone_count vezes. O root@0x40 é metadado de
    # hierarquia; se já estiver na tabela (bone[-1]='root'), não há entrada extra.
    bone_names = [reader.read_string(32) for _ in range(bone_count)]

    # 3. AnimInfo — leitura sequencial, sem seek
    anim_info = AnimInfo()
    anim_info.read_from_reader(reader)

    # M3 — Aviso Layout E: bone_separate_flags != 0 indica formato diferente.
    # 31 arquivos confirmados com bone_sep=1. O formato PRS é desconhecido mas
    # o arquivo É uma animação válida — não bloquear, apenas avisar.
    # O M4/M5 (validação + ancoragem) decidirá se o stream fecha corretamente.
    if anim_info.bone_separate_flags != 0:
        log.warning(
            "[%s] bone_sep=%d — Layout E (formato nao mapeado). "
            "Tentando parse mesmo assim; resultado pode estar incorreto.",
            label,
            anim_info.bone_separate_flags,
        )

    key_count = reader.read_u16()
    key_times = [reader.read_f32() for _ in range(key_count)]

    # 4. Detectar layout pelo pack_prs (único campo que distingue C de A/B)
    codec = anim_info.rot_codec
    if anim_info.fps_inherited and codec == "half_quat":
        layout: Layout = "C"
    elif has_root:
        layout = "A"
    else:
        layout = "B"

    rot_sz = ROT_FRAME_SIZE[codec]
    prs_start = reader.current()

    log.info(
        "[%s] layout=%s anim=%r fps=%s codec=%s bones=%d frames=%d",
        label,
        layout,
        anim_name,
        "inherit" if anim_info.fps_inherited else anim_info.fps,
        codec,
        bone_count,
        key_count,
    )

    # M4 + M5 — Validação em duas passagens com ancoragem reversa.
    # bone_sep=0 usa validador clássico.
    # bone_sep=1 usa validador com timeline local opcional por bone.
    experimental_path: Optional[List[Tuple[int, bool]]] = None

    if anim_info.bone_separate_flags:
        corrected = _anchor_prs_start_bone_sep(
            data, prs_start, bone_count, key_count, rot_sz, label
        )
    else:
        corrected = _anchor_prs_start(
            data, prs_start, bone_count, key_count, rot_sz, label
        )
    if corrected is None:
        # Fallback experimental para subvariante ainda não documentada:
        # bone_sep=1 + half_quat (pack=6) com resync local por bone.
        if anim_info.bone_separate_flags and codec == "half_quat":
            experimental_path = _solve_bone_sep_experimental_path(
                data, prs_start, bone_count, key_count, rot_sz
            )
            if experimental_path is None:
                return None
            log.warning(
                "[%s] Usando parser experimental bone_sep+half_quat (resync local).",
                label,
            )
            corrected = prs_start
        else:
            return None
    if corrected != prs_start:
        reader.skip(corrected - prs_start)
        prs_start = corrected

    # 5. PRS stream — segunda passagem: parse completo com armazenamento de dados
    tracks: List[BoneTrack] = []

    active_key_count = key_count

    for i in range(bone_count):
        if experimental_path is None and anim_info.bone_separate_flags:
            ok_h, next_pos, active_key_count = _consume_bone_sep_timeline_headers(
                data,
                reader.current(),
                bone_count,
                active_key_count,
            )
            if not ok_h:
                log.warning(
                    "[%s] loop de timeline header no bone %d — arquivo ignorado",
                    label,
                    i,
                )
                return None
            if next_pos != reader.current():
                reader.skip(next_pos - reader.current())

        if experimental_path is not None:
            flag_pos, has_local_timeline = experimental_path[i]
            if reader.current() < flag_pos:
                reader.skip(flag_pos - reader.current())
            elif reader.current() > flag_pos:
                log.debug(
                    "[%s] experimental desync bone=%d reader=0x%X path=0x%X",
                    label,
                    i,
                    reader.current(),
                    flag_pos,
                )
                return None
        else:
            has_local_timeline = False

        # Arquivo termina com 1B de padding 0x00 após o último bone.
        # Chegamos aqui apenas após a validação confirmar que o stream fecha bem.
        if reader.remaining() < 4:
            log.debug("EOF padding at bone %d — done", i)
            break

        has_pos = reader.read_u8()
        has_rot = reader.read_u8()
        has_scale = reader.read_u8()
        _euler = reader.read_u8()  # reservado, ignorado como no cpp

        track = BoneTrack(
            name=bone_names[i] if i < len(bone_names) else f"?{i}",
            has_pos_keys=has_pos,
            has_rot_keys=has_rot,
            has_scale_keys=has_scale,
            rot_codec=codec,
        )

        track.pos_keys, track.rot_keys, track.scale_keys = _read_track_samples(
            reader,
            codec,
            has_pos,
            has_rot,
            has_scale,
            active_key_count,
        )

        if experimental_path is not None:
            if has_local_timeline:
                tl_len = _detect_optional_timeline_block(
                    data, reader.current(), key_count, max_extra_keys=32
                )
                if tl_len:
                    reader.skip(tl_len)
        elif anim_info.bone_separate_flags:
            # Timeline local no Layout E agora é tratada antes de cada bone.
            pass

        tracks.append(track)

    log.info(
        "PRS done: %d/%d bones  %d B read  %d B remain",
        len(tracks),
        bone_count,
        reader.current(),
        reader.remaining(),
    )

    return SubAnimResult(
        layout=layout,
        anim_name=anim_name,
        fps=anim_info.fps,
        fps_inherited=anim_info.fps_inherited,
        key_count=key_count,
        key_times=key_times,
        rot_codec=codec,
        tracks=tracks,
        file_size=len(data),
        bytes_read=reader.current(),
    )


# ─── Parse layout D (RGIS) ────────────────────────────────────────────────────


def _parse_rgis(path: str) -> RgisResult:
    """
    Parseia um container RGIS (Layout D).
    Retorna metadados e bind pose. Não contém PRS animado.
    Para obter o PRS de uma sub-animação, carregue o .gis individual correspondente.
    """
    with open(path, "rb") as fh:
        data = fh.read()

    reader = BinaryReader(data)

    # Header RGIS
    magic = reader.read_string(4)  # "RGIS"
    _ver_a = reader.read_u8()  # version byte (=2)
    _ver_b = reader.read_u8()  # 0
    _ver_c = reader.read_u8()  # 6
    _ver_d = reader.read_u8()  # 3
    sub_count = reader.read_u16()  # número de sub-animações no índice
    bone_count = reader.read_u16()  # bones do rig completo
    _pad = reader.read_u16()  # 0x00 0x00

    log.info(
        "[%s] RGIS  bones=%d  sub_anims=%d",
        os.path.basename(path),
        bone_count,
        sub_count,
    )

    # Bone table: bone_count × 32B
    bone_names = [reader.read_string(32) for _ in range(bone_count)]

    # Bind pose: bone_count × (pos_f32 + quat_f32 + scale_f32) = 40B each
    bind_pose: List[Tuple[Vec3, Vec4, Vec3]] = []
    for _ in range(bone_count):
        p = reader.read_vec3()
        q = reader.read_quat_f32()
        s = reader.read_vec3()
        bind_pose.append((p, q, s))

    # Cabeçalho do bloco de índice
    _sep_storage = reader.read_u16()  # separate_storage flag
    _base_size = reader.read_u16()  # base_size
    sub_stride = reader.read_u32()  # stride fixo em bytes de cada sub-anim block

    # Índice de sub-animações: sub_count × sub_stride bytes
    sub_anims: List[RgisSubAnimMeta] = []
    for ai in range(sub_count):
        block_start = reader.current()

        an = reader.read_string(32)  # anim_name
        _rn = reader.read_string(32)  # root_name (sempre vazio)
        _rb = reader.read_string(32)  # root_bone_name (sempre "root" ou vazio)
        bc = reader.read_u16()  # bone_count desta sub-animação

        # skip(1020): salta keyframes e resumo de canais — não parseado aqui
        reader.skip(1020)

        # AnimInfo resumida (14B) + skip(8B) fixo = fim do bloco de 1140B
        ai_info = AnimInfo()
        ai_info.read_from_reader(reader)

        # Alinhar pelo stride fixo — garante robustez independente de versão
        consumed = reader.current() - block_start
        reader.skip(sub_stride - consumed)

        sub_anims.append(
            RgisSubAnimMeta(
                index=ai,
                anim_name=an,
                bone_count=bc,
                fps=ai_info.fps,
                fps_inherited=ai_info.fps_inherited,
                key_count=0,
                rot_codec=ai_info.rot_codec,
                is_loop=ai_info.is_loop,
                has_scaled=ai_info.has_scaled,
            )
        )

    expected = len(data)
    actual = reader.current()
    ok = actual == expected
    log.info(
        "RGIS index done: %d sub-anims  %d B verified  %s",
        len(sub_anims),
        actual,
        "ok" if ok else f"differ={actual - expected}",
    )

    return RgisResult(
        layout="D",
        bone_count=bone_count,
        sub_anim_count=sub_count,
        sub_anim_stride=sub_stride,
        bind_pose=bind_pose,
        bone_names=bone_names,
        sub_anims=sub_anims,
        file_size=len(data),
        bytes_verified=ok,
    )


# ─── Ponto de entrada universal ───────────────────────────────────────────────


def read_gis(path: str):
    """
    Le qualquer arquivo .gis e retorna o resultado correto.

    Retorna SubAnimResult para layouts A, B, C.
    Retorna RgisResult     para layout D (RGIS container).
    Retorna None           para Layout E (bone_sep!=0, não mapeado)
                           ou quando o stream PRS nao puder ser ancorado.
    Levanta ValueError     para texturas DDS com extensão .gis falsa.
    """
    with open(path, "rb") as fh:
        magic = fh.read(4)

    # M1 — Guard para formatos que não são animação.
    # DDS produz lixo silencioso se não for bloqueado aqui — pior tipo de falha.
    if magic == b"DDS ":
        raise ValueError(
            f"[{os.path.basename(path)}] Textura DDS com extensão .gis falsa "
            f"— nao e animacao. Verificar pipeline de extracao."
        )

    if magic == b"RGIS":
        return _parse_rgis(path)

    return _parse_subanim(path)


# ─── Validação ────────────────────────────────────────────────────────────────


def validate(result: SubAnimResult) -> bool:
    """Verifica norma de todos os quaternions em todos os frames."""
    bad = 0
    for bi, track in enumerate(result.tracks):
        for fi, q in enumerate(track.rot_keys):
            norm = math.sqrt(sum(v * v for v in q))
            if not (0.97 <= norm <= 1.03):
                log.warning("bone %d (%s) frame %d: |q|=%.6f", bi, track.name, fi, norm)
                bad += 1
    if bad == 0:
        log.info("validate: PASS — 0 invalid quaternion norms")
    return bad == 0


# ─── Sumário ──────────────────────────────────────────────────────────────────


def print_summary(result) -> None:
    if result is None:
        print("[IGNORADO] arquivo retornou None — Layout E ou stream nao ancorado")
        return

    if isinstance(result, RgisResult):
        print(
            f"[RGIS container]  bones={result.bone_count}  "
            f"sub_anims={result.sub_anim_count}  stride={result.sub_anim_stride}B"
        )
        print(
            f"  file={result.file_size:,}B  verified={'ok' if result.bytes_verified else 'FAIL'}"
        )
        print(
            f"  Bind pose: {len(result.bind_pose)} bones x 40B (pos_f32+quat_f32+scale_f32)"
        )
        print(f"  Sub-animações (primeiras 10):")
        for sa in result.sub_anims[:10]:
            fps_s = "inherit" if sa.fps_inherited else str(sa.fps)
            print(
                f"    [{sa.index:3d}] {sa.anim_name:30s}  bc={sa.bone_count:3d}  "
                f"fps={fps_s:8s}  codec={sa.rot_codec}"
            )
        if result.sub_anim_count > 10:
            print(f"    ... e mais {result.sub_anim_count - 10} sub-animações")
        return

    r = result
    fps_s = "inherit" if r.fps_inherited else str(r.fps)
    bad = sum(
        1
        for t in r.tracks
        for q in t.rot_keys
        if not (0.97 <= math.sqrt(sum(v * v for v in q)) <= 1.03)
    )
    print(
        f"[layout {r.layout}]  {r.anim_name!r}  "
        f"fps={fps_s}  codec={r.rot_codec}  frames={r.key_count}  bones={len(r.tracks)}"
    )
    if r.key_times:
        print(f"  duration={r.duration_ms / 1000:.3f}s  ({r.duration_ms:.1f}ms)")
    print(
        f"  file={r.file_size:,}B  read={r.bytes_read:,}B  remain={r.bytes_remaining}B"
    )
    print(
        f"  quaternion check: {'PASS — 0 invalid' if bad == 0 else f'FAIL — {bad} invalid'}"
    )
    if r.tracks:
        t0 = r.tracks[0]
        p0 = t0.pos_at(0)
        q0 = t0.rot_at(0)
        s0 = t0.scale_at(0)
        print(
            f"  bone[0] {t0.name!r}:  "
            f"pos=({p0[0]:.3f},{p0[1]:.3f},{p0[2]:.3f})  "
            f"|q|={math.sqrt(sum(v * v for v in q0)):.5f}  "
            f"scale=({s0[0]:.2f},{s0[1]:.2f},{s0[2]:.2f})"
        )


# ─── Export ───────────────────────────────────────────────────────────────────


def export_csv(
    result: SubAnimResult, out_path: str, c2p: Optional[Dict[int, int]] = None
) -> None:
    """
    Exporta CSV com PRS local cru + matrizes world por frame.
    c2p = {child_idx: parent_idx}. Se None, world = local + flip.
    """
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "frame",
                "time_ms",
                "bone_idx",
                "bone_name",
                "has_pos",
                "has_rot",
                "has_scale",
                "rot_codec",
                "pos_x",
                "pos_y",
                "pos_z",
                "quat_x",
                "quat_y",
                "quat_z",
                "quat_w",
                "scale_x",
                "scale_y",
                "scale_z",
                "world_pos_x",
                "world_pos_y",
                "world_pos_z",
                "r0_x",
                "r0_y",
                "r0_z",
                "r1_x",
                "r1_y",
                "r1_z",
                "r2_x",
                "r2_y",
                "r2_z",
            ]
        )
        for fi in range(result.key_count):
            wm = compute_world_matrices(result, fi, c2p)
            t = round(result.key_times[fi], 4)
            for bi, track in enumerate(result.tracks):
                p = track.pos_at(fi)
                q = track.rot_at(fi)
                s = track.scale_at(fi)
                m = wm.get(bi)
                if m is not None:
                    r0 = (float(m[0, 0]), float(m[0, 1]), float(m[0, 2]))
                    r1 = (float(m[1, 0]), float(m[1, 1]), float(m[1, 2]))
                    r2v = np.cross(np.array(r0), np.array(r1))
                    r2 = (float(r2v[0]), float(r2v[1]), float(r2v[2]))
                    wp = (float(m[3, 0]), float(m[3, 1]), float(m[3, 2]))
                else:
                    r0 = r1 = r2 = wp = (0.0, 0.0, 0.0)
                w.writerow(
                    [
                        fi,
                        t,
                        bi,
                        track.name,
                        track.has_pos_keys,
                        track.has_rot_keys,
                        track.has_scale_keys,
                        track.rot_codec,
                        *(round(v, 6) for v in p),
                        *(round(v, 6) for v in q),
                        *(round(v, 6) for v in s),
                        *(round(v, 6) for v in wp),
                        *(round(v, 6) for v in r0),
                        *(round(v, 6) for v in r1),
                        *(round(v, 6) for v in r2),
                    ]
                )


def export_json(result: SubAnimResult, out_path: str) -> None:
    """JSON de inspeção com todos os frames de rot/pos por bone."""

    def _r(v):
        return [round(x, 6) for x in v]

    doc = {
        "anim_name": result.anim_name,
        "layout": result.layout,
        "fps": "inherit" if result.fps_inherited else result.fps,
        "rot_codec": result.rot_codec,
        "key_count": result.key_count,
        "duration_ms": round(result.duration_ms, 3),
        "bone_count": len(result.tracks),
        "file_size": result.file_size,
        "bytes_read": result.bytes_read,
        "key_times_ms": [round(t, 3) for t in result.key_times],
        "tracks": [
            {
                "bone_idx": bi,
                "bone_name": t.name,
                "has_pos_keys": t.has_pos_keys,
                "has_rot_keys": t.has_rot_keys,
                "has_scale_keys": t.has_scale_keys,
                "rot_codec": t.rot_codec,
                "scale_bind": _r(t.scale_keys[0]),
                "pos_frames": [_r(p) for p in t.pos_keys],
                "rot_frames": [_r(q) for q in t.rot_keys],
            }
            for bi, t in enumerate(result.tracks)
        ],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)


def export_rgis_index(result: RgisResult, out_path: str) -> None:
    """JSON do índice RGIS com metadados de todas as sub-animações."""
    doc = {
        "layout": "D",
        "bone_count": result.bone_count,
        "sub_anim_count": result.sub_anim_count,
        "sub_anim_stride": result.sub_anim_stride,
        "file_size": result.file_size,
        "bone_names": result.bone_names,
        "bind_pose": [
            {
                "bone": result.bone_names[i] if i < len(result.bone_names) else f"?{i}",
                "pos": [round(v, 6) for v in p],
                "rot": [round(v, 6) for v in q],
                "scale": [round(v, 6) for v in s],
            }
            for i, (p, q, s) in enumerate(result.bind_pose)
        ],
        "sub_anims": [
            {
                "index": sa.index,
                "anim_name": sa.anim_name,
                "bone_count": sa.bone_count,
                "fps": "inherit" if sa.fps_inherited else sa.fps,
                "rot_codec": sa.rot_codec,
                "is_loop": sa.is_loop,
                "has_scaled": sa.has_scaled,
            }
            for sa in result.sub_anims
        ],
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)


# ─── CLI ──────────────────────────────────────────────────────────────────────


def main() -> None:
    import argparse, time

    ap = argparse.ArgumentParser(
        description="NeoX .gis reader — suporte a layouts A, B, C, D (RGIS); E ignorado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python read_neox_sub_animation.py cyberpunk_f.gis
  python read_neox_sub_animation.py face_idle.gis --csv --json
  python read_neox_sub_animation.py common.gis --json
  python read_neox_sub_animation.py *.gis           (glob via shell)
        """,
    )
    ap.add_argument("paths", nargs="+", help="Arquivo(s) .gis")
    ap.add_argument("--csv", "-c", action="store_true")
    ap.add_argument("--json", "-j", action="store_true")
    ap.add_argument("--validate", "-V", action="store_true")
    ap.add_argument(
        "--frame",
        "-f",
        type=int,
        default=None,
        help="Imprimir PRS de um frame específico (SubAnim apenas)",
    )
    ap.add_argument(
        "--out",
        "-o",
        default=None,
        help="Prefixo de saída (padrão: nome do arquivo sem extensão)",
    )
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    for path in args.paths:
        if not os.path.isfile(path):
            log.error("arquivo não encontrado: %s", path)
            continue

        t0 = time.time()
        try:
            result = read_gis(path)
        except ValueError as exc:
            # M1 — DDS ou outro formato inválido detectado
            log.error("%s", exc)
            print()
            continue

        dt_ms = (time.time() - t0) * 1000

        print_summary(result)
        print(f"  parse: {dt_ms:.1f}ms")

        if result is None:
            print()
            continue

        prefix = args.out or os.path.splitext(path)[0]

        if isinstance(result, RgisResult):
            if args.json:
                out = prefix + "_index.json"
                export_rgis_index(result, out)
                print(f"  [json] {out}")
            print()
            continue

        # SubAnimResult (layouts A, B, C)
        if args.validate:
            validate(result)

        if args.frame is not None:
            fi = max(0, min(args.frame, result.key_count - 1))
            print(f"\n  Frame {fi}  (t={result.key_times[fi]:.1f}ms):")
            for bi, t in enumerate(result.tracks):
                p = t.pos_at(fi)
                q = t.rot_at(fi)
                s = t.scale_at(fi)
                norm = math.sqrt(sum(v * v for v in q))
                print(
                    f"    [{bi:3d}] {t.name:30s}  "
                    f"pos=({p[0]:+.4f},{p[1]:+.4f},{p[2]:+.4f})  "
                    f"|q|={norm:.4f}  sc=({s[0]:.2f},{s[1]:.2f},{s[2]:.2f})"
                )

        if args.csv:
            t1 = time.time()
            out = prefix + "_anim.csv"
            export_csv(result, out)
            rows = result.key_count * len(result.tracks)
            print(
                f"  [csv] {out}  ({rows:,} linhas, {(time.time() - t1) * 1000:.0f}ms)"
            )

        if args.json:
            out = prefix + "_anim.json"
            export_json(result, out)
            print(f"  [json] {out}")

        print()


if __name__ == "__main__":
    main()
