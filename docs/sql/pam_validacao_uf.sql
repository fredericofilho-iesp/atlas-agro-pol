-- Base dos Dados/PAM: exportação por UF, cultura e ano.
-- BigQuery Standard SQL. Substitua os parâmetros @ano_inicio e @ano_fim
-- por parâmetros inteiros na interface do BigQuery (ex.: 2024 e 2024).
WITH base AS (
 SELECT ano, CAST(id_municipio AS STRING) AS id_municipio, produto, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_permanente`
 WHERE ano BETWEEN @ano_inicio AND @ano_fim
 UNION ALL
 SELECT ano, CAST(id_municipio AS STRING), produto, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_temporaria`
 WHERE ano BETWEEN @ano_inicio AND @ano_fim
)
SELECT ano, SUBSTR(id_municipio,1,2) AS codigo_uf, produto,
 COUNTIF(valor_producao IS NOT NULL) AS municipios_com_valor,
 COUNTIF(valor_producao IS NULL) AS registros_nulos,
 SUM(valor_producao) AS valor_total_mil_reais
FROM base
WHERE produto IN ('Soja (em grão)', 'Cana-de-açúcar', 'Milho (em grão)',
                  'Café (em grão) Total', 'Arroz (em casca)')
GROUP BY 1,2,3
ORDER BY 1,2,3;
