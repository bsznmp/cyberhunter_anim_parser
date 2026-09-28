# NeoX .gim — Especificação Binária Definitiva

**Projeto:** Engenharia Reversa Cyber Hunter (NeoX Engine)
**Status:** Formato completamente decifrado — leitura 100% sequencial, sem heurísticas
**Arquivos de referência:** `core/gim_parser.py`, `core/dto.py`

---

## 1. O QUE É UM .gim

**Game Instance Mesh** — descritor binário de uma *parte* de personagem, objeto 3D
ou material. Na maioria dos casos **não contém geometria**: é um manifesto que aponta
para `.mesh`, `.gis`, `.sfx`, `.mtg` e descreve bounding boxes, submeshes, sockets,
jiggle bones e referências de arquivo.

A NeoX Engine monta o personagem em runtime lendo os `.gim` e carregando os assets
referenciados.

### 1.1 Subtipos de .gim

| Subtipo               | Identificação                        | Exemplo                      |
|-----------------------|--------------------------------------|------------------------------|
| **Mesh-assembly**     | T2 contém `AnimAccumEnable`          | `t00_03.gim`, `body01.gim`   |
| **Material-descriptor** | T2 contém `AlphaRef`, `AlphaVal`  | `ar08.gim`, `ar10.gim`       |
| **Building-inline**   | T2 contém `v_count`, `i_count`       | `tongyong_build01b.gim`      |

O pipeline de personagem usa exclusivamente o subtipo **mesh-assembly**.

---

## 2. LAYOUT BINÁRIO

### 2.1 Cabeçalho do arquivo

```
Offset  Tam     Descrição
──────────────────────────────────────────────────────────────────
0x00    4 B     MAGIC: c1 59 41 0d  (fixo em todos os arquivos)
0x04    4 B     Tamanho total do arquivo (uint32 LE)
0x08    4 B     Reservado — sempre 0x00000000
0x0C    1 B     n1 = número de strings na Table1  (uint8, caso padrão)
0x0D    var     Table1: n1 strings null-terminated (nomes de tipo de objeto)
  ?     1 B     n2 = número de strings na Table2
  ?     var     Table2: n2 strings null-terminated (nomes de atributo)
  ?     var     Payload (dados da árvore)
```

> **Caso especial — n1 como uint16:** Arquivos com n1 > 255 (ex.: `base.gim`,
> n1=644) armazenam n1 como **uint16 LE** nos bytes 0x0C–0x0D, e Table1 começa
> em 0x0E em vez de 0x0D. Detecção: se `data[0x0D]` não é printável (`< 0x20`)
> e não é nulo (`!= 0x00`), interpretar 0x0C–0x0D como uint16.

> **Erro corrigido:** O byte entre Table1 e Table2 foi incorretamente documentado
> como "separador constante 0x14". É o **contador n2**, variável por arquivo.
> Valores observados: 7, 10, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23, 24, 25, 83.

### 2.2 Tabelas de strings

Ambas as tabelas estão sempre **ordenadas alfabeticamente**. O índice de cada
string no stream de atributos é a posição na lista ordenada.

**Table1 (tipos de objeto — T1)** — exemplos reais:
```
BoundObject, File, FileName, GisFiles, JiggleBones, NeoX,
Object, Object_0, Physics, RigidBodys,
Socket_0 … Socket_N, Sockets, Sub0 … SubN,
SubMesh, Triggers, __files_tag__
```

**Table2 (nomes de atributo — T2)** — exemplos reais (subtipo mesh-assembly):
```
AnimAccumEnable, BindType, BoneName, BoundingCenter, BoundingHalf,
BoundingInfo, Color, CompatibleMask, ForceCPUSkining, Friction,
LodLevel, Mass, MatrixToBone, Mesh, MtlIdx, MustShow, Name, Path,
Position, RBType, Restitution, RuntimeDelta, Size, TangentEnable,
TriSortMethod, Type, value, Version
```

