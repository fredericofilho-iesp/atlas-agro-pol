# Pesquisa de versões históricas da PAM 2024 — 17/11/2026

## Fontes documentais localizadas

1. **IBGE, página oficial da PAM**: https://www.ibge.gov.br/estatisticas/economicas/agricultura-e-pecuaria/9117-producao-agricola-municipal.html. Descreve a unidade municipal, o critério de divulgação (ao menos 1 ha e 1 t) e a integração dos dados do LSPA à PAM.
2. **IBGE, apresentação da PAM 2024 (setembro/2025)**: https://agenciadenoticias.ibge.gov.br/media/com_mediaibge/arquivos/86bd2f37f9fffb7f3941e1c74351f469.pdf. Evidência contemporânea de divulgação, **não uma tabela municipal arquivada**.
3. **Serviço Florestal Brasileiro, metadados da PAM 1994–2024**: https://dados.florestal.gov.br/dataset/2e0b7844-0039-4a23-a2ed-14f353fe4b29/resource/b89cbe41-121f-4ce4-9b02-bcde32b8391c/download/metadados_snif_pam_1994-2024_ibge_set_2025.pdf. Registra publicação 11/09/2025 e extração 17/09/2025. **Cautela:** os valores de produção no SNIF foram deflacionados pelo IPCA para dez/2024; não comparar diretamente com valores nominais do SIDRA/BD.
4. **Base dos Dados, catálogo da PAM**: https://basedosdados.org/dataset/fc403b40-a7e1-40e7-9efe-910847b45a69?table=bd9b2960-361f-4465-be23-baaadaaf266d. Confirma última atualização em 03/10/2025 e conversão dos símbolos `...`, `..`, `-` para nulos.
5. **IBGE, nota técnica 01/2026**: https://www.ibge.gov.br/comunicados/47932-nota-tecnica-producao-agricola-municipal-pam. Alteração da lista de produtos **a partir de 2025**; não comprova revisão dos valores municipais de 2024.
6. **IBGE, Erramos**: https://www.ibge.gov.br/erramos. Canal institucional de retificações; nenhuma retificação específica dos 43 pares foi confirmada nesta busca.

## Resultado e decisão

**Ainda não foi encontrada uma cópia oficial arquivada, datada de 2025, contendo os valores nominais de 2024 dos municípios críticos.** Não declarar a hipótese de revisão como comprovada.

Próxima tentativa: localizar no FTP do IBGE arquivos originais PAM 2024 com carimbo de versão/alteração de 2025; validar unidade e classificação antes de confrontar. Caso não exista snapshot oficial, solicitar ao IBGE por canal institucional o histórico de revisões da tabela 5457 para os códigos 5205471, 1100452, 1100098, 1100502 e 5202502, variável 215, categorias 782 para milho, cana e café, ano 2024.

A diferença de versão é plausível pela cronologia, mas um **ETL da Base dos Dados** também permanece hipótese concorrente. Manter a base analítica com proveniência e preservar ausências.
