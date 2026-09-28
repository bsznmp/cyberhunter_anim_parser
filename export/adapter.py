# -*- coding: utf-8 -*-
"""
Adaptador para gerenciar a execução do Blender em modo headless para exportação de FBX.
Unifica a lógica de localização do executável e acionamento de scripts externos.
"""
import os
import shutil
import subprocess

class BlenderAdapter:
    def __init__(self, blender_path=None):
        self.blender_executable = blender_path or self.find_blender()

    @staticmethod
    def find_blender():
        """Tenta localizar o executável do Blender no PATH ou em caminhos comuns do Windows."""
        b = shutil.which("blender")
        if b:
            return b
            
        common_paths = [
            r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
        ]
        for p in common_paths:
            if os.path.exists(p):
                return p
        return None

    @staticmethod
    def detect_gis(folder_path):
        """Busca recursivamente por arquivos .gis na pasta especificada."""
        if not folder_path or not os.path.isdir(folder_path):
            return None
        for root, _dirs, files in os.walk(folder_path):
            for f in sorted(files):
                if f.lower().endswith('.gis'):
                    return os.path.join(root, f)
        return None

    def export_fbx(self, mesh_path, out_path):
        """Executa o script de exportação FBX do Blender para um único arquivo .mesh."""
        if not self.blender_executable:
            return False, "Blender não encontrado."

        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exporter_script = os.path.join(script_dir, "export", "blender_fbx.py")

        if not os.path.exists(exporter_script):
            return False, f"Script de exportação não encontrado em: {exporter_script}"

        cmd = [
            self.blender_executable,
            "--background",
            "--python", exporter_script,
            "--", mesh_path, out_path
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(out_path):
                return True, ""
            else:
                return False, self._format_blender_error(result.stdout, result.stderr)
        except Exception as e:
            return False, str(e)

    def export_merge_fbx(self, mesh_paths, out_path, gis_path=None):
        """Executa o script de merge FBX do Blender para múltiplos arquivos .mesh."""
        if not self.blender_executable:
            return False, "Blender não encontrado."

        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exporter_script = os.path.join(script_dir, "export", "blender_merge_fbx.py")

        if not os.path.exists(exporter_script):
            return False, f"Script de merge não encontrado em: {exporter_script}"

        # Monta comando: blender -- <output.fbx> [--gis <file>] <mesh1> <mesh2> ...
        cmd = [self.blender_executable, "--background", "--python", exporter_script, "--", out_path]
        if gis_path:
            cmd += ["--gis", gis_path]
        cmd += mesh_paths

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and os.path.exists(out_path):
                return True, ""
            else:
                return False, self._format_blender_error(result.stdout, result.stderr)
        except Exception as e:
            return False, str(e)

    def _format_blender_error(self, stdout, stderr):
        """Filtra as linhas relevantes do stdout do Blender para exibição de erros."""
        error = ""
        for line in stdout.split('\n'):
            if any(k in line for k in ('Error', 'ERRO', 'Traceback', 'assert')):
                error += line + "\n"
        if not error and stderr:
            error = stderr.split('\n')[-3:] # Pega as últimas linhas do stderr se nada for achado no stdout
        return error or "Erro desconhecido durante a exportação via Blender."
