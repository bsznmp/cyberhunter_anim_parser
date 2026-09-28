Para exportar uma animação .fbx completa (all layers) via bpy e garantir reimportação limpa no próprio Blender, você precisa satisfazer um conjunto de pré-condições estruturais + parâmetros de exportação + consistência de dados de animação (F-Curves / Actions / NLA).

Vou direto ao ponto, em formato operacional.

1) Estrutura mínima que o bpy espera (INPUT correto)
A. Objetos válidos
Armature (rig principal)
Mesh (skinned ao armature)
Modificadores aplicados corretamente:
Armature Modifier ativo
Object.parent = Armature (ou via modifier)
B. Animação corretamente definida

O Blender não exporta "layers" automaticamente — ele exporta:

Active Action (ação ativa no objeto/armature)
NLA Tracks (se habilitado)
Você precisa garantir:
✔ Actions válidas
bpy.data.actions contendo animações
Cada action com:
fcurves válidas
data_path correto (ex: pose.bones["Bone"].location)
keyframes consistentes
✔ Associação da action ao rig:
armature.animation_data_create()
armature.animation_data.action = action
✔ OU uso de NLA (recomendado para "all layers")
track = armature.animation_data.nla_tracks.new()
strip = track.strips.new(action.name, start_frame, action)
2) Problema central: "All Layers" no FBX

FBX não tem conceito nativo de "layers" igual ao Blender.

O que funciona na prática:

Você precisa escolher entre:

Estratégia A — Bake everything (mais segura)

Converte tudo em uma única animação contínua:

NLA → bake
constraints → bake
drivers → bake
Estratégia B — Exportar múltiplas ações

Cada Action vira um "take" no FBX

3) Parâmetros CRÍTICOS do exportador FBX (bpy.ops.export_scene.fbx)
Configuração recomendada (robusta)
bpy.ops.export_scene.fbx(
    filepath="output.fbx",

    use_selection=False,

    object_types={'ARMATURE', 'MESH'},

    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',

    add_leaf_bones=False,  # evita lixo estrutural

    use_armature_deform_only=True,

    bake_anim=True,

    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,

    bake_anim_force_startend_keying=True,

    bake_anim_step=1.0,

    bake_anim_simplify_factor=0.0,

    axis_forward='-Z',
    axis_up='Y'
)
4) Requisitos CRÍTICOS para evitar erros (F-Curves / import)
A. F-Curves válidas

Problemas comuns:

data_path inválido → FBX quebra silenciosamente
bones renomeados sem atualizar F-Curves
curvas vazias
Verificação:
for action in bpy.data.actions:
    for fc in action.fcurves:
        if not fc.data_path:
            print("F-Curve inválida:", action.name)
B. Keyframes obrigatórios em range completo

Se não houver keyframes no início/fim:

→ Blender reimporta com glitches

Use:

bake_anim_force_startend_keying=True
C. Constraints / Drivers

FBX NÃO suporta diretamente.

→ obrigatório:

bake_anim=True
D. Escala / Transform

Antes de exportar:

bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
E. Armature consistente
Sem bones órfãos
Hierarquia válida
Sem loops
5) Pipeline recomendado (sem erro)
Etapas:
1. Validar dados
actions existentes
fcurves válidas
armature consistente
2. Converter para NLA (se necessário)
cada action → strip
3. Bake total
elimina dependências
4. Exportar com:
bake_anim=True
use_all_actions=True
use_nla_strips=True
6) Diagnóstico de erros comuns
❌ Animação não aparece ao reimportar

→ Action não estava ativa
→ NLA não habilitado

❌ Apenas parte da animação exportada

→ faltou:

bake_anim_use_all_actions
ou use_nla_strips
❌ Deformações quebradas

→ use_armature_deform_only errado
→ pesos inválidos

❌ F-Curves errors

→ data_path inválido
→ bone inexistente

7) Checklist objetivo (pré-export)
 Armature com animation_data
 Actions associadas ou no NLA
 F-Curves válidas
 Sem constraints não baked
 Transform aplicado
 Bake ativado
 All actions ou NLA habilitado



 Abaixo está um guia teórico estruturado (pipeline estilo LLMOps) para exportação FBX confiável via bpy, com foco em determinismo, validação progressiva e eliminação de inconsistências de F-Curves.

0) Modelo mental do pipeline

Objetivo: transformar um estado arbitrário do Blender em um estado exportável determinístico

Fluxo macro:
INGEST → VALIDATE → NORMALIZE → CANONICALIZE → BAKE → EXPORT → VERIFY
1) INGEST (coleta de estado)
Objetivo

Mapear completamente o estado da cena relevante para animação.

