# Resultado da coleta nacional municipal PAM 2024 — SIDRA

**Fonte:** IBGE/SIDRA, tabela 5457, variável 215, cinco culturas. **Execução original verificada:** [GitHub Actions #44106483533](https://github.com/fredericofilho-iesp/atlas-agro-pol/actions/runs/44106483533), em 17/11/2026. Todos os passos concluíram com **success**. Artefato `pam-sidra-nacional-2024-44106483533` (ID 14339460943).

## Cobertura municipal

| Métrica | Resultado |
|---|---:|
| Municípios distintos | 5.564 |
| Unidades da federação | 27 |
| Culturas | 5 |
| Pares UF/cultura | 135 |
| Registros município/cultura | 27.820 |
| Registros com valor informado | 13.832 |
| Registros ausentes (`-`) | 13.683 |
| Registros ausentes (`...`) | 305 |
| Total ausente | 13.988 |
| Duplicações de chave ano/município/produto | 0 |

**Nota:** 27.820 = 5 × 5.564, incluindo ausências explícitas; não significa 27.820 produções positivas. Não converter `-` e `...` em zero. A presença de uma linha por produto para cada município comprova cobertura do retorno da API, não produção agrícola da cultura.

## Reconciliação interna: município → total UF do SIDRA

Somas calculadas somente sobre valores informados, preservando como ausente grupos sem nenhum valor. Total UF extraído separadamente do SIDRA (tabela 5457, mesma variável e ano), armazenado nos arquivos de auditoria da etapa anterior.

- **125** pares UF/cultura com totais numéricos; **10** sem total numérico em ambas as consultas.
- Entre os 125 pares numéricos, **31** somas municipais coincidem exatamente com total UF e **94** diferem.
- A **maior diferença absoluta** é **37 mil R$** (MG/milho). A soma dos valores absolutos das diferenças é **418 mil R$**, equivalente a **0,0000767%** dos **544.710.175 mil R$** somados nos 125 totais estaduais de todas as cinco culturas.
- A diferença líquida entre somas municipais e totais estaduais é **+348 mil R$**.
- Diferenças pequenas dessa ordem são compatíveis com arredondamento de valores monetários municipais em milhares de reais; não constituem prova da causa do arredondamento. Manter o total estadual oficial como referência, evitando atribuir as discrepâncias automaticamente a falhas no pipeline.
- **Atenção:** os resultados acima **não** demonstram concordância nacional BD × SIDRA; são exclusivamente uma validação **SIDRA municipal × SIDRA estadual**.

## Estado da investigação BD × SIDRA

A comparação BD × SIDRA municipal ainda cobre apenas **seis pares prioritários**, com 1.150 registros e 43 divergências monetárias. Já existe comparação **BD agregado × SIDRA UF** para 135 pares; sete diferenças ultrapassam 1 milhão de R$ (1.000 mil R$) e justificam investigação. Expandir a comparação BD municipal × SIDRA municipal para cinco culturas em todos os municípios depende de obter/exportar a mesma seleção nacional de registros do BigQuery.

## Encaminhamentos reproduzíveis

- `pipeline/conciliar_pam_sidra_nacional.py` compara resultados municipais e totais UF, sem imputar zeros.
- O workflow `.github/workflows/pam-municipios-nacional.yml` foi **atualizado depois desta execução original** para realizar a reconciliação automaticamente e publicar `conciliacao_municipios_ufs_2024.csv`. Esta versão atualizada ainda depende de uma nova execução do CI.
- O próximo arquivo a coletar é **BD municipal nacional 2024** para as cinco culturas, garantindo chaves e símbolos compatíveis, sem alterar os dados do atlas ou `main`.
