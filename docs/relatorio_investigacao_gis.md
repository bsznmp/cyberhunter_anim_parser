# Relatório de Investigação: Formato NeoX .gis (Animação)

**Data da última atualização:** 2026-03-24
**Status:** Investigação em andamento — bloco de tracks não confirmado

---

## 1. O Que Foi Confirmado (Com Evidências Binárias)

### 1.1 Variantes do Formato

| Atributo | Variante RGIS (Parent/Lib) | Variante Raw (Child/Clip) |
|:---------|:--------------------------|:--------------------------|
| Magic    | `RGIS` (0x52474953)       | Nenhum (começa com nome ASCII) |
| Bone Count | uint32 (4 bytes)        | uint16 (2 bytes) @ offset 0x60 |
| Bone Entry | 64 bytes               | 32 bytes |
| Uso      | `common.gis`, `dongzuoku.gis` | `spawn.gis`, `idle.gis` |

### 1.2 Layout do Cabeçalho Raw (Variante Child) — CONFIRMADO

```
[0x00]  64 bytes  Instance Name (null-padded ASCII)
[0x40]  32 bytes  Anim Root Name (null-padded ASCII)
[0x60]   2 bytes  bone_count (uint16)
[0x62]  bone_count * 32 bytes  Bone Symbols (nomes, 32b cada)
  ?     20 bytes  Global Context Block (ver 1.3)
  ?     key_count * 4 bytes  Timeline (float32 ms timestamps)
  ?     ???       Track List (ver Seção 3 — NÃO CONFIRMADO)
  ?     480 bytes Pivot/Root Motion Block (sentinel: file_size - 480)
```

### 1.3 Global Context Block (20 bytes) — CORRIGIDO

Layout confirmado comparando bytes binários com `animation_format.txt`:

```
Offset  Tam  Campo             Evidência
─────────────────────────────────────────────────────────────────
[0:4]    4B  sample_fps        uint32 LE — valor 30 (0x1e000000) ou
                                0xFFFFFFFF (inválido em tpose.gis)
[4]      1B  loop              uint8 — 0=False, 1=True
                                CONFIRMADO: daomadan_spawn=0, gedou_spawn_idle=1,
                                win=0, xingchen_spawn_idle=1, tpose=1
[5]      1B  has_scaled        uint8 — 0=False, 1=True
[6:8]    2B  prs_flags         uint16 LE — valor 7 (0x07, 0x00) em todos os
                                arquivos testados; 7 = pos(1)|rot(2)|scale(4)
[8:12]   4B  accum_flags       uint32 LE — sempre 0 nos arquivos testados
[12:14]  2B  pack_prs_flags    uint16 LE — valor 4 nos arquivos testados
[14:16]  2B  key_count         uint16 LE — CONFIRMADO como contagem global
                                de frames da timeline (valores: 2, 81, 101,
                                161, 222, 311)
[16:20]  4B  bone_separate_flags uint32 LE — sempre 0 nos arquivos testados
```

**Erros corrigidos no layout anterior (gis_parser.py):**

| Campo         | Layout Errado                  | Layout Correto               |
|:--------------|:-------------------------------|:-----------------------------|
| `fps_raw`     | uint16 @ [2:4] → sempre 0     | uint32 @ [0:4] → 30          |
| `loop`        | hardcoded `False`; byte [6]=7 não é loop | uint8 @ [4] → 0/1  |
| `has_scaled`  | não lido (`u2` ignorado @ [4:6]) | uint8 @ [5]                |
| `prs_flags`   | byte [6] interpretado como "loop" | uint16 @ [6:8] = 7        |
| `key_count`   | uint16 @ [14:16] — **COINCIDENTEMENTE CORRETO** | confirmado |

### 1.4 Timeline — CONFIRMADO

Localização: imediatamente após o Global Context Block.
Formato: `key_count × float32` (timestamps em milissegundos).

