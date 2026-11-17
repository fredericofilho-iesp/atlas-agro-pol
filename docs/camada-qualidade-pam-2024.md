# Camada nacional de qualidade PAM 2024 — versão preliminar

**Situação:** camada analítica gerada em 17/11/2026, **não publicada no atlas**, sem alteração da `main`. O script reprodutível está em `pipeline/gerar_camada_qualidade_pam.py`; a fonte de entrada é a comparação nacional de 27.820 chaves BD × SIDRA.

## Estrutura

Cada linha representa uma combinação ano/município/cultura. Campos principais:

- `valor_bd_mil_reais`, `valor_sidra_mil_reais`: valores originais, sem sobrescrita.
- `valor_referencia_mil_reais`: SIDRA quando numérico; ausente caso contrário (referência **provisória**).
- `fonte_referencia`: identificação explícita da origem.
- `status_auditoria`: `concordante`, `divergente`, `ausentes_ambas`, `ausentes_bd`, `ausentes_sidra`, `sem_linha_bd` ou `sem_linha_sidra`.
- `diferenca_bd_menos_sidra_mil_reais`, `diferenca_absoluta_mil_reais`, `diferenca_relativa_sidra_pct`: calculados **somente** quando os dois valores são numéricos; diferença relativa não é definida para denominador SIDRA igual a zero.
- `simbolo_sidra`, `presenca_bd`, `presenca_sidra`, `data_extracao_sidra`, `data_extracao_bd`, `unidade`: rastreabilidade.

**Contagens esperadas** para o CSV recebido: 13.779 concordantes, 53 divergentes, 13.960 ausentes em ambas, 1 ausente no SIDRA e 27 sem linha BD. Não há ausência de linha SIDRA. Os 27 casos sem linha BD não são diferenças numéricas.

## Uso seguro no atlas

1. **Não usar** `valor_referencia_mil_reais` para preencher automaticamente valores ausentes do SIDRA com BD; manter ausência.
2. Para mapas municipais, indicar visualmente valores não informados e disponibilizar o `status_auditoria` em tooltip ou painel de detalhes.
3. Para agregados estaduais, preferir o total estadual oficial SIDRA; a soma de valores municipais arredondados pode apresentar pequenas diferenças.
4. Os 53 casos divergentes devem ter sinalização de qualidade e acesso aos valores de ambas as fontes.
5. Antes de publicar, revisar se a ausência de 27 linhas BD resulta de cobertura/ETL e confirmar data de extração BD, ainda não documentada com precisão.
6. Não usar este arquivo como base de áreas, volumes físicos ou rendimento: esta camada se refere **somente ao valor da produção**.

## Reprodução

```bash
python -m unittest discover -s tests -p 'test_gerar_camada_qualidade_pam.py' -v
python -m pipeline.gerar_camada_qualidade_pam \
  --entrada auditoria/comparacao_bd_sidra_municipal_nacional_2024.csv \
  --saida auditoria/camada_qualidade_pam_2024.csv \
  --data-sidra 2026-11-17
```

O CSV de entrada não foi incluído no GitHub para evitar versionar dados grandes sem política de armazenamento. Está disponível nos artefatos da análise; a versão reproduzível poderá ser gerada novamente a partir das duas fontes originais. O teste CI da nova etapa ainda precisa ser executado no GitHub.
