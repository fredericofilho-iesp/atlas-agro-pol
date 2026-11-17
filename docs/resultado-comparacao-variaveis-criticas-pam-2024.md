# Comparação multivariada PAM 2024 — seis casos críticos

**Execução validada:** [Actions #44096945521](https://github.com/fredericofilho-iesp/atlas-agro-pol/actions/runs/44096945521) (17/11/2026). Coletor `pipeline/coletar_pam_ibge_variaveis_criticas.py`: **sucesso**, seis registros distintos, cinco variáveis. Artefato `pam-variaveis-criticas-2024-44096945521`.

## Resultados

A comparação utiliza os cinco registros **completos da BD** compartilhados pelo pesquisador em 17/11/2026 e os seis registros oficiais do SIDRA extraídos pelo workflow. A linha BD de **GO milho, município 5205471**, ficou incompleta na transcrição enviada; nesse caso a comparação monetária anterior já é conhecida, mas área/quantidade/rendimento BD ainda não são observados aqui.

| Município IBGE | Produto | Área colhida BD → SIDRA (ha) | Quantidade BD → SIDRA (t) | Rendimento BD → SIDRA (kg/ha) | Valor BD → SIDRA (mil R$) |
|---|---|---|---|---|---|
| 5205471 (GO) | Cana | 27.000 → 39.500 | 2.295.000 → 3.357.500 | 85.000 → 85.000 | 293.760 → 429.760 |
| 5205471 (GO) | Milho | BD não informada → 47.300 | BD não informada → 319.260 | BD não informada → 6.750 | 405.801 → 237.821 |
| 5202502 (GO) | Cana | 186 → ausente | 18.600 → ausente | 100.000 → ausente | 2.046 → ausente (`-`) |
| 1100098 (RO) | Café total | 580 → 2.100 | 2.148 → 7.245 | 3.703 → 3.450 | 36.752 → 123.963 |
| 1100452 (RO) | Café total | 4.450 → 750 | 10.635 → 1.988 | 2.390 → 2.651 | 170.605 → 31.891 |
| 1100502 (RO) | Café total | 1.630 → 2.320 | 5.980 → 8.512 | 3.669 → 3.669 | 101.397 → 144.329 |

Todos os valores são relativos a 2024. Não converter valores SIDRA ausentes em zero.

## Implicações

1. **Rejeita-se, nesses cinco casos completos, a explicação de divergência exclusivamente monetária.** Áreas e quantidades também diferem em quatro casos; o quinto (5202502) está inteiramente ausente na extração SIDRA, inclusive área, quantidade e rendimento.
2. Em **GO/cana 5205471**, o rendimento é idêntico, enquanto área e quantidade diferem; valor monetário também muda. Em **RO/café 1100502**, rendimento é idêntico, enquanto área, quantidade e valor mudam. Isso é compatível com revisão de extensão/volume sem alteração do rendimento, **não prova** a causa.
3. Em **RO/café 1100098 e 1100452**, as cinco variáveis diferem; são alterações de perfil produtivo e monetário, não apenas preços.
4. **Limite probatório:** estas informações evidenciam duas versões divergentes de registros; ainda é necessário obter snapshot histórico oficial, histórico de retificações ou código ETL efetivamente empregado em 2025 antes de atribuir a causa a revisão estatística ou processamento.

## Recomendação

Para indicadores correntes do atlas, manter SIDRA como referência **provisória** nos seis casos, quando houver valor oficial informado; registrar a data de extração e guardar o campo BD original para auditoria. Em 5202502, marcar **ausente no SIDRA**, não zero. Evitar substituir toda a série sem um plano de reconciliação de UFs, produtos e datas. Não realizar merge do PR nesta etapa.
