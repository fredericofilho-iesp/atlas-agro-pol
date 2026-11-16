# Atlas Agrário e Político do Brasil

Mapa interativo da força do agro na economia e na política, município a município.

Este repositório contém, por enquanto, o **pipeline de dados da Fase 1** (núcleo agrário nacional):
produção, valor da produção, peso econômico da agropecuária e perfil produtivo dos 5.570 municípios,
com valores corrigidos pelo IPCA. O inventário completo de fontes está no documento
"Atlas Agrário e Político do Brasil — Inventário de Dados".

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-geo.txt   # opcional: só para gerar a malha a partir do shapefile
pytest -q                 # testes offline (API do IBGE simulada)
python -m pipeline        # coleta + indicadores + exportação para o site
```

A primeira coleta completa leva algumas horas: são milhares de consultas ao SIDRA, fatiadas por UF,
variável, ano e produto. As respostas ficam em cache em `data/raw/`, então rodar de novo só baixa o
que é novo. Para rodar por partes:

```bash
python -m pipeline.coletar --fontes municipios malha ipca pib
python -m pipeline.coletar --fontes pam
python -m pipeline.indicadores
```

Para conferir as variáveis de uma tabela do SIDRA:

```bash
python -m pipeline.sidra --listar 5457
```

## Acesso ao IBGE de fora do Brasil

O pipeline usa só o **apisidra.ibge.gov.br** (dados e descrição das tabelas) e o **geoftp.ibge.gov.br**
(malha), que responderam de fora do Brasil em nov/2026. A API **servicodados.ibge.gov.br**
(metadados, localidades e malhas) recusa conexões estrangeiras e só é tentada para a malha, com o
geoftp como alternativa. Se o apisidra também recusar a sua rede, o pipeline para logo no início
com uma mensagem clara.

## Atualização automática (GitHub Actions)

O workflow `.github/workflows/atualizar-dados.yml` roda todo dia 3 do mês (ou pelo botão
**Run workflow** na aba Actions), refaz os indicadores e publica `data/processed/` e `site/data/`
no repositório. Para ele poder gravar: **Settings → Actions → General → Workflow permissions →
Read and write permissions**.

## Estrutura

```
pipeline/
  config.py        anos, tabelas, nomes das variáveis (edite aqui)
  sidra.py         cliente das APIs do IBGE (metadados, fatiamento, cache, símbolos)
  coletar.py       municípios, malha, IPCA, PIB, PAM, PPM, PEVS -> data/interim/
  indicadores.py   painel município x ano, agregados por UF/Brasil, retrato atual, JSON do site
tests/             testes com API simulada
data/processed/    indicadores finais (versionados)
site/data/         arquivos leves para o mapa (versionados)
```

## Fontes da Fase 1

| Fonte | Tabela SIDRA | Uso |
| --- | --- | --- |
| Municípios | apisidra (tabela 5938, último ano) | Código, nome, UF e região |
| Malha | API de malhas do IBGE ou shapefile 2025 do geoftp | Mapa |
| IPCA | 1737 | Deflator (média anual do número-índice; ano-base = último ano completo) |
| PIB dos Municípios | 5938 | PIB, VAB total, VAB da agropecuária |
| PAM | 5457 | Área, quantidade e valor das lavouras, por produto |
| PPM | 3939, 74 | Rebanhos; produção e valor de origem animal |
| PEVS | 289, 291 | Valor da extração vegetal e da silvicultura |

As variáveis são localizadas **pelo nome** na página de descrição de cada tabela
(`apisidra.ibge.gov.br/desctabapi.aspx?c=<tabela>`; ver `config.TABELAS`). Se o IBGE
renomear uma variável, o erro lista as variáveis disponíveis para ajustar o config.

## Indicadores

| Campo | Significado |
| --- | --- |
| `vbp`, `vbp_real` | Valor bruto da produção = PAM + PPM (origem animal) + PEVS, em mil R$ (nominal / IPCA) |
| `vab_agro`, `part_vab_agro` | VAB da agropecuária e sua participação no VAB do município |
| `vbp_sobre_pib` | VBP / PIB: proporção aproximada do peso do agro (anos sem VAB setorial) |
| `part_uf_*`, `part_br_*` | Participação do município no total do estado e do país |
| `rank_br_*`, `rank_uf_*` | Posição do município no país e no estado |
| `vbp_var_10a` | Variação real do VBP em 10 anos |

## Limitações conhecidas

- **VAB da agropecuária por município só existe até 2021.** O IBGE publicou o PIB dos Municípios
  2022–2023 sem abertura setorial e fará o mesmo com 2024–2025 (em 2027). Para os anos recentes,
  o atlas usa `vbp_sobre_pib`, que é uma aproximação e não o VAB. O PIB total de 2022–2023 está
  na própria tabela 5938.
- **O último ano da PAM, PPM e PEVS é preliminar** e pode ser revisto pelo IBGE.
- **O VBP subestima a pecuária de corte**: a PPM traz rebanhos (estoque), leite, ovos, mel e lã,
  mas não o valor do abate.
- **Sigilo**: células "X" do IBGE viram ausência, nunca zero; ficam listadas em
  `data/interim/<fonte>_sigilo.csv.gz`.
- **Tabelas por produto** guardam só valores positivos e as linhas "Total", para conter o tamanho.

## Próximas etapas

1. Censo Agropecuário 2017: perfil do produtor (6776, 6778), cooperação (6851) e tecnologia
   (6869–6873).
2. Crédito rural (Banco Central) e MapBiomas Coleção 11.
3. Fase 2: camada política (TSE 2018–2026, FPA).
4. Front-end do mapa em `site/`.
