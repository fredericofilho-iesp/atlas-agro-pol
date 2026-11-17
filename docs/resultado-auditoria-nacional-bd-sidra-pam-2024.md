# Auditoria nacional BD × SIDRA — PAM 2024 (cinco culturas)

**Data:** 17/11/2026. **Entradas:** CSV BigQuery exportado pelo pesquisador (`docs/sql/pam_bd_municipios_nacional_2024.sql`), 27.793 registros; extração oficial SIDRA municipal do workflow [#44106483533](https://github.com/fredericofilho-iesp/atlas-agro-pol/actions/runs/44106483533), 27.820 registros. Junção externa pelas chaves ano, UF, município (IBGE 7 dígitos) e produto. Sem chaves duplicadas em nenhuma fonte.

## Resultado nacional

| Situação | Registros |
|---|---:|
| Concordância numérica exata | **13.779** |
| Divergência numérica | **53** |
| Ausência de valor em ambas | **13.960** |
| Valor BD presente / SIDRA ausente | **1** |
| Linha SIDRA sem linha BD | **27** |
| Linha BD sem linha SIDRA | **0** |
| **Universo de chaves** | **27.820** |

Há **13.832 pares com valores numéricos nas duas fontes**, dos quais **99,617% coincidem exatamente** (13.779/13.832). O índice não inclui as 13.960 ausências em ambas.

Soma das diferenças absolutas nos 53 casos divergentes: **675.392 mil R$** (R$ 675,392 milhões). Diferença líquida BD menos SIDRA nos casos comparáveis: **+134.080 mil R$** (R$ 134,080 milhões). Esses totais não incluem o caso de valor BD presente com SIDRA ausente.

## Distribuição por cultura

| Cultura | Iguais | Divergentes | Ausentes ambas | BD presente / SIDRA ausente | Sem linha BD |
|---|---:|---:|---:|---:|---:|
| Arroz | 1.592 | 14 | 3.957 | 0 | 1 |
| Café total | 1.334 | 21 | 4.186 | 0 | 23 |
| Cana | 3.188 | 7 | 2.367 | 1 | 1 |
| Milho | 5.025 | 11 | 527 | 0 | 1 |
| Soja | 2.640 | **0** | 2.923 | 0 | 1 |

## Estados prioritários por diferença absoluta (mil R$)

| UF | Casos divergentes | Soma absoluta |
|---|---:|---:|
| RO (11) | 16 | 336.510 |
| GO (52) | 5 | 306.761 |
| PE (26) | 7 | 22.494 |
| PR (41) | 2 | 6.658 |
| AC (12) | 20 | 2.104 |
| BA (29) | 1 | 487 |
| RJ (33) | 1 | 264 |
| DF (53) | 1 | 114 |

RO e GO concentram aproximadamente **95,24%** da soma das diferenças absolutas.

## Cinco maiores divergências (mil R$)

| Município | Produto | BD | SIDRA | BD − SIDRA |
|---|---|---:|---:|---:|
| 5205471 GO | Milho | 405.801 | 237.821 | +167.980 |
| 1100452 RO | Café | 170.605 | 31.891 | +138.714 |
| 5205471 GO | Cana | 293.760 | 429.760 | −136.000 |
| 1100098 RO | Café | 36.752 | 123.963 | −87.211 |
| 1100502 RO | Café | 101.397 | 144.329 | −42.932 |

## Diferenças de cobertura

A BD exportada contém **5.563 municípios**, enquanto o SIDRA contém **5.564**. Existem **27 chaves presentes apenas no SIDRA**, todas com valor ausente: 23 linhas de café, além das quatro outras culturas do município **5101837** (MT). O município 5101837 não aparece em nenhuma cultura na exportação BD. Esses 27 registros não constituem divergências monetárias e não devem ser interpretados como valores zero.

O caso **5202502/GO/cana** possui valor BD **2.046 mil R$** e símbolo SIDRA `-` (ausente). Não entra no total de 53 diferenças numéricas; exige investigação específica.

## Interpretação e decisão

A concordância numérica é elevada entre pares comparáveis, mas as divergências se concentram em poucos municípios e alcançam valores economicamente relevantes. **Não há evidência suficiente para atribuir a causa a revisões oficiais, diferenças de ETL ou retificações específicas.** Manter valores originais, símbolos e proveniência, sem substituir silenciosamente os registros do atlas.

**Próxima ação:** documentar critérios de seleção da fonte publicada e gerar uma camada de qualidade municipal com `status_auditoria`, `valor_bd`, `valor_sidra` e `data_extracao`; verificar os 53 casos divergentes e a cobertura do município 5101837. Não realizar merge na `main` sem autorização.
