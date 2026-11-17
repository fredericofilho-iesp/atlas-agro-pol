# Validação estadual PAM — procedimento reproduzível

**Status:** infraestrutura de comparação implementada; benchmarks oficiais
por UF **ainda não foram importados nem validados**. A tabela estadual de
135 linhas foi fornecida pelo pesquisador na conversa e não está persistida
em CSV no repositório.

1. Execute `docs/sql/pam_validacao_uf.sql` no BigQuery, definindo
   `@ano_inicio` e `@ano_fim` (2024 para o piloto), e exporte o resultado
   completo como CSV UTF-8 para `data/raw/pam_bd_uf_2024.csv`.
2. Obtenha tabela oficial da PAM/SIDRA/IBGE **por UF, ano e produto**,
   com valor da produção em mil reais, documentando tabela, variável,
   classificação, data de acesso e revisão. Prepare CSV com colunas
   `ano,codigo_uf,produto,valor_total_mil_reais`, usando exatamente
   os mesmos rótulos das cinco culturas na consulta BD.
3. Execute:
   `python -m pipeline.validar_pam_uf --bd data/raw/pam_bd_uf_2024.csv --oficial data/raw/pam_ibge_uf_2024.csv --saida data/processed/validacao_pam_uf_2024.csv`
4. Inspecione status `comparavel`, `bd_nulo`, `oficial_nulo`,
   `sem_linha_bd`, `sem_referencia_oficial`. Não converta NULL em zero.
   Para referência oficial igual a zero, diferença absoluta é calculada,
   percentual permanece em branco.

A comparação **não** infere que a soma municipal é igual ao agregado oficial
da UF; divergências podem envolver sigilo, revisões, cobertura e arredondamento.
Os valores oficiais **não devem ser fabricados** nem extraídos de tabelas
municipais da própria BD para serem chamados de validação independente.

O módulo usa apenas a biblioteca padrão Python e pode ser executado no
computador do pesquisador ou em ambiente com ambos os CSVs disponíveis.
O GitHub Actions de testes verifica a lógica sem consultar serviços externos.
