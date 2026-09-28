Você quer basicamente fazer:

[.mesh] + [.anim] → reconstruir → exportar → .fbx

Isso envolve 3 sistemas:

1. Mesh (geometria)
vértices (posição, normal, UV)
índices (triangles)
skin weights (ESSENCIAL pra animação)
2. Skeleton (hierarquia)
bones
parent/child
bind pose (matriz base)
3. Animation
keyframes por bone
posição / rotação / escala
tempo

⚙️ PIPELINE COMPLETO
ETAPA 1 — Parse do MESH

Você precisa extrair:

mesh = {
    "vertices": [...],      # (x, y, z)
    "normals": [...],
    "uvs": [...],
    "indices": [...],
    "weights": [...],       # [(bone_id, weight)]
}
ETAPA 2 — Parse do SKELETON
skeleton = {
    "bones": [
        {
            "name": "spine",
            "parent": 0,
            "bind_matrix": [...],
        }
    ]
}

⚠️ Aqui entra o ponto crítico:

👉 LOCAL vs GLOBAL

Você precisa garantir que:

bind pose está correta
hierarquia respeitada

ETAPA 3 — Parse da ANIMAÇÃO
animation = {
    "duration": 3.0,
    "fps": 30,
    "tracks": {
        "spine": [
            {
                "time": 0.0,
                "pos": (x,y,z),
                "rot": (x,y,z,w),
                "scale": (1,1,1)
            }
        ]
    }
}
🚨 PROBLEMA CENTRAL (QUE TODO MUNDO ERRA)

Os dados geralmente vêm assim:

posição → LOCAL
rotação → LOCAL
mas FBX espera → GLOBAL ou transform acumulado

👉 Você precisa fazer:

global_transform = parent_transform * local_transform
🧩 ETAPA 4 — RECONSTRUÇÃO

Você precisa montar o esqueleto completo:

def build_global_pose(bone, skeleton, local_pose):
    if bone["parent"] == -1:
        return local_pose
    parent = skeleton["bones"][bone["parent"]]
    return build_global_pose(parent, skeleton, parent_pose) @ local_pose


Exemplo base:
```
import bpy

# Criar armature
bpy.ops.object.armature_add()
armature = bpy.context.object

# Criar bones
for bone in skeleton["bones"]:
    b = armature.data.edit_bones.new(bone["name"])
    # definir head/tail

# Criar mesh
mesh = bpy.data.meshes.new("mesh")
obj = bpy.data.objects.new("mesh_obj", mesh)

# Aplicar pesos
# vertex groups...

# Criar animação
action = bpy.data.actions.new("Anim")

# Inserir keyframes
```

Exportar:
bpy.ops.export_scene.fbx(filepath="output.fbx")

🔥 PONTO AVANÇADO (NÍVEL PROFISSIONAL)
Skinning (o segredo da animação funcionar)

Cada vértice precisa:

vertex = {
    "bone_ids": [0, 3, 5],
    "weights": [0.7, 0.2, 0.1]
}

No Blender:

vg = obj.vertex_groups.new(name="spine")
vg.add([vertex_index], weight, 'ADD')

---------------------------------------------------------------

Se o mesh + skeleton está exportando corretamente, então o pipeline já tem:

✔️ hierarquia válida
✔️ bind pose consistente
✔️ skinning funcionando

👉 O que falta agora é acoplar a animação corretamente ao skeleton existente.

🔥 O PROBLEMA AGORA É OUTRO

Não é mais parsing.

É alinhamento de espaço + aplicação correta de keyframes.

🧠 CHECKPOINT CRÍTICO

Você disse:

nomes dos bones são iguais no mesh e na animação

Isso é ótimo — então você pode mapear direto:

bone_map = { bone["name"]: bone for bone in skeleton["bones"] }
⚠️ ONDE NORMALMENTE QUEBRA

Mesmo com nomes iguais, a animação pode estar em:

1. Espaço LOCAL (mais comum)

ou

2. Espaço GLOBAL (menos comum, mas acontece)

Se você aplicar errado:

animação desloca tudo
ossos “saem voando”
modelo deforma errado
🔬 COMO DESCOBRIR O ESPAÇO

Faça esse teste simples:

👉 Teste mental
Se aplicar a animação no root move o personagem inteiro → GLOBAL
Se apenas altera relativo ao pai → LOCAL
🧩 PIPELINE CORRETO (ANIMAÇÃO)
ETAPA 1 — Estrutura limpa

Você precisa garantir algo assim:

animation = {
    "tracks": {
        "spine": [keyframes...],
        "arm_l": [keyframes...],
    }
}
ETAPA 2 — Converter para MATRIZ

Cada keyframe precisa virar uma matriz:

def compose_matrix(pos, rot, scale):
    T = translation_matrix(pos)
    R = quaternion_to_matrix(rot)
    S = scale_matrix(scale)
    return T @ R @ S
⚠️ ORDEM IMPORTA MUITO

Normalmente:

M = T @ R @ S

Se inverter → quebra tudo.

🔥 ETAPA 3 — APLICAR COM HIERARQUIA

Se sua animação for LOCAL:

def get_global_transform(bone, frame_data):
    local = frame_data[bone["name"]]

    if bone["parent"] == -1:
        return local

    parent = skeleton["bones"][bone["parent"]]
    return get_global_transform(parent, frame_data) @ local
🧠 ETAPA 4 — COMPENSAR BIND POSE (ABSURDAMENTE IMPORTANTE)

Aqui está o ponto que quase ninguém percebe:

👉 FBX / Blender espera:

final_transform = anim_transform @ inverse_bind_pose

Se você não fizer isso:

animação fica deslocada
ossos “esticam”
💀 ERRO CLÁSSICO

Você exporta skeleton certo…
mas ignora bind pose na animação.

Resultado:

animação parece "quase certa", mas tudo está levemente errado

🧱 ETAPA 5 — BLENDER (integração correta)
Criar ação:
action = bpy.data.actions.new("MyAnim")
armature.animation_data_create()
armature.animation_data.action = action
Aplicar keyframes:
for frame in frames:
    bpy.context.scene.frame_set(frame)

    for bone in armature.pose.bones:
        data = animation["tracks"].get(bone.name)
        if not data:
            continue

        kf = data[frame]

        bone.location = kf["pos"]
        bone.rotation_quaternion = kf["rot"]
        bone.scale = kf["scale"]

        bone.keyframe_insert(data_path="location")
        bone.keyframe_insert(data_path="rotation_quaternion")
        bone.keyframe_insert(data_path="scale")
⚠️ POSSÍVEL PROBLEMA NO SEU CASO

Como você já exporta o skeleton corretamente:

👉 seu bind pose já está aplicado no armature

Então:

🔥 Você NÃO deve aplicar transform global direto

Você deve aplicar:

👉 transform RELATIVO AO REST POSE

🧪 TESTE QUE EU RECOMENDO (DEBUG)

Antes de tudo:

Pegue 1 bone (ex: spine)
Aplique apenas rotação
Veja se:
gira corretamente → OK
desloca → espaço errado
deforma mesh → peso/bind errado
🔥 ESTRATÉGIA PROFISSIONAL
Faça isso em etapas:
1. ✔️ Aplicar apenas ROOT motion
2. ✔️ Aplicar apenas rotação (sem posição)
3. ✔️ Aplicar tudo

------------------------------------------------------



