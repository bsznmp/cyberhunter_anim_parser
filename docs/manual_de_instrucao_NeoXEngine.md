# Manual de Instrução: Engenharia Reversa de Formatos Binários NeoX
**Baseado em erros reais e lições aprendidas do projeto CHParser (2026)**

---

## Filosofia Central

> **A engine NeoX serializa dados de forma 100% linear e sequencial.**
> Nunca há tabelas de offset. Nunca há ponteiros. Você lê byte a byte, do início ao fim.
> Se você perdeu um byte, perdeu todo o resto.

---

## Fase 0: Reconhecimento Inicial (Sem Tocar no Código)

### 0.1 Identifique o Magic Number
```
Offset 0x00: Leia os primeiros 4-8 bytes.
.mesh → 0xBBC88034 (4 bytes) + 4 bytes desconhecidos
.gis  → "anim" (4 bytes ASCII) + 4 bytes de versão
```
**Regra**: Todo formato NeoX começa com um identificador fixo de 4-8 bytes.

### 0.2 Busque Strings ASCII
```
Rode um scanner de strings no binário inteiro.
Procure por: "biped", "root", "bip001", "bone", "ik_hand"
```
- Se encontrar strings legíveis → **não há criptografia** no arquivo.
- Se NÃO encontrar → pode haver compressão (ZLIB/LZ4) ou obfuscação.
- **Erro nosso**: Suspeitamos de criptografia quando as strings estavam lá em texto puro.

### 0.3 Compare com Referências Conhecidas
Antes de inventar qualquer teoria:
1. Procure parsers existentes (GitHub, XeNTaX, ZenHAX, Loverslab).
2. Leia o código funcional linha por linha.

---

## Fase 1: Leitura Sequencial do Header

### 1.1 Padrão NeoX: Count-Then-Data
```
[uint32 count] → [array de count itens]
```
Esse padrão se repete em TODO lugar:
- Contagem de ossos → array de ossos
- Contagem de vértices → array de vértices
- Contagem de keyframes → array de keyframes

### 1.2 Padrão NeoX: Flag-Then-Optional-Block
```
[uint8/uint16 flag] → se != 0: [bloco de dados]
```
Exemplos reais:
- `bone_extra_info (uint8)` → se 1: lê `bone_count × 28` bytes
- `tangent_flag (uint16)` → se != 0: lê `vertex_count × 12` bytes
- `has_pos_keys (bool)` → se True: lê array de posições

### 1.3 Padrão NeoX: Sentinel de Fim de Seção
```
[uint16 flag] → se == 1: PARE (fim da seção variável)
```
Usado para sub-meshes: o parser lê sub-meshes em loop até encontrar `flag == 1`.

---

## Fase 2: Esqueleto (.mesh com ossos)

### Ordem Real dos Dados (Confirmada pelo converter.py)
```
1. [uint32]  bone_exist (0 = sem ossos, 1 = com ossos, >1 = versão especial)
2. SE bone_exist > 1:
     [uint8]  count extra
     [2 bytes] skip
     [count × 4 bytes] skip
3. [uint16]  bone_count
4. [bone_count × uint8]  parent_indices (0xFF = root, sem pai)
5. [bone_count × 32 bytes]  bone_names (null-padded ASCII)
6. [uint8]  bone_extra_flag
7. SE bone_extra_flag != 0:
     [bone_count × 28 bytes]  dados extras (pular)
8. [bone_count × 64 bytes]  bind_pose_matrices (4×4 float32)
9. SE múltiplos roots (-1 em parent_indices):
     Criar dummy_root virtual e reparar hierarquia
10. [uint8]  flag final (deve ser 0x00)
```

> [!CAUTION]
> **Erro Clássico Nosso**: Documentamos que os nomes vinham ANTES dos parent indices.
> A verdade é o CONTRÁRIO: parent indices PRIMEIRO, nomes DEPOIS.

---

## Fase 3: Geometria (.mesh)

### 3.1 Sub-Mesh Header Loop
```
[uint32] _offset (descartado)
LOOP:
    [uint16] flag → se == 1: BREAK
    seek(-2)  ← rewind do uint16 que não era sentinel
    [uint32] mesh_vertex_count
    [uint32] mesh_face_count
    [uint8]  uv_layers
    [uint8]  color_len
    → salvar (mesh_vertex_count, mesh_face_count, uv_layers, color_len)
FIM LOOP
```

### 3.2 Buffers Globais (NÃO por submesh)
```
[uint32] vertex_count_total (soma de todos os mesh_vertex_count)
[uint32] face_count_total (soma de todos os mesh_face_count)
```

### 3.3 Ordem dos Buffers de Dados
```
BUFFER 1: Posições      → vertex_count × 12 bytes (3 × float32: x, y, z)
BUFFER 2: Normais       → vertex_count × 12 bytes (3 × float32: nx, ny, nz)
BUFFER 3: Tangentes?    → [uint16 flag] → se != 0: vertex_count × 12 bytes
BUFFER 4: Faces         → face_count × 6 bytes (3 × uint16: v1, v2, v3)
BUFFER 5: UVs           → PER-SUBMESH (ver abaixo)
BUFFER 6: Vertex Colors → PER-SUBMESH (ver abaixo)
BUFFER 7: Skin Weights  → SE bone_exist (ver abaixo)
```

