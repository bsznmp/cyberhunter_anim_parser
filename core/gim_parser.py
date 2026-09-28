# -*- coding: utf-8 -*-
"""
NeoX .gim parser — componente de pipeline. Retorna GimDTO.

O .gim é o manifesto de montagem de um asset NeoX: não contém geometria,
apenas referências a .mesh, .gis, .sfx, .mtg e metadados de bounding box.

Formato binário documentado em docs/gim_format_definitivo.md.
"""
import re
import struct
import os
from core.dto import GimDTO

MAGIC = b'\xc1\x59\x41\x0d'

# Extensões mapeadas para bucket no GimDTO
_EXT_BUCKET = {
    '.mesh': 'mesh', '.gis': 'gis', '.mtg': 'mtg', '.sfx': 'sfx',
    '.ags': 'audio', '.wav': 'audio', '.mp3': 'audio',
    '.act': 'script', '.lua': 'script',
    '.xml': 'config', '.json': 'config', '.csv': 'config',
    '.lgt': 'other', '.cam': 'other'
}

# "(cx,cy,cz),(hx,hy,hz),r" — formato da string BoundingInfo
_BOUNDING_RE = re.compile(r'\(([^)]+)\),\(([^)]+)\),([\d.]+)')


# ---------------------------------------------------------------------------
# Helpers de leitura
# ---------------------------------------------------------------------------

def _read_strings(data, offset, count):
    """Lê `count` strings null-terminated a partir de `offset`."""
    strings = []
    for _ in range(count):
        end = data.index(b'\x00', offset)
        strings.append(data[offset:end].decode('latin-1'))
        offset = end + 1
    return strings, offset


def _read_header(data):
    """Lê o cabeçalho do .gim de forma sequencial e retorna (table2, payload_offset).

    Layout sequencial:
        0x00  4 B   MAGIC
        0x04  4 B   file_size (uint32 LE)
        0x08  4 B   reservado — sempre 0
        0x0C  1 B   n1 (uint8) — número de strings em Table1
              var   Table1: n1 strings null-terminated (tipos de objeto)
              1 B   n2 (uint8) — número de strings em Table2
              var   Table2: n2 strings null-terminated (nomes de atributo)
              var   Payload (inicia aqui)

    Nota: arquivos com n1 muito grande (ex.: base.gim, n1=644) armazenam n1
    como uint16 LE em 0x0C–0x0D; T1 começa em 0x0E. Detectado se 0x0D é
    não-printável e não-nulo.
    """
    # Detectar se n1 é uint8 (padrão) ou uint16 (arquivos grandes)
    if data[0x0d] not in (0x00,) and data[0x0d] < 0x20:
        n1 = struct.unpack_from('<H', data, 0x0c)[0]
        _, off = _read_strings(data, 0x0e, n1)
    else:
        n1 = data[0x0c]
        _, off = _read_strings(data, 0x0d, n1)

    n2 = data[off]
    off += 1
    table2, off = _read_strings(data, off, n2)
    return table2, off


def _topology_size(payload):
    """Retorna o tamanho em bytes da seção de topologia no payload.

    Formato sequencial (Count-Then-Data + terminador):
        [uint8 count] [count × 2 bytes de pares] [uint8 terminador]
        tamanho = 1 + count*2 + 1

    Os 8 bytes iniciais do payload são fixos:
        [uint32 u32a] [uint32 = 0]
    A topologia começa no byte 8.
    """
    count = payload[8]
    return 1 + count * 2 + 1


# ---------------------------------------------------------------------------
# Extração de dados
# ---------------------------------------------------------------------------