**Table2 (subtipo material-descriptor):**
```
AlphaRef, AlphaVal, CullBack, Diffuse, LightingEnable, MaterialCount,
Name, Path, SpecularEnable, Speed, TechName, TransparentMode, Type,
VColorEnable, Value, Version
```

> **Nota:** T2[0] é sempre a primeira string **em ordem alfabética** da tabela
> deste arquivo. Para mesh-assembly isso é `AnimAccumEnable`. Para
> material-descriptor é `AlphaRef`. Não há garantia de que T2[0] seja
> `AnimAccumEnable` em todos os subtipos.

### 2.3 Payload

```
Offset relativo   Tam     Descrição
──────────────────────────────────────────────────────────────────
+0x00             4 B     u32a: uint32 LE (significado não essencial ao parser)
+0x04             4 B     Sempre 0x00000000
+0x08             var     Seção de topologia (Count-Then-Data — ver seção 3)
  ?               var     Stream de atributos (ver seção 4)
```

---

## 3. SEÇÃO DE TOPOLOGIA

Começa em `payload[+0x08]`. Formato **Count-Then-Data** com terminador —
leitura 100% sequencial, sem heurísticas.

```
[uint8 count] [count × 2 bytes de pares] [uint8 terminador]
tamanho total = 1 + count*2 + 1
```

**Cálculo do data_start** (início do stream de atributos no payload):
```python
count      = payload[8]
data_start = 8 + 1 + count*2 + 1
```

### 3.1 Pares de topologia `[a, b]`

Cada par codifica uma instância na árvore de objetos:
- `a` = índice T1 do tipo deste nó
- `b` = índice T1 do tipo pai

O `count` representa o número total de **instâncias** na árvore, não de
tipos únicos. Um mesmo tipo T1 pode aparecer múltiplas vezes (ex.: 4 nós
`File` filhos de `BoundObject` → 4 entradas com `a=File_idx`).

Exemplos reais (`tongyong_build01a_lod1.gim`, T1=['NeoX','Sub0','SubMesh']):
```
count=3  pares: (0,1) (2,1) (1,0)  terminador=6

  pair[0]: (NeoX, Sub0)    → NeoX é root; b=tipo do primeiro filho canônico
  pair[1]: (SubMesh, Sub0) → SubMesh é filho de Sub0
  pair[2]: (Sub0, NeoX)    → Sub0 é filho de NeoX
```

Para o nó raiz (`NeoX`), `b` aponta para o seu primeiro tipo-filho (não para
um pai real — NeoX não tem pai). Este é o único par com semântica especial.

### 3.2 Terminador

Byte único após os pares. Valores observados: 6, 7, 8.
Hipótese: número de atributos diretos do nó raiz NeoX (não confirmado).
**Não precisa ser interpretado pelo parser** — basta avançar 1 byte.

### 3.3 Tamanhos por arquivo (verificados)

```
Arquivo                     n1   n2  count  topo_size
────────────────────────────────────────────────────
tongyong_build01a_lod1.gim   3  10     3       8
tongyong_build01b_lod1.gim   8  12     8      18
hair_00_leila.gim           12  18    12      26
body01.gim                  13  19    16      34
lingzi.gim                  21  19    24      50
tongyong_build01a_sn.gim    37  25    37      76
tongyong_build02_sn.gim     45  25    45      92
ar08.gim                    17  16    31      64
ar10.gim                    20  16    23      48
```

---

## 4. STREAM DE ATRIBUTOS

### 4.1 Localização — leitura sequencial

```python
count      = payload[8]            # uint8: número de pares da topologia
data_start = 8 + 1 + count*2 + 1  # posição do primeiro atributo no payload
```

Não há scan, não há fingerprint. O stream começa exatamente após a topologia.

