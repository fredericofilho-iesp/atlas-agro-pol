# Validação estadual PAM — procedimento reproduzível

**Status em 17/11/2026:** coleta oficial SIDRA por UF executada com sucesso no GitHub Actions (run 44060920654), com 135 linhas. **A comparação estadual com a Base dos Dados continua pendente**, pois a tabela estadual BD ainda não foi disponibilizada como CSV no repositório.

1. Execute `docs/sql/pam_validacao_uf.sql` no BigQuery, definindo
   `@ano_inicio` e `@ano_fim` (2024 para o piloto), e exporte o resultado
   completo como CSV UTF-8 para `data/raw/pam_bd_uf_2024.csv`.
2. A coleta oficial é realizada automaticamente pelo workflow `Validação PAM — IBGE` (o artefato da execução 44060920654 contém `pam_ibge_uf_2024.csv`). Alternativamente, obtenha tabela oficial da PAM/SIDRA/IBGE **por UF, ano e produto**,
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

## Comparação automática no Pull Request

Após exportar o resultado BigQuery, adicione **somente o CSV público de agregados estaduais**
`data/raw/pam_bd_uf_2024.csv` à branch `auditoria-tecnica-2026-11`.
O workflow executará novamente a coleta oficial, comparará as 135 chaves
(`ano`, `codigo_uf`, `produto`) e publicará no artefato:
`comparacao_pam_uf_2024.csv` e `resumo-comparacao.txt`, com as 15 maiores
 diferenças absolutas. **Não envie credenciais, arquivos de acesso ao BigQuery
ou bases privadas.** Se o CSV não estiver presente, a execução informará
explicitamente que a comparação está pendente, sem alegar validação estatística.

A aprovação do workflow de coleta, isoladamente, **não comprova equivalência
entre os agregados das duas fontes**.