def _scan_paths(payload):
    """Varredura do payload em busca de paths com extensão conhecida.

    Leitura sequencial de strings ASCII printáveis com extensão de arquivo
    conhecida. Strings são deduplicadas mantendo ordem de aparição.
    Robusto para arquivos com tipos de valor não documentados (0x0b, 0x0e).
    """
    buckets = {
        'mesh': [], 'gis': [], 'mtg': [], 'sfx': [],
        'audio': [], 'script': [], 'config': [], 'other': []
    }
    seen = set()
    for m in re.finditer(rb'[\x20-\x7e]{6,}', payload):
        s = m.group(0).decode('latin-1')
        ext = os.path.splitext(s)[1].lower()
        if not ext: continue
        
        bucket = _EXT_BUCKET.get(ext)
        if bucket and s not in seen:
            seen.add(s)
            buckets[bucket].append(s)
        elif s not in seen and len(ext) > 1:
            # Fallback: capturar qualquer coisa com extensão como 'other'
            seen.add(s)
            buckets['other'].append(s)
    return buckets


def _parse_bounding(payload, data_start, table2):
    """Extrai BoundingInfo do stream de atributos de forma sequencial.

    BoundingInfo é sempre uma string no formato "(cx,cy,cz),(hx,hy,hz),r".
    Localizada pelo índice T2 de 'BoundingInfo' seguido do tipo string (0x01).
    Retorna (center_tuple, half_tuple, radius_float) ou (None, None, None).
    """
    if 'BoundingInfo' not in table2:
        return None, None, None

    bi_idx = table2.index('BoundingInfo')
    limit = len(payload) - 2
    i = data_start

    while i < limit:
        if payload[i] == bi_idx and payload[i + 1] == 0x01:
            try:
                end = payload.index(b'\x00', i + 2)
                s = payload[i + 2:end].decode('latin-1')
                match = _BOUNDING_RE.match(s)
                if match:
                    center = tuple(float(x) for x in match.group(1).split(','))
                    half   = tuple(float(x) for x in match.group(2).split(','))
                    radius = float(match.group(3))
                    return center, half, radius
            except (ValueError, IndexError):
                pass
        i += 1

    return None, None, None


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def parse_gim(path):
    """Parse um arquivo .gim NeoX e retorna um GimDTO.

    Leitura 100% sequencial — sem offsets hardcoded, sem scan heurístico.

    Parameters
    ----------
    path : str
        Caminho absoluto ou relativo para o arquivo .gim.

    Returns
    -------
    GimDTO
        DTO populado com mesh_paths, gis_paths, mtg_path e bounding box.

    Raises
    ------
    ValueError
        Se o arquivo não tiver o magic NeoX correto.
    OSError
        Se o arquivo não puder ser lido.
    """
    with open(path, 'rb') as f:
        data = f.read()

    if data[:4] != MAGIC:
        raise ValueError(
            'Nao e um arquivo .gim valido: magic incorreto {:s}'.format(data[:4].hex()))

    dto = GimDTO()
    dto.source_path = os.path.abspath(path)

    # Leitura sequencial do cabeçalho: n1 + T1 + n2 + T2 + payload
    table2, payload_off = _read_header(data)
    payload = data[payload_off:]

    # Topologia: [8 bytes fixos][uint8 count][count*2 bytes pares][uint8 term]
    # data_start = posição do stream de atributos no payload
    topo_sz    = _topology_size(payload)
    data_start = 8 + topo_sz

    # Paths: scan sequencial de strings ASCII com extensão conhecida
    # Começa em data_start — paths só existem no stream de atributos
    paths           = _scan_paths(payload[data_start:])
    dto.mesh_paths   = paths['mesh']
    dto.gis_paths    = paths['gis']
    dto.sfx_paths    = paths['sfx']
    dto.audio_paths  = paths['audio']
    dto.script_paths = paths['script']
    dto.config_paths = paths['config']
    dto.other_paths  = paths['other']
    dto.mtg_path     = paths['mtg'][0] if paths['mtg'] else ''

    # Bounding box do asset completo — lida do stream a partir de data_start
    dto.bounding_center, dto.bounding_half, dto.bounding_radius = (
        _parse_bounding(payload, data_start, table2)
    )

    return dto
