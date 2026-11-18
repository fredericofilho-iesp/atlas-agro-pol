-- Auditoria de valores nulos: PAM 2024, Base dos Dados.
-- A Base dos Dados informa que '-', '..' e '...' foram convertidos para NULL.
-- Logo NULL não distingue zero absoluto, não aplicável e indisponível.
-- Esta consulta é diagnóstica; NÃO publica totais municipais.
WITH producao AS (
 SELECT 'permanente' AS tipo_lavoura, id_municipio, produto, valor_producao, quantidade_produzida, area_colhida
 FROM `basedosdados.br_ibge_pam.lavoura_permanente` WHERE ano = 2024
 UNION ALL
 SELECT 'temporaria' AS tipo_lavoura, id_municipio, produto, valor_producao, quantidade_produzida, area_colhida
 FROM `basedosdados.br_ibge_pam.lavoura_temporaria` WHERE ano = 2024
)
SELECT tipo_lavoura, COUNT(*) AS registros,
 COUNTIF(valor_producao IS NULL) AS valor_nulo,
 COUNTIF(valor_producao IS NULL AND (quantidade_produzida > 0 OR area_colhida > 0)) AS valor_nulo_producao_fisica,
 COUNT(DISTINCT id_municipio) AS municipios
FROM producao GROUP BY 1 ORDER BY 1;