Entradas necessárias
Armatures
Meshes vinculados
Actions (bpy.data.actions)
NLA Tracks
Constraints / Drivers
F-Curves
Pseudocódigo
scene_data = {
  armatures: get_all_armatures(),
  meshes: get_skinned_meshes(),
  actions: bpy.data.actions,
  nla: extract_nla_tracks(),
  constraints: scan_constraints(),
  drivers: scan_drivers()
}
2) VALIDATE (detecção de inconsistências)
Objetivo

Detectar tudo que pode quebrar export ou reimport.

Checks críticos
A. F-Curves
data_path inválido
bone inexistente
curvas vazias
channels duplicados
for action in actions:
  for fcurve in action.fcurves:
    assert is_valid_data_path(fcurve.data_path)
    assert target_exists(fcurve)
    assert has_keyframes(fcurve)
B. Actions órfãs
actions não vinculadas a nenhum objeto
if action.users == 0:
  mark_as_orphan(action)
C. Armature integrity
bones sem hierarquia
nomes inconsistentes
D. Constraints / Drivers
presença implica necessidade de bake
Saída

Relatório estruturado:

{
  errors: [...],
  warnings: [...],
  auto_fix_candidates: [...]
}
3) NORMALIZE (correções estruturais)
Objetivo

Eliminar estados inválidos antes da canonização.

Ações típicas
A. Remover lixo
delete_empty_fcurves()
remove_orphan_actions()
B. Corrigir data_path
remapear bones renomeados
C. Garantir animation_data
if not armature.animation_data:
    armature.animation_data_create()
4) CANONICALIZE (padronização de animação)
Objetivo

Transformar múltiplas fontes de animação em um modelo uniforme.

Estratégia principal

→ Converter tudo para NLA como fonte única de verdade

A. Garantir que cada Action está representada no NLA
for action in actions:
  track = ensure_nla_track(armature)
  strip = track.add_strip(action)
B. Ordenação temporal
evitar sobreposição caótica
definir offsets claros
current_frame = 0
for action in actions:
  place_strip(action, start=current_frame)
  current_frame += action.length + padding
C. Isolamento
mutar outras tracks durante validação
Resultado esperado
NLA determinístico
sem dependência de “active action”
5) BAKE (colapso de dependências)
Objetivo

Eliminar tudo que FBX não suporta:

constraints
drivers
procedural animation
Estratégia
Bake por armature
bake(
  frame_start,
  frame_end,
  step=1,
  only_selected=True,
  visual_keying=True,
  clear_constraints=False
)
Parâmetros críticos
visual_keying=True → resolve constraints
step=1 → fidelidade máxima
force_start_end_keying=True
Pós-bake
remover constraints (opcional)
validar novas F-Curves
6) EXPORT (serialização FBX)
Objetivo

Exportar com configuração que preserve:

hierarquia
animação completa
compatibilidade de reimport
Configuração lógica
export_fbx({
  bake_anim: True,
  use_nla_strips: True,
  use_all_actions: True,
  simplify: 0.0,
  add_leaf_bones: False
})
Garantias
todas as animações incluídas
nenhuma dependência externa
7) VERIFY (round-trip validation)
Objetivo

Garantir que o FBX gerado é reimportável sem perda

Estratégia
A. Reimportar automaticamente
imported_scene = import_fbx(filepath)
B. Comparar
Checks:
número de bones
número de keyframes
duração da animação
presença de todas actions/takes
assert compare_animation(original, imported)
C. Heurísticas de erro
diferença de keyframe count → perda no bake
bones extras → problema de leaf bones
animação faltando → NLA mal configurado
8) FEEDBACK LOOP (LLMOps mindset)
Objetivo

Auto-ajuste iterativo

Estratégia
Se erro detectado:
if verify_failed:
  classify_error()
  apply_fix_strategy()
  rerun_pipeline()
Exemplos
Erro	Ação corretiva
F-Curve inválida	rebuild data_path
animação ausente	forçar NLA strips
deform quebrado	rebake com visual_keying
escala inconsistente	apply transforms
9) PRINCÍPIOS CHAVE (o que elimina 90% dos erros)
1. Nunca confiar em estado implícito

→ sempre explicitar (NLA + bake)

2. Sempre bakear

→ FBX ≠ Blender runtime

3. NLA como single source of truth

→ evita ambiguidade de Actions

4. Validar antes e depois

→ pipeline, não comando único

5. Determinismo > conveniência

→ mesma entrada → mesmo FBX

10) Resumo operacional
1. Coletar dados
2. Validar F-Curves / Actions
3. Corrigir inconsistências
4. Converter tudo para NLA
5. Bake completo (visual)
6. Exportar com flags corretas
7. Reimportar e validar
8. Iterar se necessário