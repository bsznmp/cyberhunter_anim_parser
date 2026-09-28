# -*- coding: utf-8 -*-
"""
NeoX .mesh → FBX Pipeline
Usa Blender em modo headless para gerar FBX nativo e confiavel.

Uso:
  python main.py <caminho.mesh> [caminho.mesh ...]
  python main.py --blender-path "C:/Program Files/Blender/blender.exe" <caminho.mesh>
"""
import sys
import os
import subprocess
import shutil
from core.parser import parse_mesh


def find_blender():
    """Tenta localizar o executavel do Blender automaticamente."""
    # 1. Verificar se esta no PATH
    blender = shutil.which("blender")
    if blender:
        return blender

    # 2. Caminhos comuns no Windows
    common_paths = [
        r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p

    return None


def main():
    args = sys.argv[1:]

    # Flag --blender-path
    blender_path = None
    if "--blender-path" in args:
        idx = args.index("--blender-path")
        blender_path = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if not args:
        print("Uso: python main.py [--blender-path <path>] <caminho.mesh> [caminho.mesh ...]")
        sys.exit(1)

    # Localizar Blender
    if not blender_path:
        blender_path = find_blender()
    if not blender_path:
        print("[ERRO] Blender nao encontrado. Instale ou use --blender-path")
        sys.exit(1)

    print("Blender: {0}".format(blender_path))

    # Caminho do script exporter
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exporter_script = os.path.join(script_dir, "export", "blender_fbx.py")

    for mesh_path in args:
        if not os.path.exists(mesh_path):
            print("[ERRO] Arquivo nao encontrado: {0}".format(mesh_path))
            continue

        fbx_path = mesh_path.replace('.mesh', '.fbx')
        if fbx_path == mesh_path:
            fbx_path = mesh_path + '.fbx'

        print("=" * 60)
        print(" Converting: {0}".format(os.path.basename(mesh_path)))
        print("=" * 60)

        cmd = [
            blender_path,
            "--background",
            "--python", exporter_script,
            "--", mesh_path, fbx_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] {0} -> {1}".format(
                os.path.basename(mesh_path), os.path.basename(fbx_path)))
        else:
            print("[ERRO] Blender falhou:")
            # Mostrar apenas as linhas relevantes do stderr/stdout
            for line in result.stdout.split('\n'):
                if any(k in line for k in ['ERRO', 'Error', 'Traceback', 'assert', 'MeshDTO', 'OK']):
                    print("  " + line)
            if result.stderr:
                for line in result.stderr.split('\n')[-5:]:
                    print("  " + line)

        print("")


if __name__ == '__main__':
    main()
