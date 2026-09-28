Tradução para PT-BR
Formatos de Arquivo Binário
Os arquivos mesh, gis, dds e tga são todos formatos de arquivo binário. Os métodos de extração de dados importantes e filtragem variam para cada formato, sendo compatíveis apenas com versões específicas e métodos fixos. Abaixo estão exemplos de regras.

1. Regras para Mesh
Arquivos mesh atualmente suportam versões do mecanismo Nexo abaixo de 0x50004 (327684). O conteúdo do arquivo é解析ado de forma fixa através de structs. O formato de referência é:

Container: 
    header = Container: 
        file_mark = mesh (total 4)
        version = 327684
        file_version = 327684
        file_version_mask = 0
    patch_version = 0
    mesh_type = skeletal (total 8)
    bone_count = 25
    bones = ListContainer: 
        24
        11
    bone_names = ListContainer: 
        98
    has_bones_bi = True
    bone_bounding_info = <LazyRangeContainer: 25 possible items, 0 cached>
    bone_matrix = <LazyRangeContainer: 25 possible items, 0 cached>
    has_bi = False
    table_offset = 22516
    data_table = Container: 
        block_count = 1
        block_infos = ListContainer: 
            3170
        pair_count = 1
        data_pairs = ListContainer: 
            Container: 
                type = lod (total 3)
                block_idx = 0
        content = ListContainer: 
            Container: 
                sub_mesh_headers = ListContainer: 
                    Container: 
                        v_count = 229
                        tri_count = 314
                        uv_chnl_count = 2
                        has_color = False
                lod_new_v = 1
                v_count = 229
                tri_count = 314
                vb = <LazyRangeContainer: 229 possible items, 0 cached>
                nb = <LazyRangeContainer: 229 possible items, 0 cached>
                has_tangent = 1
                tangent = <LazyRangeContainer: 229 possible items, 0 cached>
                ib = <LazyRangeContainer: 942 possible items, 0 cached>
                tb = ListContainer: 
                    ListContainer: 
                        <LazyRangeContainer: 229 possible items, 0 cached>
                        <LazyRangeContainer: 229 possible items, 0 cached>
                cb = None
                ref_bones = ListContainer: 
                    1507350
                    4294967295
                    1441804
    tail = ListContainer: 

O arquivo é convertido em um objeto root durante a inspeção. Por exemplo, os dados da versão correspondem a root.header.version. As regras atualmente suportadas incluem:

root - objeto raiz completo

root/version - versão do arquivo

root/bone_count - contagem de ossos

root/refbone_count - contagem de ossos de referência (dentro de root.data_table.content.ref_bones)

Atributos personalizados root/{} - para acessar dados específicos do objeto raiz

Exemplo de regra:
Modelo não pode ter mais de 80 ossos

Campo	Valor
rpath	.*\.mesh$
xpath	root/bone_count
condition	["satisfaz expressão", "d < 80"]

2. Regras para GIS
O suporte para arquivos GIS também está relacionado à versão do mecanismo. Atualmente, são suportadas versões com recursos de track expandidos. O conteúdo do arquivo é解析ado de forma fixa através de structs. O formato de referência é:

Container: 
    header = Container: 
        file_mark = anim (total 4)
        version = 50724865
        file_version = 393217
        file_version_mask = 3
    anim_count = 5
    bone_count = 3
    bone_names = ListContainer: 
        b'bone001'
        b'bone002'
        b'root'
    bone_trans = ListContainer: 
        Container: 
            pos = ListContainer: 
                0.0
                4.044138431549072
                -3.159993298140762e-07
            rot = ListContainer: 
                1.4527657299368002e-08
                -1.4527657299368002e-08
                0.7071068286895752
                0.7071068286895752
            scale = ListContainer: 
                1.0
                1.0
                1.0
        Container: 
            pos = ListContainer: 
                0.0
                1.0272369384765625
                -0.025091886520385742
            rot = ListContainer: 
                0.5000001192092896
                0.4999999403953552
                -0.49999988079071045
                -0.5000000596046448
            scale = ListContainer: 
                1.0
                1.0
                1.0
        Container: 
            pos = ListContainer: 
                0.0
                0.0
                0.0
            rot = ListContainer: 
                0.0
                0.0
                0.0
                1.0
            scale = ListContainer: 
                1.0
                1.0
                1.0
    seperate_storage = 0
    base_size = None
    anim = ListContainer: 
        Container: 
            name = obtain (total 6)
            anim_root_name = root (total 4)
            bone_count = 3
            bone_names = ListContainer: 
                b'bone001'
                b'bone002'
                b'root'
            sample_fps = 30
            loop = False
            has_scaled = True
            prs_flags = 7
            accum_flags = 0
            pack_prs_flags = 6
            bone_separate_flags = 0
            keys_data = Container: 
                key_count = 16
                key_times = ListContainer: 
                    0.0
                    33.33333206176758
                    66.66666412353516
                    100.0
                    133.3333282470703
                    166.6666717529297
                    200.0
                    233.3333282470703
                    266.6666564941406
                    300.0
                    333.3333435058594
                    366.6666564941406
                    400.0
                    433.3333435058594
                    466.6666564941406
                    500.0
                key_data = ListContainer: 
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = True
                        euler_flags = False
                        position_key_count = 16
                        positions = <LazyRangeContainer: 16 possible items, 0 cached>
                        rot_key_count = 16
                        rot = <LazyRangeContainer: 16 possible items, 0 cached>
                        scale_key_count = 16
                        scales = <LazyRangeContainer: 16 possible items, 0 cached>
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = True
                        euler_flags = False
                        position_key_count = 16
                        positions = <LazyRangeContainer: 16 possible items, 0 cached>
                        rot_key_count = 16
                        rot = <LazyRangeContainer: 16 possible items, 0 cached>
                        scale_key_count = 16
                        scales = <LazyRangeContainer: 16 possible items, 0 cached>
                    Container: 
                        has_pos_keys = False
                        has_rot_keys = False
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 1
                        positions = <LazyRangeContainer: 1 possible items, 0 cached>
                        rot_key_count = 1
                        rot = <LazyRangeContainer: 1 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
            pivot = Container: 
                has_pivot_track = False
                track_data = None
        Container: 
            name = idle (total 4)
            anim_root_name = root (total 4)
            bone_count = 3
            bone_names = ListContainer: 
                b'bone001'
                b'bone002'
                b'root'
            sample_fps = 30
            loop = True
            has_scaled = True
            prs_flags = 7
            accum_flags = 0
            pack_prs_flags = 6
            bone_separate_flags = 0
            keys_data = Container: 
                key_count = 101
                key_times = ListContainer: 
                    0.0
                    33.33333206176758
                    66.66666412353516
                key_data = ListContainer: 
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 101
                        positions = <LazyRangeContainer: 101 possible items, 0 cached>
                        rot_key_count = 101
                        rot = <LazyRangeContainer: 101 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 101
                        positions = <LazyRangeContainer: 101 possible items, 0 cached>
                        rot_key_count = 101
                        rot = <LazyRangeContainer: 101 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = False
                        has_rot_keys = False
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 1
                        positions = <LazyRangeContainer: 1 possible items, 0 cached>
                        rot_key_count = 1
                        rot = <LazyRangeContainer: 1 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
            pivot = Container: 
                has_pivot_track = False
                track_data = None
        Container: 
            name = born (total 4)
            anim_root_name = root (total 4)
            bone_count = 3
            bone_names = ListContainer: 
                b'bone001'
                b'bone002'
                b'root'
            sample_fps = 30
            loop = False
            has_scaled = True
            prs_flags = 7
            accum_flags = 0
            pack_prs_flags = 6
            bone_separate_flags = 0
            keys_data = Container: 
                key_count = 25
                key_times = ListContainer: 
                    0.0
                    33.54166793823242
                    66.875
                key_data = ListContainer: 
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 25
                        positions = <LazyRangeContainer: 25 possible items, 0 cached>
                        rot_key_count = 25
                        rot = <LazyRangeContainer: 25 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 25
                        positions = <LazyRangeContainer: 25 possible items, 0 cached>
                        rot_key_count = 25
                        rot = <LazyRangeContainer: 25 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = False
                        has_rot_keys = False
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 1
                        positions = <LazyRangeContainer: 1 possible items, 0 cached>
                        rot_key_count = 1
                        rot = <LazyRangeContainer: 1 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
            pivot = Container: 
                has_pivot_track = False
                track_data = None
        Container: 
            name = dead (total 4)
            anim_root_name = root (total 4)
            bone_count = 3
            bone_names = ListContainer: 
                b'bone001'
                b'bone002'
                b'root'
            sample_fps = 30
            loop = False
            has_scaled = True
            prs_flags = 7
            accum_flags = 0
            pack_prs_flags = 6
            bone_separate_flags = 0
            keys_data = Container: 
                key_count = 29
                key_times = ListContainer: 
                    0.0
                    33.33333206176758
                    66.66666412353516
                key_data = ListContainer: 
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 29
                        positions = <LazyRangeContainer: 29 possible items, 0 cached>
                        rot_key_count = 29
                        rot = <LazyRangeContainer: 29 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = True
                        has_rot_keys = True
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 29
                        positions = <LazyRangeContainer: 29 possible items, 0 cached>
                        rot_key_count = 29
                        rot = <LazyRangeContainer: 29 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
                    Container: 
                        has_pos_keys = False
                        has_rot_keys = False
                        has_scale_keys = False
                        euler_flags = False
                        position_key_count = 1
                        positions = <LazyRangeContainer: 1 possible items, 0 cached>
                        rot_key_count = 1
                        rot = <LazyRangeContainer: 1 possible items, 0 cached>
                        scale_key_count = 1
                        scales = <LazyRangeContainer: 1 possible items, 0 cached>
            pivot = Container: 
                has_pivot_track = False
                track_data = None
    tail =  (total 0)