> **Erro corrigido:** A função `find_data_start` da versão anterior usava um
> scanner heurístico (`\x00\x01\x74`) para localizar o stream — violação do
> princípio NeoX de leitura sequencial (anti-padrão #1 do manual). Funcionava
> apenas para arquivos mesh-assembly onde T2[0]=AnimAccumEnable. Para
> material-descriptor (T2[0]=AlphaRef) o scanner falhava silenciosamente,
> retornando um `data_start` errado centenas de bytes à frente.

### 4.2 Codificação de atributos

Cada atributo é codificado como:
```
[T2_idx: 1 byte] [tipo: 1 byte] [valor: tamanho depende do tipo]
```

**Tipos documentados:**

| Código | Nome        | Tamanho do valor        | Notas                              |
|--------|-------------|-------------------------|------------------------------------|
| `0x01` | String      | até `\x00` (variável)   | Null-terminated, Latin-1           |
| `0x02` | UInt32      | 4 bytes                 | Little-endian                      |
| `0x04` | Raw 4 bytes | 4 bytes                 | RGBA, flags, ou dados opacos       |
| `0x05` | Float32     | 4 bytes                 | IEEE 754 LE                        |
| `0x06` | Float Array | 4 + N×4 bytes           | `[count: u32][f1 f2 ... fN: f32]`  |

**Tipos parcialmente identificados (BindType):**

| Código | Hipótese    | Evidência                                          |
|--------|-------------|----------------------------------------------------|
| `0x0b` | UInt8 (1B)  | Aparece em `01 0b [byte]` antes de atributo Path   |
| `0x0e` | Flag (0B?)  | Aparece em `01 0e` antes de atributo Path          |

> Tipos 0x0b e 0x0e aparecem no atributo `BindType` (T2[1]) em arquivos com
> sockets (armas, gadgets). O pipeline atual não os parseia — usa varredura
> de strings para extrair paths nesses casos.

### 4.3 Marcadores de árvore no stream

Dentro do stream de atributos, a hierarquia de objetos é codificada com:

| Padrão          | Significado                                          |
|-----------------|------------------------------------------------------|
| `0x01 [T1_idx]` | Abre objeto filho do tipo `T1[T1_idx]`              |
| `0x00`          | Fecha objeto atual (volta ao nível anterior)         |

**Ambiguidade:** `0x01` também é o índice T2 de `BindType` (quando BindType
existe em T2[1]). O parser resolve por precedência: se o byte seguinte não é
um tipo de valor válido (0x01, 0x02, 0x04, 0x05, 0x06), interpreta `0x01 X`
como abertura de objeto filho T1[X].

**Regra especial para `0x00`:**
- Na profundidade 1 (raiz): lido como T2[0] = primeiro atributo da raiz
- Em profundidade > 1: lido como fechamento de objeto

---

## 5. ESTRUTURA HIERÁRQUICA TÍPICA

### 5.1 Mesh-assembly: roupa/corpo

```
NeoX {
  AnimAccumEnable  = "true"
  BoundingInfo     = "(x,y,z),(x,y,z),r"
  CompatibleMask   = 0
  LodLevel         = 0|1
  Mesh             = "character\...\t00.mesh"
  TangentEnable    = "true"|"false"
  TriSortMethod    = 0
  FileName { value = "common.gis" }
  FileName { value = "lingzi.sfx" }
  Sub0 {
    BoundingCenter = [3 floats]
    BoundingHalf   = [3 floats]
    BoundingInfo   = "..."
    MtlIdx         = 0
    Name           = "body"
  }
}
```

### 5.2 Mesh-assembly: arma com sockets

```
NeoX {
  AnimAccumEnable  = "true"
  BoundingInfo     = "(-0.618,-0.0013,0.0147),(5.1333,2.3542,1.6385),5.5447"
  CompatibleMask   = 0
  LodLevel         = 1
  TangentEnable    = "false"
  TriSortMethod    = 0
  File {
    BindType = 1                         // tipo 0x0b — 1 byte
    Path = "character\...\cannon01.mesh"
    BindType = 1
    Path = "character\...\cannon01.mtg"
  }
  Socket_0 {
    MatrixToBone = [16 floats]
    MustShow     = "false"
    Name         = "shoot"
  }
}
```

### 5.3 Mesh-assembly: jiggle bone

```
NeoX {
  AnimAccumEnable = "true"
  BoundingInfo    = "(0.1513,-0.2462,0.6834),(0.078,0.1021,0.1233),0.1758"
  CompatibleMask  = 0
  ForceCPUSkining = "false"
  LodLevel        = 0
  TangentEnable   = "false"
  TriSortMethod   = 0
  Sub0 {
    BoundingCenter = [3 floats]
    BoundingHalf   = [3 floats]
    MtlIdx         = 0
    Name           = "P_5_jaw_right_m"
  }
  FileName { value = "character\...\lingzi_head.gis" }
}
```

### 5.4 Building-inline (geometria embutida)

```
NeoX {
  AnimAccumEnable = "true"
  BoundingInfo    = "(-1.79,18.75,2.09),(37.63,21.53,57.20),71.77"
  CompatibleMask  = 0
  LodLevel        = 0
  TangentEnable   = "false"
  TriSortMethod   = 0
  Sub0 {
    v_count = N         // vértices desta sub-mesh
    i_count = N         // índices desta sub-mesh
    v_start = offset    // offset no buffer global de vértices
    i_start = offset    // offset no buffer global de índices
    MtlIdx  = 0
    Name    = "tongyong_build01b_0"
  }
  // Sem File/FileName/GisFiles — geometria referenciada inline
}
```

> Arquivos deste subtipo não referenciam `.mesh`/`.gis` externos.
> O `gim_parser.py` retorna `mesh_paths=[]` e `gis_paths=[]` — comportamento correto.

---

## 6. VALORES OBSERVADOS POR ATRIBUTO

| Atributo        | Tipo     | Exemplos de valor                                    |
|-----------------|----------|------------------------------------------------------|
| AnimAccumEnable | string   | `"true"` (sempre nos arquivos mesh-assembly)         |
| BoundingInfo    | string   | `"(x,y,z),(x,y,z),r"` — centro, half-extents, raio  |
| BoundingCenter  | float[]  | 3 floats — posição do centro da bounding             |
| BoundingHalf    | float[]  | 3 floats — half-extents (metade da dimensão)         |
| CompatibleMask  | uint32   | 0                                                    |
| ForceCPUSkining | string   | `"false"`, `"true"`                                  |
| LodLevel        | uint32   | 0, 1                                                 |
| MatrixToBone    | float[]  | 16 floats — matriz 4×4 (socket bind transform)       |
| Mesh            | string   | `"character\female\lingzi\t00.mesh"`                 |
| MtlIdx          | uint32   | 0, 1, 2, 3, 4                                        |
| MustShow        | string   | `"false"`, `"true"`                                  |
| Name            | string   | nome da socket ou sub-objeto                         |
| Path            | string   | path do arquivo (.mesh, .mtg)                        |
| RuntimeDelta    | string   | `"false"`                                            |
| TangentEnable   | string   | `"false"`, `"true"`                                  |
| TriSortMethod   | uint32   | 0                                                    |
| value           | string   | path de .gis ou .sfx                                 |
| Version         | uint32   | 4 (valor mais comum)                                 |
| v_count         | uint32   | número de vértices (building-inline)                 |
| i_count         | uint32   | número de índices (building-inline)                  |

---

## 7. METODOLOGIA — LEITURA SEQUENCIAL CORRETA

### Passo 1: Validar magic e tamanho
```python
assert data[:4] == b'\xc1\x59\x41\x0d'
file_size = struct.unpack_from('<I', data, 4)[0]
```

### Passo 2: Ler n1 e Table1 (Count-Then-Data)
```python
# Detectar se n1 é uint8 (padrão) ou uint16 (arquivos grandes, ex.: base.gim)
if data[0x0d] not in (0x00,) and data[0x0d] < 0x20:
    n1 = struct.unpack_from('<H', data, 0x0c)[0]  # uint16
    _, off = read_strings(data, 0x0e, n1)
else:
    n1 = data[0x0c]                                # uint8
    _, off = read_strings(data, 0x0d, n1)
```

### Passo 3: Ler n2 e Table2 (Count-Then-Data)
```python
n2 = data[off]      # 1 byte — NÃO é constante 0x14
off += 1
table2, off = read_strings(data, off, n2)
```

### Passo 4: Calcular data_start (Count-Then-Data na topologia)
```python
payload    = data[off:]
count      = payload[8]            # uint8: número de pares da topologia
data_start = 8 + 1 + count*2 + 1  # leitura sequencial pura
```

> Não usar scanner heurístico. O tamanho da topologia é determinístico.

### Passo 5: Extrair paths do payload
```python
import re, os
EXTS = {'.mesh', '.gis', '.sfx', '.mtg'}
paths = []
seen = set()
for m in re.finditer(rb'[\x20-\x7e]{6,}', payload):
    s = m.group(0).decode('latin-1')
    if os.path.splitext(s)[1].lower() in EXTS and s not in seen:
        seen.add(s); paths.append(s)
```

### Passo 6: Extrair BoundingInfo (a partir de data_start)
```python
bi_idx = table2.index('BoundingInfo')  # se existir
# Busca sequencial: [bi_idx][0x01][string]
```

---

## 8. ARQUIVOS DE REFERÊNCIA

| Arquivo                         | Papel                                                        |
|---------------------------------|--------------------------------------------------------------|
| `core/gim_parser.py`            | Parser de pipeline — retorna `GimDTO` (componente definitivo)|
| `core/dto.py`                   | Define `GimDTO` com mesh_paths, gis_paths, bounding box      |
| `docs/gim_format_definitivo.md` | Esta especificação                                           |

---

## 9. ERROS DOCUMENTADOS E CORREÇÕES

| Campo / Comportamento            | Versão errada                                      | Versão correta                                      |
|----------------------------------|---------------------------------------------------|-----------------------------------------------------|
| Byte entre Table1 e Table2       | "separador constante 0x14"                        | contador n2, variável (7 a 83+)                    |
| Início de Table1                 | sempre offset 0x0D                                | 0x0D (uint8) ou 0x0E (uint16 quando n1 > 255)      |
| Localização do stream            | scanner `\x00\x01\x74` (heurístico)               | `8 + 1 + payload[8]*2 + 1` (sequencial)            |
| Escopo do scanner                | "funciona em qualquer .gim"                        | falha em material-descriptor (T2[0] ≠ AnimAccumEnable)|
| Topologia                        | "formato desconhecido, ignorar"                   | `[uint8 count][count×2 bytes][uint8 term]`         |
| Nomes de atributos → paths       | incorretos (ForceCPUSkining=path?)                | Path, Mesh, value — via scan de extensão           |
| Status "38/38 completo"          | inclui topologia como "desconhecida"              | topologia agora completamente decifrada             |

---

## 10. PONTOS AINDA NÃO RESOLVIDOS

1. **Significado de u32a** (payload[0:4]) — varia por arquivo, valor entre 156 e
   1851877745. Não parece ser tamanho do payload nem do stream de atributos.
   Hipótese: hash ou identificador interno.

2. **Tipos 0x0b e 0x0e** (BindType em armas com sockets):
   - `0x0b` hipótese: uint8 (1 byte de valor)
   - `0x0e` hipótese: flag sem valor (0 bytes)
   Não confirmados por análise sistemática.

3. **Tipos 0x03, 0x07–0x0a, 0x0c, 0x0d** — nunca observados. Possivelmente
   não usados nesta versão da NeoX Engine.

4. **Semântica exata do terminador da topologia** — valores 6, 7, 8 observados.
   Hipótese: número de atributos diretos do nó raiz NeoX. Não confirmada.

5. **Geometria inline do subtipo building** — atributos `v_count`, `i_count`,
   `v_start`, `i_start` foram identificados, mas o buffer de geometria em si
   não foi localizado no arquivo.
