# Diagnóstico de discrepâncias — PAM 2024, UF × cultura

**Fontes:** CSV da consulta `docs/sql/pam_validacao_uf.sql` fornecido pelo pesquisador; CSV oficial produzido pelo workflow SIDRA, execução 44060920654. Valores em **mil reais**. Comparação independente de agregados estaduais, sem inferir causalidade das divergências.

## Síntese verificável

- 135 chaves (27 UFs × 5 culturas); 125 comparáveis e 10 com ambos os valores ausentes. NULL não é zero.
- 104 das 125 diferenças comparáveis têm módulo de **até 10 mil reais**.
- Soma dos módulos das diferenças estaduais: **408.676 mil reais**; os cinco maiores pares respondem por **404.819 mil reais (99,06%)**. Essa é uma soma de discrepâncias absolutas, não uma perda econômica.
- Diferenças nacionais líquidas (BD menos IBGE): soja +51; cana −132.816; milho +189.991; café +80.208; arroz −960 (mil reais). Diferenças nacionais líquidas podem ocultar compensações estaduais.

| UF | Cultura | BD (mil R$) | IBGE (mil R$) | BD − IBGE (mil R$) | Diferença (%) | Registros municipais nulos na BD |
|---|---|---:|---:|---:|---:|---:|
| GO (52) | Milho | 9.833.827 | 9.665.843 | +167.984 | +1,738 | 34 |
| GO (52) | Cana | 11.181.865 | 11.314.854 | −132.989 | −1,175 | 133 |
| RO (11) | Café total | 2.901.624 | 2.825.713 | +75.911 | +2,686 | 0 |
| PE (26) | Milho | 135.021 | 112.524 | +22.497 | +19,993 | 59 |
| PR (41) | Café total | 815.787 | 810.349 | +5.438 | +0,671 | 224 |
| AC (12) | Arroz | 5.671 | 6.692 | −1.021 | −15,257 | 0 |

## Hipóteses a testar, não conclusões

1. **Revisão ou defasagem de versões**: comparar o dado municipal da BD com o dado municipal *atual* do SIDRA, usando a mesma tabela/variável/classificação/ano.
2. **Dados ausentes**: verificar símbolos originais do IBGE para distinguir inexistência, indisponibilidade e sigilo. A presença de 0 nulos em RO-café e AC-arroz mostra que a ausência de valores não explica necessariamente esses pares.
3. **Municípios com valores extremos**: identificar contribuições concentradas, municípios e possíveis inconsistências; não se pode atribuir a discrepância a municípios específicos apenas com os agregados estaduais.
4. **Unidades e categorias**: conferir em metadados oficiais o código da categoria, a unidade (mil reais) e a equivalência entre café total e demais categorias.

## Próxima coleta

Execute `docs/sql/pam_auditoria_municipios_2024.sql` no projeto BigQuery e exporte CSV UTF-8 com os registros municipais dos seis pares acima. O arquivo **não é validação independente por si só**: permite localizar concentração de valores e padrões de NULL na BD. A identificação dos municípios que efetivamente divergem exige **segunda fonte municipal oficial** (SIDRA) com a mesma chave de município e produto.

**Critério para uso no atlas:** não substituir valores municipais da BD por agregados oficiais estaduais; manter sinalização de qualidade e rastreabilidade até conciliar as diferenças.
