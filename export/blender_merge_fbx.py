# -*- coding: utf-8 -*-
"""
Blender-side script to Merge multiple NeoX .mesh files and export to a single FBX.
Usage: blender --background --python blender_merge_fbx.py -- <out_path> [--gis <gis_path>] <mesh1> <mesh2> ...
"""
import bpy
import os
import sys
import argparse

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import internal fbx module logic (reuse)
from export.blender_fbx import clear_scene, import_neox_mesh

def main():
    if "--" not in sys.argv:
        sys.exit(1)
        
    argv = sys.argv[sys.argv.index("--") + 1:]
    
    # Simple parse for out_path, gis_path and meshes
    out_path = argv[0]
    meshes = []
    gis_path = None
    
    i = 1
    while i < len(argv):
        if argv[i] == "--gis" and i + 1 < len(argv):
            gis_path = argv[i+1]
            i += 2
        else:
            meshes.append(argv[i])
            i += 1
            
    if not meshes:
        print("[ERRO] No meshes provided for merge.")
        sys.exit(1)
        
    clear_scene()
    
    imported_objects = []
    for m in meshes:
        if os.path.exists(m):
            obj = import_neox_mesh(m)
            imported_objects.append(obj)
            
    # GIS Integration (Phase 2 Stub)
    if gis_path:
        print(f"[Blender] GIS Detected: {gis_path}")
        print("[Aviso] GIS Animation parsing for merge is currently a STUB (Phase 2 planned).")

    # Final Export
    print(f"[Blender] Exporting merge to: {out_path}")
    bpy.ops.export_scene.fbx(
        filepath=out_path,
        use_selection=False,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        bake_anim=True,
        armature_nodetype='NULL'
    )
    print("[OK] Merge complete.")

if __name__ == "__main__":
    main()
