# -*- coding: utf-8 -*-
"""
NeoX .mesh Parser — Leitura sequencial linear baseada no converter.py.
Retorna MeshDTO para consumo por qualquer escritor (FBX, OBJ, viewport).
"""
import struct
import numpy as np
from core.dto import MeshDTO, SkeletonDTO, BoneData, SubMeshInfo
from core.exceptions import FormatError, EOFError, ValidationError

# Limites de sanidade para detectar arquivos corrompidos antes de alocar memória
_MAX_BONE_COUNT    = 10_000
_MAX_VERTEX_COUNT  = 5_000_000
_MAX_FACE_COUNT    = 10_000_000


# =============================================================================
# Helpers de leitura sequencial (file handle stream)
# =============================================================================
def _safe_read(f, n, label="data"):
    """Lê exatamente n bytes. Levanta EOFError se o arquivo estiver truncado."""
    buf = f.read(n)
    if len(buf) < n:
        raise EOFError(
            "Arquivo truncado ao ler '{0}'".format(label),
            context={"expected_bytes": n, "got_bytes": len(buf), "offset": f.tell()}
        )
    return buf

def _read_uint8(f, label="uint8"):
    return struct.unpack('B', _safe_read(f, 1, label))[0]

def _read_uint16(f, label="uint16"):
    return struct.unpack('H', _safe_read(f, 2, label))[0]

def _read_uint32(f, label="uint32"):
    return struct.unpack('I', _safe_read(f, 4, label))[0]

def _read_float(f, label="float32"):
    return struct.unpack('f', _safe_read(f, 4, label))[0]


