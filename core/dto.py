# -*- coding: utf-8 -*-
"""
DTOs (Data Transfer Objects) para o pipeline NeoX.
Contratos de dados imutáveis entre parser, writer e futuros consumidores.
"""
import numpy as np


# =============================================================================
# RGIS DTOs  (common.gis / dongzuoku.gis — manifesto do rig)
# =============================================================================

class AnimIndexEntry(object):
    """
    Uma entrada no índice de animações do RGIS.
    Metadados de um clipe antes de carregar o child .gis correspondente.
    """
    __slots__ = ['name', 'fps', 'bone_count', 'key_count', 'pack_prs_flags', 'loop']

    def __init__(self, name, fps=30, bone_count=0, key_count=0, pack_prs_flags=0, loop=False):
        self.name           = name           # str: ex "cyberpunk_f", "idle", "spawn"
        self.fps            = fps            # int: sample rate original
        self.bone_count     = bone_count     # int: bc — quantos bones este clipe anima
        self.key_count      = key_count      # int: número de keyframes
        self.pack_prs_flags = pack_prs_flags # int: codec (4=float32, 6=half_quat?)
        self.loop           = loop           # bool

    def __repr__(self):
        return "AnimIndexEntry('{0}', fps={1}, bc={2}, kc={3})".format(
            self.name, self.fps, self.bone_count, self.key_count)


class RGisDTO(object):
    """
    DTO do arquivo RGIS (common.gis / dongzuoku.gis).

    Carregado UMA VEZ por sessão. Fornece:
      - bone_names[N]   : tabela canônica índice → nome
      - bone_trans[N]   : bind pose local (T-pose) de cada bone
      - anim_index[M]   : metadados de todos os clipes (sem PRS)

    O campo separate_storage indica se os PRS streams estão embutidos (=0)
    ou em arquivos child .gis separados (!=0).
    """
    __slots__ = [
        'source_path',
        'bone_count',
        'bone_names',
        'bone_trans',
        'anim_count',
        'anim_index',
        'separate_storage',
    ]

    def __init__(self):
        self.source_path     = ""   # str: caminho absoluto do arquivo RGIS
        self.bone_count      = 0    # int: número de bones do rig completo
        self.bone_names      = []   # list[str]: nomes canônicos (bone_count)
        self.bone_trans      = []   # list[BoneTransform]: bind pose local (bone_count)
        self.anim_count      = 0    # int: total de clipes no índice
        self.anim_index      = []   # list[AnimIndexEntry]: índice de clipes
        self.separate_storage = 0   # int: 0=inline PRS, !=0=child files

    @property
    def anim_names(self):
        """Lista de nomes de clipes para popular dropdowns/listas na GUI."""
        return [e.name for e in self.anim_index]

    def find_clip(self, name):
        """Retorna AnimIndexEntry pelo nome, ou None."""
        for e in self.anim_index:
            if e.name == name:
                return e
        return None

    def __repr__(self):
        fname = self.source_path.replace('\\', '/').split('/')[-1] if self.source_path else ''
        return "RGisDTO('{0}', {1} bones, {2} clips)".format(
            fname, self.bone_count, self.anim_count)


# =============================================================================
# GIS / Animation DTOs
# Estrutura completa preparada para o gis_parser.py (Phase 2).
# Na Phase 1 apenas GisDTO.source_path é populado pela GUI.
# =============================================================================

class BoneTransform(object):
    """Pose base de um bone conforme lido do .gis (pos + rot quaternion + scale)."""
    __slots__ = ['pos', 'rot', 'scale']

    def __init__(self, pos=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0, 1.0), scale=(1.0, 1.0, 1.0)):
        self.pos   = pos    # (x, y, z)
        self.rot   = rot    # (x, y, z, w) quaternion
        self.scale = scale  # (x, y, z)


class BoneTrackDTO(object):
    """Trilha de keyframes PRS de um bone individual dentro de um AnimClipDTO."""
    __slots__ = ['bone_name', 'times', 'positions', 'rotations', 'scales']

    def __init__(self, bone_name):
        self.bone_name  = bone_name  # str
        self.times      = []         # list[float]: tempos em segundos
        self.positions  = []         # list[(x,y,z)] — vazio se has_pos_keys=False
        self.rotations  = []         # list[(x,y,z,w)] — vazio se has_rot_keys=False
        self.scales     = []         # list[(x,y,z)] — vazio se has_scale_keys=False


class AnimClipDTO(object):
    """Um clipe de animação do .gis. Phase 2: preenchido pelo gis_parser.py."""
    __slots__ = ['name', 'fps', 'loop', 'bone_tracks', 'variant',
                 'rgis_bone_names', 'rgis_bone_trans']

    def __init__(self, name, fps=30, loop=False, variant='B'):
        self.name            = name   # str: ex "idle", "run", "attack"
        self.fps             = fps    # int: sample rate original do .gis
        self.loop            = loop   # bool
        self.bone_tracks     = []     # list[BoneTrackDTO]
        self.variant         = variant # str: 'A' ou 'B'
        self.rgis_bone_names = []     # list[str]: tabela canônica do RGIS
        self.rgis_bone_trans = []     # list[BoneTransform]: bind pose do RGIS

    @property
    def frame_count(self):
        if not self.bone_tracks or not self.bone_tracks[0].times:
            return 0
        return len(self.bone_tracks[0].times)

    def __repr__(self):
        return "AnimClipDTO('{0}', {1}fps, {2} frames, {3} bones)".format(
            self.name, self.fps, self.frame_count, len(self.bone_tracks))


