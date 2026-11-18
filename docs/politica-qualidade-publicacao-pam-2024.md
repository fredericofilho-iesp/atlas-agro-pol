# Política provisória de qualidade e publicação — PAM 2024

**Estado:** proposta em auditoria, não aprovada para publicação; PR #1 permanece aberto.

## Fontes e proveniência
- **BD**: `basedosdados.br_ibge_pam.lavoura_permanente` e `lavoura_temporaria`, última modificação BigQuery informada pelo pesquisador: **03/10/2025**.
- **IBGE/SIDRA**: tabela 5457, variável 215 (valor da produção, mil R$), classificação 782, extração oficial municipal em **17/11/2026**.
- Não equiparar última modificação do BigQuery à data de revisão do IBGE.
- Preservar sempre: `fonte`, `ano_referencia`, `data_extracao`, `id_municipio`, `produto`, `unidade`, `simbolo_original` e `status_auditoria`.

## Classes de qualidade

| Status | Condição | Regra |
|---|---|---|
| `concordante` | BD e SIDRA têm o mesmo valor | Publicável com fonte e data |
| `divergente` | BD e SIDRA numéricos diferentes | Exibir fonte explícita; não substituir silenciosamente |
| `ausente_ambas` | Nenhuma fonte informa valor | Não imputar zero |
| `ausente_bd` | Apenas SIDRA informa valor | Sinalizar e investigar |
| `ausente_sidra` | Apenas BD informa valor | Sinalizar e investigar; não converter `-` em zero |
| `nao_auditado` | Não há comparação independente | Não declarar validado |

## Evidências de 2024

Nos seis pares UF/cultura auditados, 1.150 chaves municipais: 656 concordantes, 43 divergentes, 450 ausentes nas duas fontes e 1 ausente no SIDRA. O confronto multivariado dos casos prioritários mostrou diferenças também em áreas e quantidades produzidas, e não apenas no valor monetário. Isso **não comprova** revisão oficial; histórico de versões e ETL de 2025 seguem pendentes.

## Regras para o atlas

1. **Não alterar a camada de dados brutos** nem substituir BD por SIDRA de forma irreversível.
2. Para painéis de 2024, disponibilizar o valor SIDRA como **referência oficial provisória**, apenas quando presente, e registrar o valor BD em campo separado. A escolha final de fonte depende de reconciliação municipal/estadual para todas as cinco culturas.
3. Não produzir ranking municipal, agregados estaduais ou indicadores derivados como *validados* se contiverem chaves `divergente`, `ausente_sidra` ou `nao_auditado` sem nota de qualidade e critério de agregação.
4. Nunca tratar `NULL`, `-`, `...` ou outros símbolos de ausência como zero. Zero explícito só pode ser usado se a fonte informar 0.
5. Conferir coerência entre soma municipal e total estadual oficial; diferenças de arredondamento devem ser documentadas, não corrigidas automaticamente.
6. Em café, evitar dupla contagem de `Café (em grão) Total` com arábica/canephora.
7. Para séries temporais, manter a mesma definição de cultura, unidade e versão, ou explicitar quebras de série.
8. Mudança para `main` e publicação de dados reconciliados dependem de revisão dos relatórios e autorização do mantenedor.

## Critérios objetivos para liberar a publicação

- Cinco culturas × 27 UFs verificadas em agregados estaduais.
- Cobertura municipal conferida para os indicadores que serão publicados.
- Diferenças e ausências documentadas, com trilha de proveniência.
- Testes automatizados aprovados e artefatos de comparação arquivados.
- Decisão explícita de qual versão de cada indicador será publicada.

**Próximo passo operacional:** ampliar a coleta municipal SIDRA além dos seis pares prioritários e produzir relatório de cobertura, mantendo o PR aberto. Não pressupor que os 43 casos sejam o universo de divergências nacionais.
