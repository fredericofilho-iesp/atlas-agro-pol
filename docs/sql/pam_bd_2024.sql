-- Piloto nacional: PAM 2024 por município e produto.
-- Fonte secundária: Base dos Dados, com dados originais do IBGE.
-- Executar no BigQuery em projeto autorizado; exportar resultado para CSV UTF-8.
-- Nota: não confundir valor de produção das lavouras com VBP total agropecuário.
-- Evitar SELECT * e conferir custo/limite de exportação antes de executar.
SELECT
  ano,
  id_municipio,
  produto,
  valor_producao,
  'permanente' AS tipo_lavoura
FROM `basedosdados.br_ibge_pam.lavoura_permanente`
WHERE ano = 2024
UNION ALL
SELECT
  ano,
  id_municipio,
  produto,
  valor_producao,
  'temporaria' AS tipo_lavoura
FROM `basedosdados.br_ibge_pam.lavoura_temporaria`
WHERE ano = 2024
ORDER BY id_municipio, tipo_lavoura, produto;