class GisDTO(object):
    """
    DTO do arquivo .gis NeoX.

    Phase 1: apenas source_path é populado — o gis_dto é passado ao
             blender_merge_fbx.py como referência para quando Phase 2 chegar.
    Phase 2: gis_parser.py preenche bone_names, bone_transforms e anim_clips.

    bone_names lista os nomes canônicos dos bones do personagem, na mesma ordem
    em que aparecem no .gis. Útil para validar/normalizar o skeleton primário
    extraído dos .mesh files.
    """
    __slots__ = ['source_path', 'bone_names', 'bone_transforms', 'anim_clips']

    def __init__(self):
        self.source_path     = ""   # str: caminho absoluto do arquivo .gis
        self.bone_names      = []   # list[str]: nomes canônicos (Phase 2)
        self.bone_transforms = []   # list[BoneTransform]: T-pose canônica (Phase 2)
        self.anim_clips      = []   # list[AnimClipDTO]: vazio na Phase 1

    @property
    def has_animations(self):
        return len(self.anim_clips) > 0

    @property
    def bone_count(self):
        return len(self.bone_names)

    def __repr__(self):
        fname = self.source_path.replace('\\', '/').split('/')[-1] if self.source_path else ''
        return "GisDTO('{0}', {1} bones, {2} clips)".format(
            fname, self.bone_count, len(self.anim_clips))


class GimDTO(object):
    """
    DTO do arquivo .gim NeoX — manifesto de montagem de um asset.

    O .gim não contém geometria: descreve quais arquivos carregar (.mesh, .gis,
    .mtg) e fornece dados de bounding box para o asset completo.

    Produzido por core/gim_parser.py:parse_gim(path).
    Consumido por qualquer assembler que precise resolver o asset a partir de um
    único ponto de entrada (ex.: MergeDTO builder).

    Todos os paths são game-relative com separador backslash, exatamente como
    armazenados no arquivo binário.
    """
    __slots__ = [
        'source_path',
        'mesh_paths',
        'gis_paths',
        'sfx_paths',
        'audio_paths',
        'script_paths',
        'config_paths',
        'other_paths',
        'mtg_path',
        'bounding_center',
        'bounding_half',
        'bounding_radius',
    ]

    def __init__(self):
        self.source_path     = ""    # str: caminho absoluto do arquivo .gim
        self.mesh_paths      = []    # list[str]: paths de .mesh referenciados
        self.gis_paths       = []    # list[str]: paths de .gis referenciados
        self.sfx_paths       = []    # list[str]: paths de .sfx referenciados
        self.audio_paths     = []    # list[str]: paths de .ags, .wav, .mp3
        self.script_paths    = []    # list[str]: paths de .act, .lua
        self.config_paths    = []    # list[str]: paths de .xml, .json, .csv
        self.other_paths     = []    # list[str]: extensões variadas
        self.mtg_path        = ""    # str: primeiro .mtg referenciado
        self.bounding_center = None  # tuple(x, y, z) | None
        self.bounding_half   = None  # tuple(x, y, z) | None — half-extents
        self.bounding_radius = None  # float | None — bounding sphere radius

    @property
    def gis_path(self):
        """Atalho para o primeiro .gis (caso mais comum: um único skeleton)."""
        return self.gis_paths[0] if self.gis_paths else ""

    @property
    def has_bounding(self):
        return self.bounding_center is not None

    def __repr__(self):
        fname = self.source_path.replace('\\', '/').split('/')[-1]
        return "GimDTO('{0}', {1} meshes, {2} gis)".format(
            fname, len(self.mesh_paths), len(self.gis_paths))


class MtgDTO(object):
    """
    DTO do arquivo .mtg NeoX — material binário (BXML).
    
    Identifica o shader/técnica, texturas referenciadas e propriedades
    de parâmetros do shader.
    """
    __slots__ = [
        'source_path',
        'shaders',
        'textures',
        'properties',
    ]

    def __init__(self, source_path=""):
        self.source_path = source_path
        self.shaders    = []  # list[str]: ex ['standard.fx', 'standard.mesh_shader']
        self.textures   = []  # list[str]: ex ['diffuse.tga', 'normal.dds']
        self.properties = []  # list[str]: ex ['diffuse_color', 'intensity']

    def __repr__(self):
        return "MtgDTO('{0}', {1} textures, {2} props)".format(
            os.path.basename(self.source_path), len(self.textures), len(self.properties))