Verificado em daomadan_spawn.gis (key_count=222, fps=30):
```
33.33ms, 66.67ms, 100.00ms, 133.33ms, ...  (intervalos de 1000/30 ms)
```

### 1.5 Pivot / Root Motion Block — CONFIRMADO (POSIÇÃO)

Os últimos 480 bytes de cada arquivo `.gis` Raw são o bloco de Root Motion.
Sentinela: `file_size - 480` = offset do início do bloco.

Verificado em todos os 5 arquivos testados — pivô encontrado na posição correta.

**Conteúdo interno do bloco:** não mapeado ainda.

---

## 2. O Que Está Documentado em `animation_format.txt` (Fonte Oficial NeoX)

O arquivo `docs/ref/animation_format.txt` contém a especificação oficial NeoX
(fonte: documentação interna NeteEase/NeoX Engine). Dados relevantes confirmados:

### 2.1 Estrutura da Track por Bone (do formato oficial)

```
key_data per bone:
    has_pos_keys        bool (uint8)
    has_rot_keys        bool (uint8)
    has_scale_keys      bool (uint8)
    euler_flags         bool (uint8)
    position_key_count  uint16   ← PER-BONE, não global
    positions           position_key_count × 12 bytes (3×float32)
    rot_key_count       uint16   ← PER-BONE, não global
    rot                 rot_key_count × 16 bytes (4×float32)
    scale_key_count     uint16   ← PER-BONE, não global
    scales              scale_key_count × 12 bytes (3×float32)
```

**Ponto crítico:** mesmo quando `has_scale_keys = False`, `scale_key_count = 1`
(1 keyframe de pose estática). O mínimo de keyframes por canal é **sempre 1**,
nunca 0.

**Implicação para o parser atual:** o gis_parser usa o `key_count` global para
todos os canais de todos os bones — isto está ERRADO. Cada canal tem seu próprio
contador.

### 2.2 Campos Confirmados via animation_format.txt

| Campo           | Valor no .txt         | Confirmado no binário? |
|:----------------|:----------------------|:-----------------------|
| `sample_fps`    | 30 (int)              | ✓ uint32 @ [0:4]       |
| `loop`          | True/False (bool)     | ✓ uint8 @ [4]          |
| `has_scaled`    | True/False            | ✓ uint8 @ [5]          |
| `prs_flags`     | 7                     | ✓ uint16 @ [6:8]       |
| `accum_flags`   | 0                     | ✓ uint32 @ [8:12]      |
| `pack_prs_flags`| 6 (parent) / 4 (child?)| parcial              |
| `key_count`     | var (16, 101, etc.)   | ✓ uint16 @ [14:16]     |

---

## 3. Bloco de Tracks — NÃO CONFIRMADO (Maior Pendência)

### 3.1 O Problema

Os primeiros bytes após a timeline **não são flags de canal**. São valores
float32 que parecem ser coordenadas 3D (posições de bones):

```
daomadan_spawn.gis, bytes após timeline:
a4 32 77 bf  → float ≈ -0.967
bf f1 13 41  → float ≈  9.247
c0 cb a4 c0  → float ≈ -5.150
...
```

Isto indica que existe um bloco de dados entre a **timeline** e a **lista de
tracks de animação** que ainda não foi identificado.

### 3.2 Hipótese Principal: Bone Transforms (Bind Pose)

O formato parent `.gis` (animation_format.txt) contém `bone_trans` com pos,
rot, scale de cada bone **antes** dos clips de animação. O formato child `.gis`
possivelmente também tem este bloco.

Se o bloco de bone_transforms existe no child format:

```
Tamanho hipotético:
  bone_count × (3 + 4 + 3) floats × 4 bytes = bone_count × 40 bytes

daomadan: 223 × 40 = 8.920 bytes de bone_transforms hipotéticos
```

**Verificação pendente:** pular `bone_count × 40` bytes após a timeline e
verificar se os bytes seguintes são flags de canal (0/1).

