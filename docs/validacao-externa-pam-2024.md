# Validação externa PAM 2024 — Base dos Dados versus IBGE

Comparação nacional em **mil reais**. Base dos Dados: resultados BigQuery fornecidos pelo pesquisador. IBGE: valores das séries históricas do IBGE Explica e painel de indicadores, consultados em 16/11/2026.

| Cultura | Soma municipal BD | Brasil IBGE | BD − IBGE | Diferença relativa |
|---|---:|---:|---:|---:|
| Soja (em grão) | 260.233.559 | 260.233.510 | 49 | 0.00002% |
| Cana-de-açúcar | 104.971.415 | 105.104.231 | -132.816 | -0.12637% |
| Milho (em grão) | 88.118.185 | 87.928.195 | 189.990 | 0.21607% |
| Café (em grão) Total | 69.205.996 | 69.125.789 | 80.207 | 0.11603% |
| Arroz (em casca) | 22.317.494 | 22.318.455 | -961 | -0.00431% |

**Nota:** a soma dos valores municipais da Base dos Dados não é necessariamente igual ao agregado nacional publicado pelo IBGE. O IBGE adverte que divergências podem decorrer de desidentificação para sigilo dos informantes. Essa hipótese é plausível, mas **não demonstrada** como causa exclusiva das diferenças acima. Outras possibilidades incluem revisões de dados, processamento e diferenças de cobertura. Não ajustar artificialmente os valores.

**Regra de publicação:** manter a coluna de soma observada da Base dos Dados separada dos benchmarks nacionais do IBGE. Não atribuir selo de equivalência municipal/estadual antes de validação por UF e investigação das maiores diferenças. Para café, excluir Arábica e Canephora do total quando incluída a categoria Café Total.

## Fontes oficiais
- https://www.ibge.gov.br/indicadores/estatisticas (soja, milho, cana, café)
- https://www.ibge.gov.br/explica/producao-agropecuaria/arroz/br (arroz)
- https://www.ibge.gov.br/explica/producao-agropecuaria/cafe/br (café)
- https://www.ibge.gov.br/explica/producao-agropecuaria/cana-de-acucar/br (cana)
