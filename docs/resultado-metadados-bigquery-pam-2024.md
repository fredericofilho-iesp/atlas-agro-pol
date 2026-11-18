# Metadados de atualização das tabelas PAM no BigQuery

Consulta: `docs/sql/pam_metadados_bigquery.sql`. Resultado fornecido pelo pesquisador em 17/11/2026.

| tabela | criada_em_utc | ultima_modificacao_bigquery_utc | linhas_estimadas | tamanho_bytes |
|---|---|---|---:|---:|
| lavoura_permanente | 2025-10-03 18:16:43.278 UTC | 2025-10-03 18:16:45.664 UTC | 10.734.658 | 437.993.546 |
| lavoura_temporaria | 2025-10-03 18:16:43.531 UTC | 2025-10-03 18:16:46.153 UTC | 9.362.529 | 418.691.227 |

**Interpretação:** ambas as tabelas foram criadas e modificadas no BigQuery em 03/10/2025, em segundos próximos. Isso é consistente com uma carga conjunta das duas tabelas nessa data. O campo `last_modified_time` informa modificação do objeto BigQuery; **não prova** que todos os registros de 2024 foram atualizados nessa data, que o IBGE os revisou posteriormente, nem que a carga corresponde à primeira versão da PAM 2024. A consulta também não oferece histórico de alterações por município.

A coleta oficial SIDRA municipal executada pelo projeto em 17/11/2026 é posterior à última modificação observada das tabelas BD. A defasagem temporal é **compatível** com a hipótese de versões diferentes, mas **não confirma** sua causa.

## Teste discriminante proposto

Para cada um dos 43 registros discrepantes, obter uma cópia oficial da PAM 2024 datada de 2025, idealmente anterior ou próxima à carga de 03/10/2025. Comparar três valores: (a) SIDRA histórico 2025; (b) BD carregada em 2025; (c) SIDRA atual 2026. Se (a) = (b) e (c) difere, haverá evidência forte de revisão posterior à carga BD. Se (a) = (c) e (b) difere, priorizar auditoria do ETL/categorização da BD. Se os três diferem, examinar versões e classificação.

**Próximo passo sem BigQuery:** procurar arquivos históricos da PAM em fontes oficiais, preservando metadados e datas de extração. Não alterar valores do atlas até confirmar a proveniência.