# =============================================================================
# Parser principal
# =============================================================================
def parse_mesh(path):
    """
    Parseia um arquivo .mesh NeoX e retorna um MeshDTO.
    Leitura 100% sequencial — nunca faz seek para frente.
    Baseado na logica do converter.py (referencia funcional).
    """
    dto = MeshDTO()
    dto.source_path = path

    with open(path, 'rb') as f:
        # =====================================================================
        # HEADER
        # =====================================================================
        magic_raw = _safe_read(f, 8, "magic")
        # Valida os 4 bytes do magic number NeoX .mesh
        if magic_raw[:4] != b'\x34\x80\xc8\xbb':
            raise FormatError(
                "Magic number inválido para arquivo .mesh NeoX",
                context={"path": path, "got": magic_raw[:4].hex()}
            )
        bone_exist = _read_uint32(f, "bone_exist")

        # =====================================================================
        # SKELETON (se existir)
        # =====================================================================
        if bone_exist:
            # Caso especial: bone_exist > 1 (versao com dados extras no header)
            if bone_exist > 1:
                count = _read_uint8(f)
                f.read(2)               # 2 bytes skip
                f.read(count * 4)       # count × 4 bytes skip

            bone_count = _read_uint16(f, "bone_count")
            if bone_count > _MAX_BONE_COUNT:
                raise ValidationError(
                    "bone_count improvável — arquivo possivelmente corrompido",
                    context={"bone_count": bone_count, "max_allowed": _MAX_BONE_COUNT, "path": path}
                )

            # 1. Parent indices (1 byte cada)
            raw_parents = np.frombuffer(f.read(bone_count), dtype='u1')
            parent_nodes = [int(p) if p != 255 else -1 for p in raw_parents]

            # 2. Bone names (32 bytes cada, null-padded)
            bone_names = []
            for _ in range(bone_count):
                raw = f.read(32)
                # Limpeza idêntica ao GIS parser para consistência
                clean_bytes = raw.split(b'\x00', 1)[0]
                try:
                    res = clean_bytes.decode('utf-8', errors='replace').strip()
                    name = "".join(c for c in res if ord(c) >= 32).strip()
                except:
                    name = "unknown_bone"
                bone_names.append(name)

            # 3. Extra info flag
            bone_extra_flag = _read_uint8(f)
            if bone_extra_flag:
                for _ in range(bone_count):
                    f.read(28)          # 28 bytes extras por bone (pular)

            # 4. Bind pose matrices (4×4 float = 64 bytes cada)
            mat_raw = np.frombuffer(f.read(bone_count * 64), dtype='<f4').reshape(bone_count, 4, 4)
            bones = [
                BoneData(index=i, name=bone_names[i], parent_index=parent_nodes[i], bind_matrix=mat_raw[i])
                for i in range(bone_count)
            ]

            # 5. Caso de multiplos roots: criar dummy_root
            has_dummy = False
            root_count = sum(1 for p in parent_nodes if p == -1)
            if root_count > 1:
                has_dummy = True
                num = len(parent_nodes)
                for bone in bones:
                    if bone.parent_index == -1:
                        bone.parent_index = num
                dummy = BoneData(
                    index=num,
                    name='dummy_root',
                    parent_index=-1,
                    bind_matrix=np.identity(4)
                )
                bones.append(dummy)

            # 6. Flag final (deve ser 0)
            _flag = _read_uint8(f, "skeleton_end_flag")
            if _flag != 0:
                raise FormatError(
                    "Flag pós-skeleton inválida",
                    context={"expected": 0, "got": _flag, "offset": f.tell(), "path": path}
                )

            dto.skeleton = SkeletonDTO(bones, has_dummy_root=has_dummy)

        # =====================================================================
        # SUB-MESH METADATA
        # =====================================================================
        _offset = _read_uint32(f)  # uint32 descartado

        submeshes = []
        while True:
            flag = _read_uint16(f)
            if flag == 1:
                break
            # Nao era sentinel — rewind 2 bytes
            f.seek(-2, 1)
            mesh_vc = _read_uint32(f)
            mesh_fc = _read_uint32(f)
            uv_layers = _read_uint8(f)
            color_len = _read_uint8(f)
            submeshes.append(SubMeshInfo(mesh_vc, mesh_fc, uv_layers, color_len))

        dto.submeshes = submeshes

        # =====================================================================
        # GEOMETRY — BUFFERS GLOBAIS
        # =====================================================================
        vertex_count = _read_uint32(f, "vertex_count")
        face_count   = _read_uint32(f, "face_count")
        if vertex_count > _MAX_VERTEX_COUNT:
            raise ValidationError(
                "vertex_count improvável — arquivo possivelmente corrompido",
                context={"vertex_count": vertex_count, "max_allowed": _MAX_VERTEX_COUNT, "path": path}
            )
        if face_count > _MAX_FACE_COUNT:
            raise ValidationError(
                "face_count improvável — arquivo possivelmente corrompido",
                context={"face_count": face_count, "max_allowed": _MAX_FACE_COUNT, "path": path}
            )

        # Buffer 1: Posicoes (3 × float32 por vertice)
        dto.positions = list(map(tuple, np.frombuffer(f.read(vertex_count * 12), dtype='<f4').reshape(-1, 3)))

        # Buffer 2: Normais (3 × float32 por vertice)
        dto.normals = list(map(tuple, np.frombuffer(f.read(vertex_count * 12), dtype='<f4').reshape(-1, 3)))

        # Buffer 3: Tangentes opcionais
        tangent_flag = _read_uint16(f)
        if tangent_flag:
            f.seek(vertex_count * 12, 1)  # pular tangentes

        # Buffer 4: Faces — Triangle List (3 × uint16 por face)
        dto.faces = list(map(tuple, np.frombuffer(f.read(face_count * 6), dtype='<u2').reshape(-1, 3)))

        # Buffer 5: UVs — PER-SUBMESH
        uvs = []
        for sub in submeshes:
            if sub.uv_layers > 0:
                raw = np.frombuffer(f.read(sub.vertex_count * 8), dtype='<f4').reshape(-1, 2)
                uvs.extend(map(tuple, raw))
                f.read(sub.vertex_count * 8 * (sub.uv_layers - 1))
            else:
                uvs.extend([(0.0, 0.0)] * sub.vertex_count)
        dto.uvs = uvs

        # Buffer 6: Vertex Colors — PER-SUBMESH (pular)
        for sub in submeshes:
            f.read(sub.vertex_count * 4 * sub.color_len)

        # Buffer 7: Skin Weights (se tem skeleton)
        if bone_exist:
            # 7a. Bone indices (4 × uint8 por vertice)
            dto.joint_indices = list(map(list, np.frombuffer(f.read(vertex_count * 4), dtype='u1').reshape(-1, 4)))

            # 7b. Bone weights (4 × float32 por vertice)
            dto.joint_weights = list(map(list, np.frombuffer(f.read(vertex_count * 16), dtype='<f4').reshape(-1, 4)))

    return dto
