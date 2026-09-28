# NeoX `.gis` Binary Layout (bycodex53)

Este documento descreve o layout binario observado nos arquivos `.gis` do NeoX, com foco em parsing robusto e sem drift.

Ele foi escrito a partir da engenharia reversa aplicada no parser em `core/read_neox_sub_animation.py` e validado em colecoes reais grandes.

## 1) Tipos de arquivo `.gis`

O parser separa os arquivos em 3 grupos principais:

- **SubAnim (`Layouts A/B/C/E`)**: contem PRS animado por bone.
- **Container RGIS (`Layout D`)**: indice de sub-anims + bind pose, sem stream PRS animado.
- **Falso `.gis` (DDS)**: textura com extensao trocada.

Deteccao inicial por magic:

- `b"RGIS"` -> Layout D
- `b"DDS "` -> erro explicito (nao e animacao)
- caso contrario -> SubAnim

## 2) Cabecalho comum de SubAnim

Offsets em bytes (LE):

- `0x00..0x1F`  : `anim_name` (char[32], null-terminated)
- `0x20..0x3F`  : `anim_root_name` (char[32])
- `0x40..0x5F`  : `root_bone_name` (char[32])
- `0x60..0x61`  : `bone_count` (u16)
- `...`         : `bone_count * 32` bytes de nomes de bones
- `...`         : `AnimInfo` (14 bytes)
- `...`         : `global_key_count` (u16)
- `...`         : `global_key_times` (`global_key_count * f32`)
- `...`         : inicio do stream PRS

### AnimInfo (14 bytes)

Ordem de leitura:

- `fps` (u32)
- `is_loop` (u8)
- `has_scaled` (u8)
- `prs_flags` (u16)
- `accum_flags` (u32)
- `pack_prs_flags` (u8)
- `bone_separate_flags` (u8)

Semantica importante:

- `pack_prs_flags=4` -> rotacao `float32 quat` (16 bytes/frame)
- `pack_prs_flags=6` -> rotacao `half_quat` (8 bytes/frame)
- `bone_separate_flags=0` -> stream classico (A/B/C)
- `bone_separate_flags=1` -> stream separado (E)

## 3) Layouts A/B/C (bone_sep=0)

Cada bone segue a estrutura:

- `has_pos` (u8)
- `has_rot` (u8)
- `has_scale` (u8)
- `euler_reserved` (u8)
- `pos`   : `(global_key_count if has_pos else 1) * vec3_f32`
- `rot`   : `(global_key_count if has_rot else 1) * quat(codec)`
- `scale` : `(global_key_count if has_scale else 1) * half3`

Regra de fechamento valida:

- Depois de `bone_count` bones, sobra exatamente **1 byte** (`0x00`) no EOF.

### A vs B vs C

- **A**: `root_bone_name` preenchido em `0x40`.
- **B**: `root_bone_name` vazio em `0x40`.
- **C**: tipicamente `fps=0xFFFFFFFF` + `pack_prs_flags=6` (`half_quat`).

## 4) Layout D (RGIS container)

`RGIS` nao contem PRS animado de subanim; contem metadados e bind pose.

Estrutura observada:

- Header RGIS (`magic`, versao, `sub_anim_count`, `bone_count`)
- `bone_count * 32` nomes de bones
- `bone_count * 40` bind pose (`pos_f32 + quat_f32 + scale_f32`)
- bloco de indice com stride fixo por subanim (geralmente 1140 bytes)

Uso pratico:

- Ler metadados/indice no RGIS.
- Carregar o `.gis` individual para o PRS animado real.

## 5) Layout E (bone_sep=1): modelo revisado

O insight central: em `bone_sep=1`, o stream nao e simplesmente "um bone apos outro com `global_key_count` fixo".

### 5.1 Timeline local intercalada

Antes de um bone pode existir **header de timeline local**:

- `local_key_count` (u16)
- `local_key_times` (`local_key_count * f32`)

Quando esse header aparece, o parser atualiza um `active_key_count` que passa a governar a leitura dos canais animados seguintes.

### 5.2 Leitura por bone com `active_key_count`

Depois de consumir headers locais (se houver), cada bone le:

