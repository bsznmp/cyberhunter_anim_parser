---
description: Testes automatizados de falsificabilidade para suposições estruturais errôneas em arquivos binários (ex: desalinhamento de tipos int16 vs int32). Metodologia: Gestão de incerteza, separando hipóteses de fatos observados através de sanity checks matem
---

ESTRATÉGIA DE VALIDAÇÃO: FALSIDADE E EFEITO CASCATA
A persona atua como um orquestrador de investigação e sabe que suas suposições estruturais são apenas hipóteses iniciais
. Quando a IA "conclui" temporariamente que um campo tem 16-bits (2 bytes), mas o formato real utiliza 32-bits (4 bytes), ocorre o que chamamos de desalinhamento em cascata. Todo o resto do mapeamento (os 96 bytes supostos) ficará deslocado da memória real.
Para que a IA detecte que sua própria suposição está errada sem auxílio visual, ela programa Testes de Coerência de Dados e Consistência Estrutural
. Se a suposição falhar em qualquer um desses testes, a IA entra em rota de "Iteração" (Fase 7) e ajusta a hipótese
.
Os testes que a IA projeta para refutar suas próprias premissas são:
1. Teste de Fronteira e Alinhamento Global (EOF Match)
A IA sabe que não podem sobrar nem faltar bytes mágicos
.
A Lógica: Se um arquivo tem 10.000 bytes e a IA assume que o bloco de animação tem 100 frames de 96 bytes, o payload total seria de 9.600 bytes. Somado ao cabeçalho conhecido, a equação matemática deve equivaler ao tamanho exato do arquivo no disco.
O Gatilho de Falha: Se a IA errou e o campo era de 32-bits em vez de 16-bits, o tamanho real do frame (stride) seria maior que 96 bytes. Ao tentar varrer o arquivo com o passo errado, o script da IA ou terminará prematuramente (sobrando bytes não mapeados) ou tentará ler além do fim do arquivo (lançando um erro Out of Bounds). Ao capturar essa exceção estrutural, a IA refuta sua própria conclusão
.
2. Teste de Domínio e Limites (Sanity Checks)
A IA testa se os números extraídos fazem sentido lógico dentro do contexto computacional do artefato
.
Teste de Índices: Se a IA mapeou hierarquia de ossos usando 16-bits em vez de 32-bits, a leitura vai pegar metades de inteiros combinados com padding. Isso gerará um ID de osso absurdo, como 65280. O script da IA terá uma asserção programada: assert(ID_Bone_Pai < Total_de_Ossos). Se existem apenas 50 ossos no cabeçalho e o ID lido foi 65280, a hipótese estrutural da IA é imediatamente invalidada.
Teste de Floats (IEEE 754): Ler matrizes de posições XYZ com offsets errados faz com que os bytes lidos não formem pontos flutuantes válidos. A IA busca ativamente por NaN (Not a Number) ou coordenadas astronômicas (ex: eixo Y=3.4×10 
35
 ) aplicando testes lógicos de bounding box (-10000.0 < float_lido < 10000.0). A falha indica um erro anterior de alinhamento ou tamanho de variável
.
3. Automação de Parsing Estrito via Kaitai Struct
Em vez de depender de scripts artesanais frágeis, a estratégia principal de validação de esquemas da IA é usar o Kaitai Struct
.
A IA cria uma definição declarativa inicial, afirmando: bone_id: u2 (unsigned int de 16-bit).
Ao rodar a validação automatizada, o parser do Kaitai tentará validar blocos recursivamente.
Se os dados subsequentes (como Magic Bytes de início de frame) não aparecerem no byte exato projetado pela IA, o Kaitai lança uma falha apontando exatamente em qual offset a suposição quebrou. A IA analisa o log e corrige sua hipótese para u4 (32-bit).

--------------------------------------------------------------------------------
MATRIZ DE DEPURACÃO DE HIPÓTESES
Suposição Errada da IA
Efeito Físico na Memória
Teste Automatizado de Refutação
Mapear int16 onde é int32.
Desalinhamento de 2 bytes em cadeia. O próximo float perde seus 2 primeiros bytes e "rouba" 2 bytes do campo seguinte.
Teste de Entropia Numérica: Os valores lidos como floats repentinamente passam a dar resultados NaN ou Infinito
.
Supor Stride (tamanho do bloco) de 96 bytes (faltou prever 4 bytes de Padding).
A leitura do primeiro frame funciona, do segundo fica 4 bytes fora, do terceiro 8 bytes.
Teste de Continuidade: Verificação geométrica de anomalias cinemáticas extremas calculando o delta entre frames.
Supor Little-Endian em dados gravados como Big-Endian.
A quantidade de ossos no cabeçalho é lida ao contrário (ex: 01 00 00 00 se torna 16.777.216 em vez de 1).
Teste de Limiar de Memória: Tentar alocar tabelas imensas que estouram a RAM indica endianness incorreto
.