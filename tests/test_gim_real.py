# -*- coding: utf-8 -*-
import pytest
import os
import sys

# Garantir que a raiz do projeto esteja no path para importar core
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core.gim_parser import parse_gim

TEST_PATH = r"C:\Users\diesel\Documents\_all_projects\Cyber Hunter Projetos\.CyberConv\.outros\female\lingzi"

def get_gim_files():
    if not os.path.exists(TEST_PATH):
        return []
    return [os.path.join(TEST_PATH, f) for f in os.listdir(TEST_PATH) if f.endswith('.gim')]

@pytest.mark.parametrize("gim_file", get_gim_files() if get_gim_files() else ["missing_path"])
def test_parse_real_gim(gim_file):
    if gim_file == "missing_path":
        pytest.skip("Caminho de teste não encontrado localmente.")
        
    print(f"\n[TEST] Parsing: {os.path.basename(gim_file)}")
    dto = parse_gim(gim_file)
    
    # Validações estruturais do DTO
    assert dto is not None
    assert os.path.isabs(dto.source_path)
    assert isinstance(dto.mesh_paths, list)
    assert isinstance(dto.gis_paths, list)
    assert isinstance(dto.mtg_path, str)
    
    # Logs para auditoria manual (vistos no output do pytest -s)
    if dto.mesh_paths:
        print(f"  [MESHES] ({len(dto.mesh_paths)})")
        for m in dto.mesh_paths:
            print(f"    - {m}")
            
    if dto.gis_paths:
        print(f"  [GIS] ({len(dto.gis_paths)})")
        for g in dto.gis_paths:
            print(f"    - {g}")
            
    if dto.mtg_path:
        print(f"  [MTG] {dto.mtg_path}")

    if dto.bounding_center:
        print(f"  [BOUNDING] R={dto.bounding_radius:.4f} Center={dto.bounding_center}")

    # Pelo menos um recurso deve ser encontrado em um .gim válido de personagem
    if os.path.basename(gim_file) != "base.gim": # base.gim as vezes é um manifesto vazio ou de cena
        total_assets = len(dto.mesh_paths) + len(dto.gis_paths) + (1 if dto.mtg_path else 0)
        assert total_assets > 0, f"O arquivo {gim_file} não parece conter assets NeoX."
