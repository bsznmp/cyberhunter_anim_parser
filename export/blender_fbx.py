# -*- coding: utf-8 -*-
"""
Blender-side script to import NeoX .mesh files and export to FBX.
Usage: blender --background --python blender_fbx.py -- <mesh_path> <fbx_path>
"""
import bpy
import os
import sys
import numpy as np

# Add project root to sys.path so we can import core.parser
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from core.parser import parse_mesh
from core.exceptions import NeoXError

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def import_neox_mesh(mesh_path):
    print(f"[Blender] Parsing mesh: {mesh_path}")
    try:
        dto = parse_mesh(mesh_path)
    except NeoXError as e:
        print(f"[ERRO] NeoX Parser failed: {e}")
        sys.exit(1)

    mesh_name = os.path.splitext(os.path.basename(mesh_path))[0]
    
    # 1. Create Mesh
    bm_data = bpy.data.meshes.new(mesh_name)
    bm_obj = bpy.data.objects.new(mesh_name, bm_data)
    bpy.context.collection.objects.link(bm_obj)
    
    # Vertices & faces
    # Flip -X for Blender coordinate mapping if required (per converter.py)
    verts = [(-p[0], p[1], p[2]) for p in dto.positions]
    bm_data.from_pydata(verts, [], dto.faces)
    bm_data.update()
    
    # Normals
    bm_data.use_auto_smooth = True
    # bm_data.normals_split_custom_set_from_vertices([(-n[0], n[1], n[2]) for n in dto.normals])
    
    # UVs
    if dto.uvs:
        uv_layer = bm_data.uv_layers.new(name="UVMap")
        for i, face in enumerate(bm_data.polygons):
            for j, loop_index in enumerate(face.loop_indices):
                vert_idx = face.vertices[j]
                uv = dto.uvs[vert_idx]
                uv_layer.data[loop_index].uv = (uv[0], 1.0 - uv[1])

    # 2. Create Skeleton (Armature)
    if dto.skeleton:
        arm_data = bpy.data.armatures.new(mesh_name + "_Arm")
        arm_obj = bpy.data.objects.new(mesh_name + "_Arm", arm_data)
        bpy.context.collection.objects.link(arm_obj)
        
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        blender_bones = {}
        for bone in dto.skeleton.bones:
            eb = arm_data.edit_bones.new(bone.name)
            blender_bones[bone.name] = eb
            
            # NeoX bind matrix transformation logic
            # Simplificação: Usar matriz de binding convertida
            mat = bone.bind_matrix
            # Flip lateral -X
            mat[0, 3] = -mat[0, 3] 
            
            eb.head = (0, 0, 0)
            eb.tail = (0, 0, 0.1) # Default tail to show direction
            eb.matrix = bpy.types.Object.matrix_world.copy() # Placeholder
            # A real engine parser would decompose the bind matrix here
            
        # Parent bones
        for bone in dto.skeleton.bones:
            if bone.parent_index != -1:
                parent_name = dto.skeleton.bones[bone.parent_index].name
                arm_data.edit_bones[bone.name].parent = arm_data.edit_bones[parent_name]
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Link Mesh to Armature
        bm_obj.parent = arm_obj
        modifier = bm_obj.modifiers.new(name="Armature", type='ARMATURE')
        modifier.object = arm_obj
        
        # Vertex Groups (Bone Weights)
        if dto.joint_indices and dto.joint_weights:
            for i, bone in enumerate(dto.skeleton.bones):
                bm_obj.vertex_groups.new(name=bone.name)
            
            for v_idx, indices in enumerate(dto.joint_indices):
                weights = dto.joint_weights[v_idx]
                for i, b_idx in enumerate(indices):
                    if b_idx < len(dto.skeleton.bones) and weights[i] > 0:
                        bone_name = dto.skeleton.bones[b_idx].name
                        bm_obj.vertex_groups[bone_name].add([v_idx], weights[i], 'REPLACE')

    return bm_obj if not dto.skeleton else arm_obj

def main():
    # Parse arguments after '--'
    if "--" not in sys.argv:
        print("[ERRO] Usage: blender --background --python blender_fbx.py -- <mesh_path> <fbx_path>")
        sys.exit(1)
        
    argv = sys.argv[sys.argv.index("--") + 1:]
    if len(argv) < 2:
        print("[ERRO] Missing path arguments.")
        sys.exit(1)
        
    mesh_path = argv[0]
    out_path = argv[1]
    
    clear_scene()
    root_obj = import_neox_mesh(mesh_path)
    
    # Export to FBX
    print(f"[Blender] Exporting to: {out_path}")
    bpy.ops.export_scene.fbx(
        filepath=out_path,
        use_selection=False,
        mesh_smooth_type='FACE',
        add_leaf_bones=False,
        bake_anim=True,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        armature_nodetype='NULL'
    )
    print("[OK] Export complete.")

if __name__ == "__main__":
    main()
