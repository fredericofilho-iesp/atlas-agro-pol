# Auditoria técnica inicial — 16/11/2026

**Estado:** inspeção estática; ainda não houve execução de coleta real nem validação integral dos testes nesta branch.

## Arquivos examinados
- README.md; pipeline/config.py; pipeline/__main__.py; pipeline/sidra.py; pipeline/coletar.py; pipeline/indicadores.py; rodar_coleta.bat; .github/workflows/testes.yml.

## Achados prioritários
1. **Bloqueio estrutural da coleta:** `pipeline/coletar.py:main` chama `sidra.testar_conexao()` antes de qualquer fonte, inclusive malha e futuras fontes independentes. O teste depende do domínio legado `apisidra.ibge.gov.br`, sujeito a desafios HTTP 403.
2. **Dependência de endpoint legado:** `sidra.py` obtém metadados via `desctabapi.aspx` e valores via `/values`. Avaliar migração à API oficial de Agregados v3 (`servicodados.ibge.gov.br/api/v3/agregados`), validando diferenças de esquema e limites de consulta. Não basta trocar a URL.
3. **Inconsistência de nomenclatura econômica:** `vbp_sobre_pib` é chamado de aproximação do peso do agro. É apenas razão entre grandezas diferentes, **não** participação no PIB. O somatório PAM + PPM origem animal + PEVS é indicador parcial de valor de produção, não VBP agropecuário abrangente, pois exclui abate e outros componentes.
4. **Risco de totalizações incompletas:** `total_por_municipio` usa a categoria Total globalmente quando ela aparece em qualquer registro; verificar disponibilidade de totais por tabela, município e ano e evitar soma de categorias hierárquicas. `soma` ignora ausências, podendo produzir agregados incompletos sem sinalização de cobertura.
5. **Períodos e comparabilidade:** fontes podem ter anos de referência diferentes; não usar automaticamente o último ano de uma série para todas as camadas. Validar deflator IPCA e metadados de unidade.
6. **Integridade territorial:** lista de municípios derivada da tabela de PIB do último ano; preferir cadastro oficial de localidades e verificar mudanças de cobertura.
7. **Infraestrutura:** workflow `testes.yml` executa apenas testes simulados; não certifica a conectividade real. Não há front-end pronto comprovado.

## Próximos testes, antes de modificar o pipeline
- Testar metadados e um único município/ano na API v3, registrando status HTTP, formato JSON e cobertura.
- Validar tabelas e variáveis de PAM, PIB, IPCA e Censo Agro.
- Testar casos de sigilo, ausência, total hierárquico, série com ano ausente e cobertura incompleta.
- Separar coleta por fonte; falha de uma fonte não deve bloquear as demais.
- Publicar primeiro um painel nacional mínimo com indicador bem definido e ano explícito.

## Critérios de aceite
- Fonte e tabela documentadas, data de extração, unidade, ano e cobertura por indicador.
- Nenhuma imputação automática de sigilo como zero.
- Nenhuma razão VBP/PIB rotulada como participação no PIB.
- Testes automatizados e amostra real verificada antes de atualizar `main`.
- Nenhuma alteração em `main` sem revisão.
