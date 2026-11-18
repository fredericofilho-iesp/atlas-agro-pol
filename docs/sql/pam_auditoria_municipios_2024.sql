-- Auditoria municipal das discrepâncias PAM 2024: GO (milho e cana),
-- RO (café), PE (milho), PR (café), AC (arroz).
-- Fonte: basedosdados.br_ibge_pam. Valores em mil R$.
-- Retorna TODAS as linhas de municípios dos pares prioritários,
-- inclusive NULL; não confundir NULL com produção zero.
WITH base AS (
  SELECT ano, CAST(id_municipio AS STRING) AS id_municipio,
         produto, valor_producao, 'permanente' AS origem
  FROM `basedosdados.br_ibge_pam.lavoura_permanente`
  WHERE ano = 2024
  UNION ALL
  SELECT ano, CAST(id_municipio AS STRING), produto, valor_producao,
         'temporaria' AS origem
  FROM `basedosdados.br_ibge_pam.lavoura_temporaria`
  WHERE ano = 2024
),
alvos AS (
  SELECT '52' codigo_uf, 'Milho (em grão)' produto UNION ALL
  SELECT '52', 'Cana-de-açúcar' UNION ALL
  SELECT '11', 'Café (em grão) Total' UNION ALL
  SELECT '26', 'Milho (em grão)' UNION ALL
  SELECT '41', 'Café (em grão) Total' UNION ALL
  SELECT '12', 'Arroz (em casca)'
)
SELECT b.ano, SUBSTR(b.id_municipio, 1, 2) AS codigo_uf,
       b.id_municipio, b.produto, b.origem,
       b.valor_producao AS valor_producao_mil_reais,
       IF(b.valor_producao IS NULL, 'nulo', 'informado') AS status_valor
FROM base b
JOIN alvos a
  ON SUBSTR(b.id_municipio, 1, 2) = a.codigo_uf
 AND b.produto = a.produto
ORDER BY codigo_uf, b.produto, b.valor_producao DESC, b.id_municipio;