Alternativas a testar se 40 bytes/bone não fechar:
- 28 bytes/bone (apenas pos + rot, sem scale)
- 12 bytes/bone (apenas pos)
- Nenhum bloco (os floats são o início de um formato de track diferente)

### 3.3 Verificação pela Matemática do Arquivo

Para confirmar, a equação deve fechar:

```
file_size = header + bone_symbols + meta + timeline + [bone_trans?] + tracks + pivot

daomadan_spawn.gis:
  file_size        = 784.809 bytes
  header           = 98 bytes    (64 + 32 + 2)
  bone_symbols     = 7.136 bytes (223 × 32)
  meta             = 20 bytes
  timeline         = 888 bytes   (222 × 4)
  pivot            = 480 bytes
  ─────────────────────────────
  disponível para bone_trans + tracks = 776.187 bytes
```

Se existir bone_trans (223 × 40 = 8.920 bytes):
```
  disponível para tracks = 776.187 - 8.920 = 767.267 bytes
```

Estimativa para tracks (223 bones, ~pos+rot, pos_count=1, rot_count=222):
```
  por bone: 4 (flags) + 6 (3 counts) + 1×12 (pos) + 222×16 (rot) + 1×12 (scale)
           = 10 + 12 + 3.552 + 12 = 3.586 bytes
  total:   223 × 3.586 ≈ 799.678 bytes   ← maior que 767.267, não fecha ainda
```

A matemática não fecha completamente — estrutura exata das tracks ainda é incerta.

---

## 4. Erros Conhecidos no Parser Atual (`core/gis_parser.py`)

| # | Campo / Comportamento          | Código Errado                                | Impacto       |
|---|:-------------------------------|:---------------------------------------------|:--------------|
| 1 | fps hardcoded via campo errado  | `fps_raw = meta[2:4]` → sempre 0             | Médio         |
| 2 | loop hardcoded False            | `loop=False` (não lê meta[4])                | Alto          |
| 3 | Flags do track: 7 bytes         | `f.read(7)` como pares uint16                | Alto (crash)  |
| 4 | key_count global para todos     | `range(key_count)` em pos/rot/scale          | Alto (corrupt)|
| 5 | Peek heurístico para local counts| `if peek == key_count: f.read(4)`            | Anti-padrão   |
| 6 | has_scaled não lido             | meta[5] ignorado                             | Baixo         |

---

## 5. Plano de Investigação para a Próxima Sessão

**Prioridade 1 — Confirmar bone_transforms:**
```python
# Após a timeline, pular N bytes e verificar se são flags de canal
after_timeline_pos = timeline_pos + key_count * 4
# Testar: N = bone_count * 40 (pos12 + rot16 + scale12)
# Testar: N = bone_count * 28 (pos12 + rot16)
# Testar: N = 0 (sem bone_transforms)
# Verificar se os bytes em after_timeline_pos + N são [0/1, 0/1, 0/1, 0/1]
```

**Prioridade 2 — Confirmar estrutura de track via arquivo pequeno:**
Usar `tpose.gis` (bone_count=254, key_count=2, tamanho total pequeno) para
mapear manualmente os tracks byte a byte.

**Prioridade 3 — Confirmar se pack_prs_flags=4 indica variante:**
O animation_format.txt mostra `pack_prs_flags=6` no parent format e nossos
arquivos têm `pack_prs_flags=4`. Pode indicar variante de compressão de canal.

**Prioridade 4 — Mapear bloco Pivot (480 bytes):**
Identificar os campos do Root Motion block via arquivo com movimento de câmera/root.

---

## 6. Arquivos de Teste Disponíveis

Localização: `c:\Users\diesel\Desktop\CHParser\files_neox\`

Arquivos recomendados para próxima sessão (pequenos e representativos):
- `tpose.gis` — bone_count=254, key_count=2 (menor arquivo para análise manual)
- `gedou_spawn_idle.gis` — bone_count=223, key_count=81, loop=True
- `win.gis` — bone_count=220, key_count=101, loop=False, has_scaled=False
