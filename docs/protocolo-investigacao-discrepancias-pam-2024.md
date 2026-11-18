# Protocolo de investigação das discrepâncias municipais PAM 2024

## Resultado já observado

Confronto independente SIDRA/BD de 1.150 chaves municipais (seis pares UF × cultura):
656 valores iguais, 43 diferentes, 450 ausentes nas duas fontes e um informado
na BD e ausente no SIDRA. Os valores oficiais foram extraídos em 17/11/2026.

## Hipóteses concorrentes e testes

1. **Revisões de série/versões distintas:** consultar os metadados e o histórico
   de atualização da PAM e da Base dos Dados. Diferença entre fontes não prova
   revisão. Registre a data de extração, tabela 5457, variável 215, classificação
   782 e os códigos de categoria de cada produto.
2. **Mudanças em poucos municípios:** inspecionar os maiores deltas no arquivo
   `auditoria_municipal_ranking.csv`; o município de código 5205471 (GO)
   concentra as diferenças de milho (+167.980 mil R$) e cana (−136.000 mil R$).
   O sinal oposto por produto exige comparação específica dos registros.
3. **Ausências e convenções de símbolos:** verificar o símbolo SIDRA original
   (`-`, `...`, etc.) e os campos de produção e área; não imputar zero.
   No código 5202502, GO/cana, BD registra 2.046 mil R$ e SIDRA `-`.
4. **Reconciliação municipal-estadual:** calcular separadamente a soma municipal
   oficial e o total estadual oficial; pequenas diferenças de arredondamento
   não justificam discrepâncias municipais de centenas de milhões de reais.

## Execução reproduzível

A entrada é o CSV de confronto municipal com colunas `ano`, `codigo_uf`,
`id_municipio`, `produto`, `valor_producao_mil_reais_bd`,
`valor_producao_mil_reais_sidra`, `simbolo_sidra`. Execute:

```bash
python -m pipeline.diagnosticar_divergencias_pam \
  --entrada data/raw/comparacao_municipal_pam_2024.csv \
  --saida-dir auditoria
```

O comando produz detalhe, ranking e resumo por UF/cultura. Para
reproduzir a análise no repositório, é preciso primeiro adicionar o CSV
de entrada à branch de auditoria; **não se deve declarar a execução
reproduzida no GitHub antes disso**.

## Regra de publicação

Manter valores BD e SIDRA identificados por fonte e data, sem substituir
automaticamente registros municipais. Documentar casos discrepantes antes
de derivar indicadores, mapas e rankings econômicos.
