-- PAM 2024: verificar esquema, linhagem e valores de campos na Base dos Dados.
-- Executar cada SELECT separadamente no BigQuery caso o console não permita
-- múltiplas consultas. INFORMATION_SCHEMA não revela necessariamente ETL.
SELECT table_name, column_name, data_type, ordinal_position
FROM `basedosdados.br_ibge_pam.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name IN ('lavoura_permanente','lavoura_temporaria')
ORDER BY table_name, ordinal_position;

-- Descrições e rótulos (se preenchidos no BigQuery).
SELECT table_name, option_name, option_value
FROM `basedosdados.br_ibge_pam.INFORMATION_SCHEMA.TABLE_OPTIONS`
WHERE table_name IN ('lavoura_permanente','lavoura_temporaria')
ORDER BY table_name, option_name;

-- A partir do esquema acima, conferir nomes dos campos e, só então,
-- executar os diagnósticos de 2024 em consultas separadas.
