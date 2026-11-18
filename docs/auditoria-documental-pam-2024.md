# Auditoria documental da PAM — 2024 (16/11/2026)

## Achado decisivo: a Base dos Dados perde distinções dos símbolos originais
O catálogo da Base dos Dados informa expressamente que **'...', '..' e '-' são
convertidos em NULL** nas tabelas PAM. No IBGE, esses símbolos têm significados
diferentes: '-' é zero absoluto; '..' não se aplica; '...' não disponível.
O IBGE também usa 'X' para valores inibidos por sigilo e '0' para zero por
arredondamento. Não foi possível estabelecer pelo catálogo consultado o
tratamento completo de 'X' na transformação da Base dos Dados.

Consequência: a observação NULL na Base dos Dados **não permite recuperar**
qual símbolo original a gerou. É incorreto tratá-la como zero ou como
desconhecida com significado uniforme. Para publicação, recuperar símbolos
originais por fonte oficial ou manter uma classificação de ausência
indeterminada e indicadores explicitamente parciais.

## Evidências empíricas — consultas no BigQuery do projeto atlas-agro-pol
PAM 2024, permanentes + temporárias:
- 394.137 registros, 5.563 municípios, 71 produtos;
- 61.040 valores monetários presentes, 333.097 NULL (84,51%);
- permanentes: 210.558 registros, 185.250 NULL (87,98%);
- temporárias: 183.579 registros, 147.847 NULL (80,54%);
- três registros com valor monetário NULL e produção física positiva:
  2927200, cana-de-açúcar (área 2 ha, quantidade 4);
  3509007, cana-de-açúcar (área 1 ha, quantidade 2);
  4300604, sorgo em grão (área 2 ha, quantidade 1).
Os dados acima foram fornecidos pelo pesquisador, não reexecutados pelo pipeline.

## Validação oficial disponível
O IBGE Explica publica série de valor de produção por produto, inclusive
2024, e alerta que somas municipais podem divergir de totais estaduais devido
a sigilo estatístico. Usar como *benchmark por produto*; não presumir que
soma municipal sempre iguala total nacional oficial.

Exemplo verificável: soja, Brasil, valor da produção 2024:
260.233.510 **mil reais** (IBGE Explica; consultar a página e verificar a
revisão/data antes de comparação).

## Critérios de liberação
1. Documentar códigos de ausência originais e sua transformação;
2. Confirmar se a fonte inclui registros sigilosos e como foram tratados;
3. Conferir produtos, unidades, séries e códigos territoriais;
4. Comparar 2024 por produto/UF/Brasil com benchmarks oficiais, registrando
   diferenças esperadas por sigilo e arredondamento;
5. Não publicar soma de valores observados como total oficial enquanto não
   houver reconciliação; rotular como soma observada, se utilizada.

## Referências
- https://basedosdados.org/dataset/fc403b40-a7e1-40e7-9efe-910847b45a69
- https://www.ibge.gov.br/explica/producao-agropecuaria/soja/br
- https://www.ibge.gov.br/biblioteca/visualizacao/periodicos/66/pam_2015_v42_br.pdf
