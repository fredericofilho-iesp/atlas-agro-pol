-- Exportação nacional BD/PAM municipal 2024 para auditoria com SIDRA.
-- Executar no BigQuery e EXPORTAR o resultado completo para CSV UTF-8.
-- Inclui valores NULL; nunca usar COALESCE(valor_producao, 0).
-- Mesmas culturas da coleta oficial SIDRA (tabela 5457/variável 215).
WITH base AS (
  SELECT ano, sigla_uf, CAST(id_municipio AS STRING) id_municipio,
         produto, valor_producao, 'permanente' origem
  FROM `basedosdados.br_ibge_pam.lavoura_permanente`
  WHERE ano = 2024 AND produto = 'Café (em grão) Total'
  UNION ALL
  SELECT ano, sigla_uf, CAST(id_municipio AS STRING), produto,
         valor_producao, 'temporaria'
  FROM `basedosdados.br_ibge_pam.lavoura_temporaria`
  WHERE ano = 2024
    AND produto IN ('Soja (em grão)', 'Milho (em grão)',
                    'Cana-de-açúcar', 'Arroz (em casca)')
)
SELECT
  ano,
  SUBSTR(id_municipio, 1, 2) AS codigo_uf,
  id_municipio,
  produto,
  origem,
  valor_producao AS valor_producao_mil_reais,
  IF(valor_producao IS NULL, 'nulo', 'informado') AS status_valor
FROM base
ORDER BY codigo_uf, id_municipio, produto;