- 4 bytes de flags (`has_pos`, `has_rot`, `has_scale`, reservado)
- `pos`   com `active_key_count` se animado, senao 1
- `rot`   com `active_key_count` se animado, senao 1
- `scale` com `active_key_count` se animado, senao 1

### 5.3 Validacao de header local

Para reduzir falso positivo, um header local so e aceito se:

- `1 < local_key_count <= 512`
- bloco cabe no arquivo
- primeiro tempo proximo de `0.0`
- primeiros tempos sao estritamente crescentes
- tempos em faixa plausivel (`<= 200000` ms)

Existe um guard adicional quando `local_key_count > bone_count`.

## 6) Codecs e tamanhos por frame

- `pos`: `vec3_f32` -> 12 bytes
- `rot(float32)`: `quat_f32` -> 16 bytes
- `rot(half_quat)`: `quat_f16x4` -> 8 bytes
- `scale`: `half3` (`f16x3`) -> 6 bytes

## 7) Regras de robustez usadas pelo parser

- Parse sequencial (sem seek arbitrario no fluxo principal).
- Validacao leve de stream antes do parse completo.
- Fechamento estrito em EOF-1 para detectar drift.
- Ancoragem de `PRS_START` em `+-32` bytes quando necessario.
- Fallback experimental controlado para subvariantes de `bone_sep+half_quat`.

## 8) EBNF simplificada (SubAnim)

```text
SubAnim = Header, BoneTable, AnimInfo, GlobalTimeline, PrsStream, PadByte ;

GlobalTimeline = global_key_count:u16, global_key_count * f32 ;

PrsStream(layout in A/B/C) = bone_count * BoneTrack(global_key_count) ;

PrsStream(layout in E) = bone_count * (
    { LocalTimelineHeader },
    BoneTrack(active_key_count)
) ;

LocalTimelineHeader = local_key_count:u16, local_key_count * f32 ;

BoneTrack(k) = has_pos:u8, has_rot:u8, has_scale:u8, reserved:u8,
               Pos(has_pos, k), Rot(has_rot, k), Scale(has_scale, k) ;
```

## 9) Observacoes para manutencao

- `root_bone_name` em `0x40` e metadado; nao adicionar "bone extra" por causa dele.
- O indice local de bone muda entre arquivos; usar nome para correlacao.
- Evitar assumir que `global_key_count` vale para todos os bones em `bone_sep=1`.
- Para regressao, sempre testar em corpus real grande (nao apenas amostras sinteticas).

## 10) Estado de validacao (corpus usado)

Com o parser atual:

- `character-folder\leila\common_gis` -> `257/257` arquivos parseados
- `.outros\male\common\dongzuoku_gis` -> `2163/2163` arquivos parseados

## 11) Postmortem: personagem deitado / malha torcida no app

Sintoma observado:

- personagem deitado durante playback
- bones em orientacoes opostas
- malha torcida mesmo com parser fechando stream corretamente

Causa raiz:

- O problema principal **nao estava no parser `.gis`**.
- Estava no runtime de skinning, em uma inconsistencia de convencao de matriz:
  - pose animada era montada com `BoneTran(...).to_matrix().T`
  - bind da malha era consumido via `bind_matrix.T`
  - a combinacao gerava base de transformacao divergente (rot/trans), resultando em skin matrices longe da identidade na tpose.

Correcao aplicada:

- Implementada construcao explicita de TRS em convencao de coluna no runtime:
  - `runtime/animation/skinning.py` -> `_build_trs_matrix_col(P, R, S)`
- A mesma convencao passou a ser usada para:
  - matriz local animada por bone
  - base local opcional do RGIS (retarget)
  - injecao de root

Resultado:

- skin matrices na tpose voltaram para perto da identidade
- personagem deixou de ficar deitado
- torcao de malha eliminada no playback

Licao de manutencao:

- Se o parser estiver fechando EOF e quaternions validos, mas a malha distorcer,
  investigar primeiro **convensao de matriz/ordem de multiplicacao/transposicao**
  no pipeline de skinning, antes de mexer no parser binario.

---

Se no futuro surgir nova variante, o ponto de extensao recomendado e a deteccao/consumo de `LocalTimelineHeader` e a politica de `active_key_count`.
