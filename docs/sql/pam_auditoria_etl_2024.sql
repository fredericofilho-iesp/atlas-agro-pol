-- Auditoria ETL PAM 2024 — seis pares prioritários.
-- Esquema confirmado em 17/11/2026: ambas tabelas têm ano, sigla_uf,
-- id_municipio, produto, area_colhida, quantidade_produzida,
-- rendimento_medio_producao, valor_producao; permanentes têm
-- area_destinada_colheita; temporárias têm area_plantada.
-- Rodar cada instrução SELECT separadamente. Valores monetários em mil R$.

-- A. Integridade de chaves e cobertura por UF/produto.
WITH uniao AS (
 SELECT 'permanente' origem, ano, sigla_uf, id_municipio, produto,
        area_destinada_colheita AS area_referencia, area_colhida,
        quantidade_produzida, rendimento_medio_producao, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_permanente` WHERE ano=2024
 UNION ALL
 SELECT 'temporaria', ano, sigla_uf, id_municipio, produto,
        area_plantada, area_colhida, quantidade_produzida,
        rendimento_medio_producao, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_temporaria` WHERE ano=2024
),
alvos AS (
 SELECT 'GO' uf, 'Milho (em grão)' produto UNION ALL
 SELECT 'GO', 'Cana-de-açúcar' UNION ALL
 SELECT 'RO', 'Café (em grão) Total' UNION ALL
 SELECT 'PE', 'Milho (em grão)' UNION ALL
 SELECT 'PR', 'Café (em grão) Total' UNION ALL
 SELECT 'AC', 'Arroz (em casca)'
)
SELECT b.sigla_uf, b.produto, b.origem,
       COUNT(*) AS registros,
       COUNT(DISTINCT b.id_municipio) AS municipios_distintos,
       COUNTIF(b.valor_producao IS NULL) AS valor_nulo,
       COUNTIF(b.valor_producao = 0) AS valor_zero_explicito,
       COUNTIF(b.valor_producao < 0) AS valor_negativo,
       COUNTIF(b.area_colhida IS NULL) AS area_colhida_nula,
       COUNTIF(b.quantidade_produzida IS NULL) AS quantidade_nula,
       COUNTIF(b.valor_producao IS NOT NULL
               AND b.quantidade_produzida IS NULL) AS valor_sem_quantidade,
       COUNTIF(b.valor_producao IS NOT NULL
               AND b.area_colhida IS NULL) AS valor_sem_area,
       COUNTIF(SUBSTR(b.id_municipio,1,2) != CASE b.sigla_uf
         WHEN 'GO' THEN '52' WHEN 'RO' THEN '11'
         WHEN 'PE' THEN '26' WHEN 'PR' THEN '41'
         WHEN 'AC' THEN '12' END) AS codigo_uf_inconsistente
FROM uniao b JOIN alvos a
 ON b.sigla_uf=a.uf AND b.produto=a.produto
GROUP BY 1,2,3 ORDER BY 1,2,3;

-- B. Inspecionar registros completos dos municípios de maior discrepância,
-- incluindo áreas, quantidade e rendimento para avaliar se a diferença
-- está restrita ao valor monetário.
WITH uniao AS (
 SELECT 'permanente' origem, ano, sigla_uf, id_municipio, produto,
        area_destinada_colheita AS area_referencia, area_colhida,
        quantidade_produzida, rendimento_medio_producao, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_permanente` WHERE ano=2024
 UNION ALL
 SELECT 'temporaria', ano, sigla_uf, id_municipio, produto,
        area_plantada, area_colhida, quantidade_produzida,
        rendimento_medio_producao, valor_producao
 FROM `basedosdados.br_ibge_pam.lavoura_temporaria` WHERE ano=2024
)
SELECT *
FROM uniao
WHERE (id_municipio='5205471' AND produto IN ('Milho (em grão)','Cana-de-açúcar'))
   OR (id_municipio IN ('1100452','1100098','1100502')
       AND produto='Café (em grão) Total')
   OR (id_municipio='5202502' AND produto='Cana-de-açúcar')
ORDER BY id_municipio, produto, origem;

-- C. Duplicatas por chave natural; resultado esperado: zero linhas.
WITH uniao AS (
 SELECT 'permanente' origem, ano, sigla_uf, id_municipio, produto
 FROM `basedosdados.br_ibge_pam.lavoura_permanente` WHERE ano=2024
 UNION ALL
 SELECT 'temporaria', ano, sigla_uf, id_municipio, produto
 FROM `basedosdados.br_ibge_pam.lavoura_temporaria` WHERE ano=2024
)
SELECT ano, id_municipio, produto, COUNT(*) n,
       STRING_AGG(DISTINCT origem, ', ') AS origens
FROM uniao
WHERE (sigla_uf='GO' AND produto IN ('Milho (em grão)','Cana-de-açúcar'))
   OR (sigla_uf='RO' AND produto='Café (em grão) Total')
   OR (sigla_uf='PE' AND produto='Milho (em grão)')
   OR (sigla_uf='PR' AND produto='Café (em grão) Total')
   OR (sigla_uf='AC' AND produto='Arroz (em casca)')
GROUP BY 1,2,3 HAVING COUNT(*)>1 ORDER BY n DESC;
