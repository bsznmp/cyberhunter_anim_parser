# -*- coding: utf-8 -*-
import pytest
import os
import sys
import math

# Garantir que a raiz do projeto esteja no path para importar core
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.read_neox_sub_animation import read_gis, RgisResult, SubAnimResult, validate

# Caminhos fornecidos pelo usuário
BASE_PATH = r"C:\Users\diesel\Documents\_all_projects\Cyber Hunter Projetos\.CyberConv\.outros\female\lingzi"
CHILD_PATH = os.path.join(BASE_PATH, "common_gis")

def get_gis_files():
    files = []
    # common.gis na raiz (Layout D)
    common_path = os.path.join(BASE_PATH, "common.gis")
    if os.path.exists(common_path):
        files.append(common_path)
    # Todos os arquivos em common_gis/ (Layouts A/B/C)
    if os.path.exists(CHILD_PATH):
        files += [os.path.join(CHILD_PATH, f) for f in os.listdir(CHILD_PATH) if f.endswith('.gis')]
    return files

@pytest.mark.parametrize("gis_file", get_gis_files() if get_gis_files() else ["missing_path"])
def test_parse_real_gis(gis_file):
    if gis_file == "missing_path":
        pytest.skip("Arquivos GIS de teste não encontrados.")
        
    print(f"\n[GIS-TEST] Arquivo: {os.path.basename(gis_file)}")
    result = read_gis(gis_file)
    
    assert result is not None
    
    if isinstance(result, RgisResult):
        # Validação do Container RGIS (Layout D)
        print(f"  [LAYOUT D] Container RGIS Detectado")
        print(f"    - Bones no Rig:   {result.bone_count}")
        print(f"    - Clipes no Index: {result.sub_anim_count}")
        assert result.bone_count > 0
        assert result.sub_anim_count > 0
        assert len(result.bone_names) == result.bone_count
        assert len(result.bind_pose) == result.bone_count
        assert result.bytes_verified, "O tamanho lido difere do tamanho real do arquivo (Parse Incompleto)."
        
    elif isinstance(result, SubAnimResult):
        # Validação de Clipes (Layouts A, B, C)
        print(f"  [LAYOUT {result.layout}] Clipe de Animacao")
        print(f"    - Bones Animados: {len(result.tracks)}")
        print(f"    - Frames:         {result.key_count}")
        print(f"    - Codec Rot:      {result.rot_codec}")
        
        if result.key_count > 0:
            print(f"    - Duracao:        {result.duration_ms/1000:.3f}s")
        
        # Validação Matemática de Altíssima Fidelidade (Quaternions)
        is_valid = validate(result)
        assert is_valid, "Erro de normalização de quatérnios detectado! Dados podem estar corrompidos ou codec errado."
        
        # Verificação de bones específicos se for Layout C (Facial)
        if result.layout == "C":
            # Animações faciais costumam ter poucos bones mas muitos frames e half_quat
            assert result.rot_codec == "half_quat"
            print("    [FOTO] Layout C (Half-Quat) Validado com Sucesso.")

    print(f"  [STATUS] Parse: {(result.bytes_read if hasattr(result, 'bytes_read') else result.file_size)/1024:.1f} KB Processados.")