> [!IMPORTANT]
> **As Faces vêm ANTES das UVs.** Nós erramos catastroficamente ao assumir que
> vinham depois. O converter.py prova: Pos → Norm → (Tangent?) → **Faces** → UVs.

### 3.4 UVs (Per-Submesh)
```
PARA CADA submesh em model['mesh']:
    SE uv_layers > 0:
        [mesh_vertex_count × 8 bytes]  (2 × float32: u, v)
        [mesh_vertex_count × 8 × (uv_layers - 1)]  camadas extras (pular)
    SENÃO:
        UVs = (0.0, 0.0) para cada vértice
```

### 3.5 Vertex Colors (Per-Submesh)
```
PARA CADA submesh em model['mesh']:
    [mesh_vertex_count × 4 × color_len]  (pular/ler conforme necessidade)
```

### 3.6 Skin Weights
```
SE bone_exist:
    [vertex_count × 4 bytes]   bone_indices (4 × uint8, 0xFF = sem influência)
    [vertex_count × 16 bytes]  bone_weights (4 × float32)
```

---

## Fase 4: Coordenadas e Exportação

### 4.1 Transformação de Eixos
```
Para OBJ:  v(-x, y, z)     vn(-x, y, z)     vt(u, 1-v)
Para PMX:  v(-x, y, -z)    vn(-nx, ny, -nz)  vt(u, v)
Para FBX:  Depende do importador (Blender assume Z-Up)
```
**Regra**: Apenas o X é SEMPRE negado. A troca Y↔Z é **específica do exportador**, não do formato.

### 4.2 Triangle Lists (NÃO Strip)
```
Cada face = 3 × uint16 (v1, v2, v3)
Sem deobfuscação. Sem bitwise NOT. Sem zig-zag.
Índices são 0-based e diretos.
```

### 4.3 FBX PolygonVertexIndex
```
Para cada triângulo (a, b, c):
    Escrever: a, b, ~c    (onde ~c = -(c+1), marca fim do polígono)
```

---

## Anti-Padrões: O Que NUNCA Fazer

| # | Anti-Padrão | Por Que Falha |
|---|---|---|
| 1 | **Scanner heurístico** para "adivinhar" offsets | O formato é linear. Se você precisa adivinhar, perdeu bytes antes. |
| 2 | **Pular para offsets absolutos** | Não existem tabelas de offset. Leia sequencialmente. |
| 3 | **Assumir stride interleaved** | Os buffers são separados (Pos, Norm, UV), não intercalados. |
| 4 | **Procurar "Chunks" independentes** | Sub-meshes compartilham buffers globais. Não são chunks isolados. |
| 5 | **Aplicar XOR/NOT nos face indices** | Faces são texto puro (uint16 direto). A obfuscação XOR existe apenas nos bone transforms. |
| 6 | **Ler do fim para o início** | O formato é 100% forward-only. Nunca precisa de seek reverso. |
| 7 | **Confiar em documentação de RE** | Confie APENAS em código que compila e roda. Docs de RE têm alta taxa de erro. |

---

## Checklist para Arquivo Novo Desconhecido

```
[ ] 1. Ler magic (4-8 bytes) e comparar com formatos conhecidos
[ ] 2. Rodar strings para verificar se há criptografia
[ ] 3. Procurar parsers existentes no GitHub/XeNTaX
[ ] 4. Se encontrar parser: LER O CÓDIGO, não a documentação
[ ] 5. Escrever parser sequencial byte-a-byte
[ ] 6. Validar cada campo lido (count < 100000, floats entre -1000 e 1000)
[ ] 7. Nunca pular bytes sem justificativa provada
[ ] 8. Se algo não bate: VOLTAR e verificar se perdeu 1 byte antes
[ ] 9. Exportar OBJ primeiro (mais simples de validar visualmente)
[ ] 10. Só depois de OBJ OK, partir para FBX/PMX
```

---

## Referências Confiáveis

| Recurso | Caminho | Confiabilidade |
|---|---|---|
| `converter.py` | `ref/converter.py` | ⭐⭐⭐⭐⭐ Código funcional |
| `CyberConv_analysis.md` | `ref/CyberConv_analysis.md` | ⭐⭐⭐ Bom para conceitos, impreciso na ordem |
| `animation_format.txt` | `ref/animation_format.txt` | ⭐⭐⭐⭐ Estrutura oficial da NetEase |
| `Background Knowledge of Bone.md` | `ref/minhas_pesquisas/` | ⭐⭐⭐ Conceitos gerais úteis |
| Nossas docs gemini_analysis | `docs/gemini_analysis/` | ⭐⭐ Esqueleto OK, geometria errada |
