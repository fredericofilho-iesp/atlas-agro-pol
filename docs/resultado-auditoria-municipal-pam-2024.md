# Auditoria municipal PAM 2024 — confronto SIDRA × Base dos Dados

**Execução oficial:** [GitHub Actions #44069002204](https://github.com/fredericofilho-iesp/atlas-agro-pol/actions/runs/44069002204), workflow `Auditoria municipal PAM — SIDRA`, em 17/11/2026. **Fonte BD:** exportação municipal da consulta `docs/sql/pam_auditoria_municipios_2024.sql` fornecida pelo pesquisador. **Unidade:** mil reais. Comparação realizada pelo código municipal IBGE, ano e cultura. O arquivo analítico completo foi gerado fora do repositório nesta etapa.

## Resultados

- As duas fontes contêm **1.150 linhas** com exatamente as mesmas chaves.
- **656 pares numericamente iguais**, **43 divergentes**, **450 sem valor em ambas** e **1 com valor na BD e símbolo "-" no SIDRA**.
- Valores oficiais ausentes: **451** (446 com símbolo `-` e 5 com `...`). Ausência não equivale automaticamente a zero.
- Os 43 pares divergentes concentram-se em 6 grupos; sua soma de diferenças pode apresentar compensação entre municípios.

| UF | Cultura | Iguais | Divergentes | Nulos nas duas | Exceção BD informado / SIDRA ausente |
|---|---|---:|---:|---:|---:|
| GO | Milho | 211 | 1 | 34 | 0 |
| GO | Cana-de-açúcar | 109 | 3 | 133 | 1 |
| RO | Café total | 36 | 16 | 0 | 0 |
| PE | Milho | 119 | 7 | 59 | 0 |
| PR | Café total | 173 | 2 | 224 | 0 |
| AC | Arroz | 8 | 14 | 0 | 0 |

### Municípios com maiores diferenças absolutas (BD − SIDRA, em mil reais)

| Código municipal | UF | Cultura | BD | SIDRA | Diferença |
|---|---|---|---:|---:|---:|
| 5205471 | GO | Milho | 405.801 | 237.821 | +167.980 |
| 1100452 | RO | Café | 170.605 | 31.891 | +138.714 |
| 5205471 | GO | Cana | 293.760 | 429.760 | −136.000 |
| 1100098 | RO | Café | 36.752 | 123.963 | −87.211 |
| 1100502 | RO | Café | 101.397 | 144.329 | −42.932 |

**Achado crítico:** em Goiás, o mesmo código municipal **5205471** é responsável por quase toda a diferença do milho e pela maior parte da diferença da cana. A diferença oficial BD/SIDRA nesses grupos não é disseminada por todos os municípios.

**Inconsistência de ausência:** a BD informa **2.046 mil reais** na cana em Goiás, município **5202502**, mas o SIDRA usa `-`; exige revisão da codificação original.

**Importante sobre reconciliação:** o total SIDRA extraído diretamente de municípios pode diferir em alguns milhares de reais da consulta SIDRA diretamente por UF; não se deve pressupor aditividade exata sem testar categorias, revisões ou arredondamentos. Ex.: GO milho soma municipal SIDRA = 9.665.847, enquanto UF SIDRA previamente extraída = 9.665.843; PE milho = 112.527 vs 112.524; RO café = 2.825.712 vs 2.825.713.

## Limites da interpretação

A detecção de divergências não determina qual fonte está correta nem por que houve alterações. A hipótese de **revisões ou diferenças de versão** é plausível, mas necessita de registros oficiais de metadados, data de extração, revisão e histórico. O símbolo `-` do SIDRA foi preservado: não imputar como zero. Os campos de café representam café total e não devem ser somados com arábica/canephora.

## Decisão provisória

Não efetuar substituição em massa dos valores municipais BD nem merge do PR antes de documentar discrepâncias e seus efeitos nos indicadores. Para publicação dos mapas, preferir rastreabilidade por fonte e sinalização de qualidade, com série de extração oficial datada.