As informações espaciais de cada osso nas animações são armazenadas em arquivos GIS. Como a quantidade de animações varia de modelo para modelo (de alguns poucos a milhares), para modelos com poucas animações existe apenas um arquivo GIS, enquanto modelos com muitas animações utilizam um arquivo GIS principal e vários arquivos GIS secundários. Caso contrário, concentrar todas as animações em um único arquivo GIS resultaria em arquivos de dezenas de megabytes, com tempos de carregamento longos e manutenção difícil.

O arquivo GIS principal armazena apenas os nomes e durações de todas as animações do modelo, enquanto os arquivos GIS secundários armazenam as informações espaciais de cada osso em relação ao osso pai e os quadros-chave das animações específicas.

O arquivo é convertido em um objeto root durante a inspeção. Em comparação com o arquivo GIS principal, o arquivo GIS secundário (conforme imagem) tem como principal diferença o atributo anim.

Container:
    name = shd_start_fl (total 12)
    root_name = biped root (total 10)
    bone_count = 100
    bone_name_id = ListContainer:
        1701865826
        100
        0
        0
        0
        0
        0
        .
        .
    sample_fps = 0
    loop = True
    has_scaled = True
    prs_flags = 25968
    accum_flags = 544350308
    pack_prs_flags = 102
    bone_separate_flags = 105
    length = 4.5438147884045724e+30
    keys_data_offset = 49
    anim = Container:
        name = \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00biped r finger11 (total 30)
        anim_root_name = \x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00biped r finger12 (total 30)
        bone_count = 0
        bone_names = ListContainer:
        sample_fps = 0
        loop = False
        has_scaled = False
        prs_flags = 0
        accum_flags = 0
        pack_prs_flags = 98
        bone_separate_flags = 105

As regras atualmente suportadas incluem:

root - objeto raiz completo

root/bone_count - contagem de ossos

root/samplefps - quadros por segundo (FPS) da animação

Atributos personalizados root/{} - para acessar dados específicos do objeto raiz

Dados sob root.anim - como keys_data.key_count (quantidade de quadros-chave)

Exemplo de regra:
Número de quadros da animação não pode exceder 5 (arquivo GIS pai)

Campo	Valor
rpath	.*\.gis$
xpath	root/anim
condition	['satisfaz expressão', 'd < 5']
filter	artfunc_checkgis_keycount

python
def checkgis_keycount(**pdict): 
    data = pdict.get('data', []) 
    try: 
        result = data[0][0].keys_data.key_count 
    except: 
        return [len(data)] 
    return [result]

3. Regras para DDS (aplicável a arquivos TGA)
Arquivos DDS são atualmente解析ados por bibliotecas de terceiros. O suporte é limitado às seguintes especificações:

Pixel format: apenas formatos FOURCC ou RGB

Formatos RGB suportados: A8R8G8B8, A1R5G5B5, A4R4G4B4, R8G8B8, R5G6B5

Formatos FOURCC suportados: DXT1, DXT2, DXT3, DXT4, DXT5

Os principais atributos解析ados são:

Campo	Descrição
root.size	Altura e largura do arquivo (ex: 1024, 1024)
root.header_size	Tamanho do header (deve ser 124 bytes; usado para validar conformidade do formato)
root.mode	Formato da imagem (L, P, RGB, RGBA, CMYK, YCbCr, I, F, etc.)
root.mipmaps	Número de níveis mipmap
root.pfsize	Tamanho do pixel format (deve ser 32 bytes)
root.pfflags	Flags do domínio de valores do pixel format
root.fourcc	Formato de compressão (série DXTn). Requer que a flag DDPF_FOURCC em pfflags esteja ativa
root.bitcount	Número de bits RGB (requer canal A presente)
root.pixel_format	Formato de compressão (mais detalhado que fourcc)
Exemplo de regra:
Dimensões do arquivo não podem exceder 1024x1024

Campo	Valor
rpath	.*\.dds$
xpath	root/size
condition	["satisfaz expressão", "int(d[0]) <= 1024 and int(d[1]) <= 1024"]