"""Testes offline do pipeline, com a API do IBGE simulada (tests/fake_ibge.py)."""
from __future__ import annotations

import json
import math

import pandas as pd
import pytest

from pipeline import coletar, config, indicadores, sidra
from tests import fake_ibge


@pytest.fixture()
def ambiente(tmp_path, monkeypatch):
    """Diretórios temporários + API falsa + só RJ e MT + limite pequeno (força fatiamento)."""
    for nome in ("RAW", "INTERIM", "PROCESSED", "SITE_DATA"):
        p = tmp_path / nome.lower()
        p.mkdir()
        monkeypatch.setattr(config, nome, p)
    monkeypatch.setattr(config, "RAIZ", tmp_path)
    monkeypatch.setattr(config, "UFS", {33: "RJ", 51: "MT"})
    monkeypatch.setattr(config, "ANO_INICIO", 2014)
    monkeypatch.setattr(config, "ANO_BASE_IPCA", None)
    monkeypatch.setattr(config, "PAUSA_ENTRE_REQUISICOES", 0)
    monkeypatch.setattr(config, "MAX_VALORES_POR_REQUISICAO", 2000)
    urls = []

    def falso(url, timeout=180):
        urls.append(url)
        return fake_ibge.resposta(url)

    monkeypatch.setattr(sidra, "_get_json", falso)
    return {"urls": urls, "tmp": tmp_path}


# ---------------------------------------------------------------------------
# Unidades
# ---------------------------------------------------------------------------
def test_simbolos_do_ibge():
    assert sidra.para_numero("-") == 0.0
    assert math.isnan(sidra.para_numero("X"))
    assert math.isnan(sidra.para_numero("..."))
    assert sidra.para_numero("12.5") == 12.5


def test_normalizar_ignora_acentos():
    assert sidra.normalizar("  Área  Colhida ") == "area colhida"


def test_variavel_por_nome_exclui_percentual():
    meta = sidra.Metadados(5457, {k: v for k, v in fake_ibge.META[5457].items() if k != "periodos"}, [])
    assert meta.variavel_id(["valor da producao"], ["percentual"]) == 215
    with pytest.raises(LookupError):
        meta.variavel_id(["valor da producao"])  # ambígua sem o "exclui"


def test_fatiar_periodos():
    blocos = sidra.fatiar_periodos([str(a) for a in range(2000, 2010)], 900, 2000)
    assert [len(b) for b in blocos] == [2, 2, 2, 2, 2]


# ---------------------------------------------------------------------------
# Ponta a ponta
# ---------------------------------------------------------------------------
def test_pipeline_completo(ambiente):
    coletar.main([])
    indicadores.main()

    # A PAM teve de ser fatiada por produto (limite 2000 / 900 municípios = 2 categorias)
    pam_urls = [u for u in ambiente["urls"] if "/t/5457/" in u]
    assert any("c782/40471,40124" in u for u in pam_urls)
    assert not any("c782/all" in u for u in pam_urls)

    # IPCA: só anos completos (2026 tem 9 meses)
    ipca = pd.read_csv(config.INTERIM / "ipca_anual.csv.gz")
    assert ipca["ano"].max() == 2025

    # Sigilo ("X") registrado à parte, não como zero
    sig = pd.read_csv(config.INTERIM / "pam_sigilo.csv.gz")
    assert ((sig["codigo"] == 5103403) & (sig["ano"] == 2020)).any()

    painel = pd.read_csv(config.PROCESSED / "indicadores_municipio_ano.csv.gz")
    sorriso = painel[(painel["codigo"] == 5107925)].set_index("ano")

    # VBP = lavouras + origem animal + extração + silvicultura
    a = sorriso.loc[2025]
    assert a["vbp"] == pytest.approx(a["vbp_lavouras"] + a["vbp_origem_animal"] + a["vbp_silvicultura"], rel=1e-9)

    # deflação: no ano-base, valor real = nominal
    assert a["vbp_real"] == pytest.approx(a["vbp"])
    assert sorriso.loc[2015, "vbp_real"] > sorriso.loc[2015, "vbp"]

    # participações no estado e no país somam 1
    ano = painel[painel["ano"] == 2025]
    assert ano["part_br_vbp"].sum() == pytest.approx(1.0)
    assert ano.groupby("uf")["part_uf_vbp"].sum().tolist() == pytest.approx([1.0, 1.0])

    # VAB da agropecuária só até 2021; PIB até 2023
    assert sorriso["vab_agro"].dropna().index.max() == 2021
    assert sorriso["pib"].dropna().index.max() == 2023
    assert sorriso.loc[2021, "part_vab_agro"] == pytest.approx(0.45, rel=1e-3)

    # agregados por UF e Brasil
    uf = pd.read_csv(config.PROCESSED / "indicadores_uf_ano.csv")
    assert {"RJ", "MT", "BR"} <= set(uf["uf"])

    # site
    site = json.loads((config.SITE_DATA / "municipios.json").read_text())
    s = site["5107925"]
    assert s["lav"][0].startswith("Soja")
    assert s["vbp_rank"] == 1
    assert s["bov"] > 0
    assert s["vab_part"] == pytest.approx(0.45, rel=1e-3)
    meta = json.loads((config.SITE_DATA / "meta.json").read_text())
    assert meta["ano_base_ipca"] == 2025
    assert meta["anos_referencia"]["vab_agro"] == 2021
    assert meta["anos_referencia"]["vbp_sobre_pib"] == 2023
    assert (config.SITE_DATA / "malha_municipios.topojson").exists()


def test_cache_evita_novo_download(ambiente):
    coletar.main(["--fontes", "pib"])
    n1 = len([u for u in ambiente["urls"] if "apisidra" in u])
    coletar.main(["--fontes", "pib"])
    n2 = len([u for u in ambiente["urls"] if "apisidra" in u])
    assert n1 > 0 and n2 == n1
