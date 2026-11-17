# PAM 2024 — investigação documental de versões e revisões (17/11/2026)

## Evidências verificadas

- Fonte primária: IBGE, **Produção Agrícola Municipal**, tabela SIDRA **5457**, variável **215** (valor da produção, mil reais), classificação **782**. Documentação oficial: https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal-culturas-temporarias-e-permanentes.html e https://sidra.ibge.gov.br/tabela/5457.
- O IBGE informa que a PAM divulga dados municipais de área, quantidade, rendimento e valor de produção, e disponibiliza série histórica no SIDRA. A presença de símbolos de ausência deve ser tratada conforme metadados da pesquisa, não convertida em zero.
- O Serviço Florestal Brasileiro registra, em metadados de sua extração da PAM 2024, **publicação pelo IBGE em 11/09/2025** e **coleta em 17/09/2025**: https://dados.florestal.gov.br/dataset/2e0b7844-0039-4a23-a2ed-14f353fe4b29/resource/b89cbe41-121f-4ce4-9b02-bcde32b8391c/download/metadados_snif_pam_1994-2024_ibge_set_2025.pdf. **Esta data é de uma extração de terceiro e não prova que a Base dos Dados use a mesma versão.**
- Extração independente do SIDRA pelo workflow em 17/11/2026: https://github.com/fredericofilho-iesp/atlas-agro-pol/actions/runs/44069002204.

## Confronto empírico

O cruzamento fornecido para auditoria contém **1.150** chaves municipais: **656 iguais**, **43 numericamente diferentes**, **450 ausentes nas duas fontes**, **1 valor BD informado e SIDRA ausente**. Os **cinco maiores deltas absolutos representam 85,15%** da soma das diferenças absolutas dos 43 casos (672.710 mil reais). Esse percentual não deve ser confundido com diferença líquida estadual, porque valores positivos e negativos se compensam.

| Município IBGE | Cultura | BD (mil R$) | SIDRA (mil R$) | BD − SIDRA (mil R$) |
|---|---|---:|---:|---:|
| 5205471 | Milho | 405.801 | 237.821 | +167.980 |
| 1100452 | Café total | 170.605 | 31.891 | +138.714 |
| 5205471 | Cana-de-açúcar | 293.760 | 429.760 | −136.000 |
| 1100098 | Café total | 36.752 | 123.963 | −87.211 |
| 1100502 | Café total | 101.397 | 144.329 | −42.932 |

## Conclusão documental, com grau de certeza

**Confirmado:** duas extrações, realizadas por caminhos distintos, contêm valores diferentes para 43 pares município × cultura. Os dados municipais oficiais foram obtidos diretamente do SIDRA em novembro de 2026.

**Não confirmado:** que os valores da Base dos Dados sejam de uma edição antiga, que a divergência tenha sido causada por revisão oficial, ou que um dos sistemas tenha erro de processamento. O documento do SFB demonstra uma data de publicação/coleta da PAM 2024, **não um histórico de versões municipais**. O material público consultado não identifica os motivos específicos das cinco discrepâncias maiores.

## Próximas verificações necessárias

1. Registrar o timestamp e, se disponível, o identificador de atualização das tabelas `basedosdados.br_ibge_pam.lavoura_permanente` e `lavoura_temporaria`; consultar metadados e pipeline de ingestão da BD.
2. Verificar se existem snapshots arquivados da PAM 2024 com os **mesmos códigos municipais e produtos**; confrontar especificamente os cinco maiores deltas. Uma extração de 2025, se encontrada, será evidência mais forte de revisão do que um metadado sem valores.
3. Para 5205471, verificar milho e cana simultaneamente; para 1100452, 1100098 e 1100502, café total. Manter o código IBGE como chave e verificar rótulos/categorias.
4. Investigar o caso 5202502 (cana): BD = 2.046 mil reais, SIDRA = `-`. Verificar se o símbolo significa ausência, não ocorrência ou outro código segundo documentação.
5. Antes da publicação, definir fonte de referência e data de extração para cada indicador. Não substituir automaticamente valores sem registrar a decisão.

**Status:** auditoria de diferenças concluída; **causalidade das diferenças em aberto**. O PR permanece aberto e não altera `main`.
