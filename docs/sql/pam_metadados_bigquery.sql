-- Auditoria de metadados BigQuery para a PAM (não é histórico de versões).
-- Executar no projeto atlas-agro-pol, região compatível com o dataset público.
-- __TABLES__.last_modified_time indica modificação do objeto BigQuery,
-- não a data de extração original, nem comprova revisão do IBGE.
SELECT
  table_id AS tabela,
  TIMESTAMP_MILLIS(creation_time) AS criada_em_utc,
  TIMESTAMP_MILLIS(last_modified_time) AS ultima_modificacao_bigquery_utc,
  row_count AS linhas_estimadas,
  size_bytes AS tamanho_bytes
FROM `basedosdados.br_ibge_pam.__TABLES__`
WHERE table_id IN ('lavoura_permanente', 'lavoura_temporaria')
ORDER BY tabela;
