# Reverse Engineering Analysis Worksheet — NeoX .gis (Child/Raw)

### Seção 1 — Identificação do Arquivo
- **Nome do formato:** NeoX GIS Animation (Child Variant)
- **Extensão(ões):** [.gis](file:///c:/Users/diesel/Desktop/CHParser/files_neox/win.gis)
- **Tamanho típico:** 10KB ([tpose.gis](file:///c:/Users/diesel/Desktop/CHParser/files_neox/tpose.gis)) a 800KB ([daomadan_spawn.gis](file:///c:/Users/diesel/Desktop/CHParser/files_neox/daomadan_spawn.gis))
- **Assinatura mágica:** Nenhuma (Formato Raw/Child). Identificado pelo Bone Name Header (64 bytes).
- **Versão do formato:** NeoX V2+ (indicado pelo KeyCount no offset 14 do contexto global).
- **Endianness:** [x] Little  [ ] Big  [ ] Misto
- **Plataforma alvo:** PC / Android (NeoX Engine)

### Seção 2 — Estrutura Geral
- **Arquitetura:** [x] Offsets fixos  [ ] Chunks  [ ] OO/grafo
- **Entropia média:** 0.4 (Headers) a 0.75 (Dense Animation Data).
- **Compressão detectada:** [ ] Nenhuma  [ ] Zlib  [ ] LZ4  [x] Delta/Quantized (indicado por `pack_prs_flags=4`)
- **Seções identificadas:**
  - [0x00] [64] Header: ASCII Magic (Character Name)
  - [0x40] [32] Padding: Geralmente nulo.
  - [0x60] [2] Bone Count (uint16)
  - [0x62] [bone_count * 32] Bone Symbols (ASCII + 0x10 uint16 Meta opcional)
  - [Var] [20 ou 24] Global Context Block (Metadata) - Offset depende de alinhamento / Blocos Extras.
    - **Variante Standard:** FPS (0), PRS (6), KeyCount (16).
    - **Variante Extended (Shift):** FPS (4), PRS (10), KeyCount (18). Sinalizado por prs_flags > 0xFF.
  - [Var] [key_count * 4] Timeline (Timestamps em ms - uint32 ou float32)
  - [Var] [bone_count * 36] Bind Pose / Root Pose Block
  - [Var] [Variável] Animation Tracks (PRS Channels)
  - [EOF - 480] [480] Pivot Block

### Seção 3 — Esqueleto
- **Quantidade de ossos:** Variável (ex: 254 em [tpose.gis](file:///c:/Users/diesel/Desktop/CHParser/files_neox/tpose.gis), 223 em `daomadan`)
- **Formatos de hierarquia:** [x] Lista plana (referenciada por símbolos)
- **Formato de matriz:** [x] TRS separado
- **Alinhamento:** 4 bytes para floats; 2 bytes para half-floats.
- **Strings de nomes:** [x] Presentes em blocos de 32 bytes (null-terminated).
- **Quantização (Bind Pose):** Posição/Rotação em Float32; Escala em Float16 (Half-Float).

### Seção 4 — Animação
- **Duração total:** `key_count` frames.
- **Framerate:** Armazenado como uint32 no Context Block (comumente 30).
- **Representação de tempo:** [x] Float abs (ms)
- **Organização:** [x] Por canal (track) após o bloco de Bind Pose.
- **Canais presentes:** [x] Posição  [x] Rotação  [x] Escala
- **Compressão de canal:** [x] Nenhuma (float32)  [ ] int16 quantizado
- **Canais constantes:** [x] Omitidos (fallback do Bind Pose se o flag de trilha for 0).

### Seção 5 — Eventos e Strings
- **Posição da tabela:** Início do arquivo (Bone Symbols).
- **Codificação:** [x] ASCII
- **Formato:** [x] Null-terminated (padding até 32/64 bytes).
- **Referência por:** [x] Índice implícito na ordem dos ossos.

### Seção 6 — Observações Técnicas Atualizadas
- **Variabilidade Determinística:** O shift de metadados não é aleatório; ele ocorre quando o cabeçalho inclui campos de suporte a rigs estendidos (identificados por bits altos no `prs_flags`).
- **Timeline de Milliseconds:** Algumas animações (`daomadan`) usam `uint32` para milissegundos absolutos, enquanto outras usam `float32`. O parser deve testar a taxa de incremento para diferenciar.
- **Bone Symbols Híbridos:** A tabela de símbolos de 32 bytes pode conter metadados embutidos após o terminador nulo do nome (ex: `KeyCount` local no offset 16).
- **Consolidação Blender:** O uso de `bake_anim_use_all_actions` no exportador é vital para capturar todas as layers de animação convertidas a partir de arquivos GIS individuais.
