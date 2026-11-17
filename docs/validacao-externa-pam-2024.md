# Auditoria nacional PAM 2024 — validação externa pendente

> **ATENÇÃO — retificação metodológica (17/11/2026).** Uma versão anterior
> deste documento atribuía cinco valores nacionais ao IBGE como se tivessem
> sido conferidos em fontes oficiais. **Essa verificação documental não foi
> demonstrada.** Os números anteriores foram retirados para evitar a
> circulação de referências não verificadas. Não citar a comparação anterior
> como evidência de concordância estatística.

## Valores observados na Base dos Dados

Resultados agregados pelo pesquisador no BigQuery, em **mil reais**:

| Cultura | Soma municipal BD 2024 |
|---|---:|
| Soja (em grão) | 260.233.559 |
| Cana-de-açúcar | 104.971.415 |
| Milho (em grão) | 88.118.185 |
| Café (em grão) Total | 69.205.996 |
| Arroz (em casca) | 22.317.494 |

**Fonte:** consultas às tabelas `basedosdados.br_ibge_pam.lavoura_permanente`
e `basedosdados.br_ibge_pam.lavoura_temporaria`, resultados fornecidos pelo
pesquisador. Estes valores **não** são benchmarks independentes do IBGE.

## Protocolo para completar a comparação

1. Obter valores oficiais diretamente do SIDRA/IBGE, tabela 5457, para o
   mesmo ano, produtos, unidade territorial e variável monetária.
2. Guardar o arquivo bruto, metadados da consulta, URL de origem e data.
3. Conferir unidade de medida, nomes/códigos das categorias e eventual
   existência de totais hierárquicos (café).
4. Comparar por UF antes de comparar o Brasil, preservando ausência de
   informação distinta de zero.
5. Documentar revisões e discrepâncias; não inferir causalidade de diferenças
   (sigilo, arredondamento etc.) sem evidência específica.

**Status:** nenhuma equivalência nacional ou estadual entre as duas fontes
foi validada independentemente neste documento.
