# Alternativa de aquisição — Base dos Dados / BigQuery

## Diagnóstico (16/11/2026)
A execução 43900179280 do GitHub Actions teve **timeout** nos três pedidos à API v3
do IBGE (PAM: metadados, períodos e amostra). Timeout não prova bloqueio
intencional. O serviço de Metadados Estatísticos do IBGE citado no catálogo do
Conecta Gov.br tem propósito de **metadados**, não substitui as tabelas PAM.

## Fontes verificadas
- Base dos Dados / IBGE PAM: `br_ibge_pam.lavoura_permanente` e
  `br_ibge_pam.lavoura_temporaria`, série anunciada até 2024.
- PIB municipal: `br_ibge_pib.municipio`, cobertura anunciada até 2023;
  disponibilização de abertura setorial depende do ano.
- PPM: tabelas por rebanhos, produção de origem animal e aquicultura;
  os indicadores não devem ser somados como se efetivos fossem produção.
- PEVS: extração vegetal e silvicultura, até 2024 no catálogo observado.

Fontes:
- https://basedosdados.org/dataset/fc403b40-a7e1-40e7-9efe-910847b45a69
- https://basedosdados.org/dataset/fcf025ca-8b19-4131-8e2d-5ddb12492347
- https://basedosdados.org/dataset/f7df4160-7a6f-4658-a287-3a73d412ed10
- https://basedosdados.org/dataset/cecb702d-d4b7-45ec-adbb-719ebd5b3906
- https://basedosdados.org/docs/access_data_bq
- https://www.gov.br/conecta/catalogo/apis/metadados-estatisticos-do-ibge

## Piloto PAM 2024
1. Validar nomes das duas tabelas e colunas no catálogo BigQuery, pois o esquema
   pode mudar. Abrir `docs/sql/pam_bd_2024.sql` no editor BigQuery e executar.
2. O projeto Google Cloud/BigQuery do pesquisador é necessário para consultas;
   não colocar credenciais ou chaves no repositório público. A Base dos Dados
   descreve uma franquia gratuita de consultas, sujeita aos limites atuais.
3. Exportar **todas as linhas** do resultado para CSV UTF-8. Não utilizar cópia
   truncada pela interface de resultados; se necessário exportar via Cloud Storage.
4. Executar `python -m pipeline.importar_bd_pam --entrada pam_bd_2024.csv`.
   O arquivo `data/interim/pam.csv.gz` resultante é compatível com o
   formato de entrada do pipeline de indicadores.
5. Validar cobertura nacional, duplicidades, produtos e agregação comparando
   com totais anuais oficiais antes da publicação.

O importador só usa biblioteca padrão, rejeita duplicatas e números inválidos,
preserva nulos e **não calcula totais municipais quando houver valores nulos**.
Ele soma exclusivamente os produtos explicitamente presentes no CSV; portanto,
a ausência de produtos/municípios na fonte ainda exige teste de completude.
O valor de produção da PAM representa **lavouras**, não agropecuária integral.

## Estado da integração
Este é um caminho alternativo **preparado, não executado com dados reais**.
Não substitui a coleta das demais fontes, tampouco resolve o cálculo de
VBP agropecuário abrangente. Não alterar `main` sem validação.
