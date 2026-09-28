import struct
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.read_neox_sub_animation import (
    _detect_optional_timeline_block,
    _validate_prs_stream_bone_sep,
    SubAnimResult,
    read_gis,
)


def _pad32(text: str) -> bytes:
    raw = text.encode("utf-8")
    return raw + b"\x00" * (32 - len(raw))


def _half1() -> bytes:
    return struct.pack("<hhh", 0x3C00, 0x3C00, 0x3C00)


def _build_layout_e_sample() -> bytes:
    data = bytearray()

    data += _pad32("anim_e")
    data += _pad32("root")
    data += _pad32("root")

    bone_count = 2
    key_count = 3

    data += struct.pack("<H", bone_count)
    data += _pad32("bone_a")
    data += _pad32("bone_b")

    data += struct.pack("<IBBHI", 30, 0, 1, 7, 0)
    data += struct.pack("<BB", 4, 1)

    data += struct.pack("<H", key_count)
    data += struct.pack("<3f", 0.0, 33.333332, 66.666664)

    # Bone 0: pos animado, rot/scale estáticos, com timeline local opcional.
    data += struct.pack("<BBBB", 1, 0, 0, 0)
    data += struct.pack("<9f", 0.0, 1.0, 2.0, 0.1, 1.1, 2.1, 0.2, 1.2, 2.2)
    data += struct.pack("<4f", 0.0, 0.0, 0.0, 1.0)
    data += _half1()
    data += struct.pack("<H", key_count)
    data += struct.pack("<3f", 0.0, 33.333332, 66.666664)

    # Bone 1: rot animado, sem timeline local.
    data += struct.pack("<BBBB", 0, 1, 0, 0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack(
        "<12f",
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.1,
        0.995,
        0.0,
        0.0,
        0.2,
        0.98,
    )
    data += _half1()

    data += b"\x00"
    return bytes(data)


def _build_layout_e_adaptive_kc_sample() -> bytes:
    data = bytearray()

    data += _pad32("anim_e_adaptive")
    data += _pad32("root")
    data += _pad32("root")

    bone_count = 2
    global_kc = 2
    local_kc = 5

    data += struct.pack("<H", bone_count)
    data += _pad32("bone_a")
    data += _pad32("bone_b")

    data += struct.pack("<IBBHI", 30, 0, 1, 7, 0)
    data += struct.pack("<BB", 4, 1)

    data += struct.pack("<H", global_kc)
    data += struct.pack("<2f", 0.0, 33.333332)

    # Bone 0: estático em todos os canais.
    data += struct.pack("<BBBB", 0, 0, 0, 0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack("<4f", 0.0, 0.0, 0.0, 1.0)
    data += _half1()

    # Header de timeline local antes do bone 1.
    data += struct.pack("<H", local_kc)
    data += struct.pack("<5f", 0.0, 33.333332, 66.666664, 100.0, 133.333328)

    # Bone 1: rotação animada com local_kc=5.
    data += struct.pack("<BBBB", 0, 1, 0, 0)
    data += struct.pack("<3f", 0.0, 0.0, 0.0)
    data += struct.pack(
        "<20f",
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.05,
        0.9987,
        0.0,
        0.0,
        0.10,
        0.9950,
        0.0,
        0.0,
        0.15,
        0.9887,
        0.0,
        0.0,
        0.20,
        0.9800,
    )
    data += _half1()

    data += b"\x00"
    return bytes(data)


def test_detect_optional_timeline_block() -> None:
    block = struct.pack("<H3f", 3, 0.0, 33.333332, 66.666664)
    size = _detect_optional_timeline_block(block, 0, 3)
    assert size == len(block)


def test_validate_bone_sep_stream_accepts_optional_timeline() -> None:
    blob = _build_layout_e_sample()
    prs_start = 32 * 3 + 2 + 32 * 2 + 14 + 2 + 4 * 3
    ok, end_pos, err = _validate_prs_stream_bone_sep(blob, prs_start, 2, 3, 16)
    assert ok, err
    assert end_pos == len(blob) - 1


def test_read_gis_parses_layout_e_sample(tmp_path) -> None:
    sample = tmp_path / "layout_e_sample.gis"
    sample.write_bytes(_build_layout_e_sample())

    result = read_gis(str(sample))
    assert result is not None
    assert isinstance(result, SubAnimResult)
    assert result.layout == "A"
    assert result.key_count == 3
    assert len(result.tracks) == 2
    assert result.bytes_remaining == 1


def test_read_gis_parses_layout_e_adaptive_keycount(tmp_path) -> None:
    sample = tmp_path / "layout_e_adaptive_kc.gis"
    sample.write_bytes(_build_layout_e_adaptive_kc_sample())

    result = read_gis(str(sample))
    assert result is not None
    assert isinstance(result, SubAnimResult)
    assert result.key_count == 2
    assert len(result.tracks) == 2

    # Bone 1 deve usar key_count local (5), não o global (2).
    assert len(result.tracks[1].rot_keys) == 5
    assert result.bytes_remaining == 1