class MergeDTO(object):
    """
    Agrega múltiplos MeshDTO para exportação em FBX único.
    Análogo ao ModelConverter(rootName, List<GameObject>, ...) do AssetStudio:
      — cria um frame raiz sintético
      — todos os meshes viram filhos desse raiz
      — gis_dto carrega animações (Phase 2)

    primary_skeleton: skeleton com mais bones entre os mesh_dtos.
    Na Phase 2, gis_dto.bone_names pode ser usado para validar/reordenar.
    """
    __slots__ = ['root_name', 'mesh_dtos', 'gis_dto']

    def __init__(self, root_name, mesh_dtos, gis_dto=None):
        self.root_name  = root_name   # str: nome do nó raiz no FBX
        self.mesh_dtos  = mesh_dtos   # list[MeshDTO]
        self.gis_dto    = gis_dto     # GisDTO | None

    @property
    def has_animations(self):
        return self.gis_dto is not None and self.gis_dto.has_animations

    @property
    def primary_skeleton(self):
        """Skeleton com mais bones — usado como Armature canônico no Blender."""
        best = None
        for dto in self.mesh_dtos:
            if dto.has_skeleton:
                if best is None or dto.skeleton.bone_count > best.bone_count:
                    best = dto.skeleton
        return best

    @property
    def mesh_count(self):
        return len(self.mesh_dtos)

    def __repr__(self):
        skel = "{0} bones".format(self.primary_skeleton.bone_count) \
               if self.primary_skeleton else "no skeleton"
        return "MergeDTO('{0}', {1} meshes, {2}, gis={3})".format(
            self.root_name, self.mesh_count, skel, self.gis_dto is not None)


class SubMeshInfo(object):
    """Metadados de uma sub-mesh dentro do .mesh."""
    __slots__ = ['vertex_count', 'face_count', 'uv_layers', 'color_len']

    def __init__(self, vertex_count, face_count, uv_layers, color_len):
        self.vertex_count = vertex_count
        self.face_count = face_count
        self.uv_layers = uv_layers
        self.color_len = color_len

    def __repr__(self):
        return "SubMeshInfo(vc={0}, fc={1}, uv={2}, col={3})".format(
            self.vertex_count, self.face_count, self.uv_layers, self.color_len)


class BoneData(object):
    """Dados de um osso individual."""
    __slots__ = ['index', 'name', 'parent_index', 'bind_matrix']

    def __init__(self, index, name, parent_index, bind_matrix):
        self.index = index              # int: posicao no array
        self.name = name                # str: nome limpo (sem null bytes)
        self.parent_index = parent_index  # int: -1 = root
        self.bind_matrix = bind_matrix  # np.ndarray(4,4): world space bind pose


class SkeletonDTO(object):
    """Hierarquia completa de ossos. Consumido por FBX writer e GIS parser."""
    __slots__ = ['bones', 'has_dummy_root']

    def __init__(self, bones, has_dummy_root=False):
        self.bones = bones              # list[BoneData]
        self.has_dummy_root = has_dummy_root  # bool: True se um root virtual foi criado

    @property
    def bone_count(self):
        return len(self.bones)

    @property
    def bone_names(self):
        """Lista de nomes na ordem original. Necessario para o .gis."""
        return [b.name for b in self.bones]

    @property
    def bone_parents(self):
        """Lista de parent indices na ordem original. Necessario para o .gis."""
        return [b.parent_index for b in self.bones]

    def get_bone_by_name(self, name):
        """Busca um osso pelo nome. Retorna None se nao encontrado."""
        for b in self.bones:
            if b.name == name:
                return b
        return None


class MeshDTO(object):
    """
    DTO principal do pipeline. Dados CRUS do arquivo .mesh, sem transformacao de eixos.
    Cada consumidor (FBX, viewport, assembler) aplica suas proprias transformacoes.
    """
    __slots__ = [
        'source_path',
        'skeleton',
        'submeshes',
        'positions',
        'normals',
        'faces',
        'uvs',
        'joint_indices',
        'joint_weights',
    ]

    def __init__(self):
        self.source_path = ""               # str: caminho do arquivo original
        self.skeleton = None                # SkeletonDTO ou None
        self.submeshes = []                 # list[SubMeshInfo]
        self.positions = []                 # list[tuple(x,y,z)] float32 crus
        self.normals = []                   # list[tuple(x,y,z)] float32 crus
        self.faces = []                     # list[tuple(v1,v2,v3)] Triangle List
        self.uvs = []                       # list[tuple(u,v)] float32 crus
        self.joint_indices = []             # list[list[int]] 4 bones por vertice
        self.joint_weights = []             # list[list[float]] 4 pesos por vertice

    @property
    def has_skeleton(self):
        return self.skeleton is not None and self.skeleton.bone_count > 0

    @property
    def vertex_count(self):
        return len(self.positions)

    @property
    def face_count(self):
        return len(self.faces)

    def __repr__(self):
        skel = "{0} bones".format(self.skeleton.bone_count) if self.has_skeleton else "no skeleton"
        return "MeshDTO({0}, {1} verts, {2} faces, {3} submeshes)".format(
            skel, self.vertex_count, self.face_count, len(self.submeshes))
