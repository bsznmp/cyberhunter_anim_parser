Abaixo está um mapa mental técnico do bpy focado em animação + FBX, estruturado como um grafo de dependência real (não superficial), orientado para engenharia reversa e automação robusta.

🧠 1) Núcleo do sistema (grafo principal)
Scene
 ├── Object (type=ARMATURE)
 │    ├── data → Armature
 │    ├── pose → Pose
 │    │     └── bones → PoseBone[]
 │    │           └── constraints
 │    │
 │    ├── animation_data
 │    │     ├── action → Action
 │    │     └── nla_tracks → NlaTrack[]
 │    │             └── strips → NlaStrip[]
 │    │                     └── action → Action
 │    │
 │    └── modifiers (Armature)
 │
 ├── Object (type=MESH)
 │    ├── vertex_groups
 │    └── modifiers (Armature)
 │
 └── bpy.data.actions → Action[]
🎯 2) Entidades críticas (e suas responsabilidades)
2.1 bpy.types.Action

Função: container de animação (nível lógico)

Action
 └── fcurves → FCurve[]
        └── keyframe_points

📌 Insight:

Uma Action = conjunto de curvas
Não está ativa por padrão → precisa de binding
2.2 bpy.types.FCurve

Função: curva de animação (nível físico/exportável)

FCurve
 ├── data_path  (ex: pose.bones["Bone"].location)
 ├── array_index (X/Y/Z)
 └── keyframes

📌 Insight crítico:
→ FBX exporta essencialmente isso
→ se isso estiver errado → tudo quebra

2.3 bpy.types.AnimationData

Função: ponte entre objeto e animação

AnimationData
 ├── action (ativa)
 └── nla_tracks

📌 Insight:

Sem isso → animação "invisível"
É o ponto de controle do pipeline
2.4 bpy.types.NlaTrack / NlaStrip

Função: sistema de camadas (pseudo “layers”)

NlaTrack
 └── strips
      └── action

📌 Insight crítico:
→ FBX usa isso como base para múltiplas animações
→ é a forma mais próxima de "all layers"

2.5 bpy.types.PoseBone

Função: alvo final da animação

PoseBone
 ├── location
 ├── rotation_quaternion / euler
 ├── scale
 └── constraints

📌 Insight:

F-Curves apontam aqui
Constraints vivem aqui → precisam de bake
🔄 3) Fluxo de animação (como os dados fluem)
Pipeline interno do Blender:
Action
 → FCurves
   → data_path resolve para PoseBone
     → Pose evaluation
       → Constraints / Drivers
         → Resultado final (viewport)
Problema:

FBX NÃO exporta:

constraints
drivers
evaluation runtime
Solução:
Bake → converte tudo → FCurves puras
⚠️ 4) Pontos de falha (onde 90% dos erros acontecem)
4.1 data_path inválido

Exemplo quebrado:

pose.bones["Bone.001"].location

Se o bone não existir:
→ FCurve silenciosamente inválida

4.2 Action não vinculada
Action existe → mas não está em:
- animation_data.action
- NLA

→ não exporta

4.3 Dependência de constraints
Bone → constraint → target

→ FBX ignora
→ resultado: animação errada

4.4 NLA inconsistente
strips sobrepostos
muted tracks
ordem indefinida
4.5 Transform não aplicado
Object scale ≠ 1

→ deformação errada no FBX

🏗️ 5) Modelo canônico (estado ideal para export)
Armature
 └── animation_data
       └── NLA (source of truth)
             └── strips organizados sequencialmente

FCurves:
 ✔ válidas
 ✔ completas (start/end)
 ✔ sem dependência externa

Constraints:
 ✖ inexistentes (ou baked)

Transforms:
 ✔ aplicados
🔧 6) Mapeamento direto para export FBX
O exportador lê:
Object
 └── animation_data
       ├── action (se NLA off)
       └── NLA (se enabled)
             └── strips
                   └── actions
                         └── FCurves
Flags que controlam isso:
bake_anim_use_nla_strips=True
bake_anim_use_all_actions=True
🔍 7) Estratégia de inspeção (debug real)
7.1 Inspecionar Actions
for a in bpy.data.actions:
    print(a.name, len(a.fcurves))
7.2 Validar FCurves
for fc in action.fcurves:
    print(fc.data_path, fc.array_index)
7.3 Mapear para bones
obj.path_resolve(fc.data_path)

→ se falhar → erro crítico

7.4 Inspecionar NLA
for track in obj.animation_data.nla_tracks:
    for strip in track.strips:
        print(strip.action.name)
🧩 8) Relação com engenharia reversa (seu caso)
O que você extrai de um .mesh / engine:
hierarquia de bones
keyframes
transforms
O que você precisa reconstruir no bpy:
PoseBone ← destino
FCurve   ← representação
Action   ← agrupamento
NLA      ← organização
Pipeline mental:
RAW DATA
 → gerar FCurves
   → montar Action
     → bind no Armature
       → inserir no NLA
         → bake (se necessário)
           → export FBX
🧠 9) Insight avançado (mais importante do guia)

O Blender não é "action-based" — ele é evaluation-based

Ou seja:

Actions = input
Constraints = modificadores
NLA = orquestração
Resultado final ≠ dados armazenados
Consequência direta:

👉 Você nunca deve exportar sem bake
👉 Você nunca deve confiar só em Actions

📌 10) TL;DR operacional
1. Tudo vira FCurve
2. FCurve precisa de data_path válido
3. Actions precisam estar no NLA
4. Constraints precisam virar keyframes (bake)
5. FBX lê apenas o resultado final