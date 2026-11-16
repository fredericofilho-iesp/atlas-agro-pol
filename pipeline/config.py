"""Configuração central do pipeline do Atlas Agrário e Político do Brasil.

Tudo que muda com frequência (anos, tabelas, nomes de variáveis) fica aqui,
para que os scripts de coleta não precisem ser editados.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "data"
RAW = DATA / "raw"            # respostas brutas das APIs (cache)
INTERIM = DATA / "interim"    # tabelas arrumadas (tidy), uma por fonte
PROCESSED = DATA / "processed"  # indicadores finais
SITE_DATA = RAIZ / "site" / "data"  # arquivos leves consumidos pelo site

for _p in (RAW, INTERIM, PROCESSED, SITE_DATA):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Recorte temporal e moeda
# ---------------------------------------------------------------------------
# Primeiro ano das séries anuais (2006 = ano do penúltimo Censo Agro).
ANO_INICIO = int(os.getenv("ATLAS_ANO_INICIO", "2006"))

# Ano-base dos valores reais (IPCA, média anual). None = último ano completo
# disponível na tabela 1737 do SIDRA.
ANO_BASE_IPCA: int | None = (
    int(os.environ["ATLAS_ANO_BASE_IPCA"]) if os.getenv("ATLAS_ANO_BASE_IPCA") else None
)

# ---------------------------------------------------------------------------
# Unidades da Federação (código IBGE -> sigla)
# ---------------------------------------------------------------------------
UFS = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}

# ---------------------------------------------------------------------------
# Tabelas do SIDRA usadas na Fase 1
#
# As variáveis são localizadas pelo NOME (via metadados da API), e não por
# código fixo: "inclui" = trechos que o nome deve conter; "exclui" = trechos que
# não pode conter. A comparação ignora acentos e maiúsculas. Se o IBGE mudar um
# código, o pipeline continua funcionando; se mudar um nome, o erro diz quais
# variáveis existem (ou rode: python -m pipeline.sidra --listar <tabela>).
# ---------------------------------------------------------------------------
TABELAS = {
    "ipca": {
        "tabela": 1737,
        "nivel": "n1",
        "variaveis": {
            "indice": {"inclui": ["numero-indice"], "exclui": []},
        },
    },
    "pib": {
        "tabela": 5938,
        "nivel": "n6",
        "variaveis": {
            "pib": {"inclui": ["produto interno bruto", "precos correntes"],
                    "exclui": ["per capita", "percentual"]},
            "vab_total": {"inclui": ["valor adicionado bruto", "total"],
                          "exclui": ["percentual", "participacao"]},
            "vab_agro": {"inclui": ["valor adicionado bruto", "agropecuaria"],
                         "exclui": ["percentual", "participacao"]},
        },
    },
    "pam": {
        "tabela": 5457,
        "nivel": "n6",
        "variaveis": {
            "area_plantada_ha": {"inclui": ["area plantada"], "exclui": ["percentual"]},
            "area_colhida_ha": {"inclui": ["area colhida"], "exclui": ["percentual"]},
            "quantidade": {"inclui": ["quantidade produzida"], "exclui": ["percentual"]},
            "valor_mil_reais": {"inclui": ["valor da producao"], "exclui": ["percentual"]},
        },
        # baixa todos os produtos (inclui a categoria "Total")
        "classificacao": {"todas_categorias": True},
    },
    "ppm_rebanhos": {
        "tabela": 3939,
        "nivel": "n6",
        "variaveis": {
            "efetivo_cabecas": {"inclui": ["efetivo"], "exclui": ["percentual"]},
        },
        "classificacao": {"todas_categorias": True},
    },
    "ppm_origem_animal": {
        "tabela": 74,
        "nivel": "n6",
        "variaveis": {
            "quantidade": {"inclui": ["producao de origem animal"], "exclui": ["percentual", "valor"]},
            "valor_mil_reais": {"inclui": ["valor da producao"], "exclui": ["percentual"]},
        },
        "classificacao": {"todas_categorias": True},
    },
    "pevs_extracao": {
        "tabela": 289,
        "nivel": "n6",
        "variaveis": {
            "valor_mil_reais": {"inclui": ["valor da producao"], "exclui": ["percentual"]},
        },
        "classificacao": {"todas_categorias": True},
    },
    "pevs_silvicultura": {
        "tabela": 291,
        "nivel": "n6",
        "variaveis": {
            "valor_mil_reais": {"inclui": ["valor da producao"], "exclui": ["percentual"]},
        },
        "classificacao": {"todas_categorias": True},
    },
}

# Limite prudente de valores por requisição à apisidra (o limite do IBGE é
# maior, mas requisições menores falham menos).
MAX_VALORES_POR_REQUISICAO = 40_000

# Pausa entre requisições, em segundos (gentileza com o servidor do IBGE).
PAUSA_ENTRE_REQUISICOES = float(os.getenv("ATLAS_PAUSA", "0.5"))
