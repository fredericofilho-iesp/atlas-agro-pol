# Protótipo cartográfico PAM 2024 (não publicado)

## Arquivos
- Interface: `site/auditoria-pam/index.html`.
- Dados de entrada: `camada_qualidade_pam_2024.csv` produzida por `pipeline/gerar_camada_qualidade_pam.py`.
- Geometria: GeoJSON municipal simplificado carregado sob demanda de `tbrugz/geodata-br`, via URL pública. **Dependência externa provisória**; validar cobertura e atualização dos limites antes da publicação. Não se presume que a malha seja oficial do IBGE.

## Como testar
1. Baixar o HTML da branch `auditoria-tecnica-2026-11`, preservando o nome `index.html`.
2. Abrir no navegador com conexão à internet. Leaflet, PapaParse, mapa-base OSM e GeoJSON são carregados externamente.
3. Selecionar o CSV de qualidade já gerado pela auditoria nacional. O CSV é processado localmente no navegador, sem envio a um servidor.
4. Selecionar cultura, UF e alternar entre valor da produção e status da auditoria.
5. Clicar no município para ver código IBGE, valores BD e SIDRA, diferença e classificação.

**Atenção:** esta interface é um protótipo independente. Não está publicada no GitHub Pages e não altera a página principal. O carregamento externo de geometrias não foi validado em todos os navegadores; se falhar, os controles de dados permanecem disponíveis, mas o mapa municipal não será desenhado.

## Critérios para publicação
- Hospedar geometria geográfica auditada com licença e proveniência verificadas, preferencialmente derivada de fonte oficial IBGE.
- Validar que os códigos de município do GeoJSON correspondem às chaves IBGE de sete dígitos; municípios sem geometria devem ser contabilizados.
- Substituir a seleção manual de CSV por dados estáticos versionados e compactados, sem sacrificar proveniência.
- Implementar testes de integração de navegador e verificar desempenho para cerca de 5,6 mil polígonos.
- Revisar contraste, acessibilidade, filtros e classificações da legenda.
- Confirmar autorização antes de qualquer merge na `main` ou publicação do site.
