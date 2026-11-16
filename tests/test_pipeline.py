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
    monkeypatch.setattr(sidra, "_get_texto", falso)
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


def test_variavel_por_nome_exclui_percentual_e_participacao():
    meta = sidra.Metadados(5457, {k: v for k, v in fake_ibge.META[5457].items() if k != "periodos"}, [])
    assert meta.variavel_id(["valor da producao"]) == 215
    pib = sidra.Metadados(5938, {k: v for k, v in fake_ibge.META[5938].items() if k != "periodos"}, [])
    assert pib.variavel_id(["produto interno bruto", "precos correntes"], ["per capita"]) == 37
    assert pib.variavel_id(["valor adicionado bruto", "agropecuaria"]) == 513
    with pytest.raises(LookupError):
        pib.variavel_id(["valor adicionado bruto"])  # ambígua


def test_descricao_real_do_ibge():
    """Página real desctabapi.aspx?c=74 (capturada em nov/2026)."""
    from pathlib import Path
    pagina = (Path(__file__).parent / "fixtures" / "desctabapi_74.html").read_text(encoding="utf-8")
    d = sidra.interpretar_desctabapi(pagina)
    assert d["nome"].startswith("Produção de origem animal")
    assert d["periodos"][0] == "1974" and d["periodos"][-1] == "2025"
    assert [v["id"] for v in d["variaveis"]] == [106, 215, 1000215]
    assert d["variaveis"][1]["nome"].startswith("Valor da produção (Mil Cruzeiros")
    assert "casas decimais" not in d["variaveis"][0]["nome"]
    c = d["classificacoes"][0]
    assert c["id"] == 80 and c["categorias"][0] == {"id": 0, "nome": "Total"}
    assert len(c["categorias"]) == 7
    meta = sidra.Metadados(74, d, d["periodos"])
    assert meta.variavel_id(["valor da producao"]) == 215


def test_resposta_com_dimensoes_nulas():
    cab = {"NC": "Nível Territorial (Código)", "NN": "Nível Territorial", "MC": "Unidade de Medida (Código)",
           "MN": "Unidade de Medida", "V": "Valor", "D1C": "Brasil (Código)", "D1N": "Brasil",
           "D2C": "Variável (Código)", "D2N": "Variável", "D3C": "Ano (Código)", "D3N": "Ano",
           "D4C": None, "D4N": None}
    linha = {"NC": "1", "NN": "Brasil", "MC": "40", "MN": "Mil Reais", "V": "9012142000", "D1C": "1",
             "D1N": "Brasil", "D2C": "37", "D2N": "PIB", "D3C": "2021", "D3N": "2021", "D4C": None, "D4N": None}
    df = sidra.interpretar_resposta([cab, linha])
    assert df.loc[0, "valor"] == 9012142000 and df.loc[0, "periodo"] == "2021"
    assert "categoria" not in df


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
    assert any("c782/0,40124" in u for u in pam_urls)
    assert not any("c782/all" in u for u in pam_urls)
    # PPM origem animal e PEVS: só a categoria Total (código 0)
    assert all("/c80/0/" in u for u in ambiente["urls"] if "/t/74/" in u and "/values/" in u)
    assert all("/c193/0/" in u for u in ambiente["urls"] if "/t/289/" in u and "/values/" in u)

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
    # PEVS hierárquica: o Total não soma "1 - Alimentícios" + "1.1 - Açaí" em dobro
    cuiaba = painel[painel["codigo"] == 5103403].set_index("ano")
    assert cuiaba.loc[2014, "vbp_extracao"] == pytest.approx(500)

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

    # municípios vêm do apisidra ("Nome - UF")
    mun = pd.read_csv(config.INTERIM / "municipios.csv.gz")
    assert set(mun["uf"]) == {"RJ", "MT"} and "Sorriso" in set(mun["nome"])
    assert mun.set_index("codigo").loc[5107925, "regiao"] == "Centro-Oeste"

    # Angra: café aparece uma vez só (Total), sem o subproduto Arábica
    assert site["3300100"]["lav"][0] == "Café (em grão) Total"
    assert not any("Arábica" in x for x in site["3300100"]["lav"])


def test_cache_evita_novo_download(ambiente):
    coletar.main(["--fontes", "pib"])
    n1 = len([u for u in ambiente["urls"] if "/values/" in u])
    coletar.main(["--fontes", "pib"])
    n2 = len([u for u in ambiente["urls"] if "/values/" in u])
    assert n1 > 0 and n2 == n1


def test_resposta_real_do_apisidra():
    """Trecho real de /values/t/5457/n6/in n3 51/v/215/p/2025/c782/0,40124 (nov/2026)."""
    from pathlib import Path
    dados = json.loads((Path(__file__).parent / "fixtures" / "values_5457_sorriso_2025.json").read_text(encoding="utf-8"))
    df = sidra.interpretar_resposta(dados)
    assert list(df["codigo"]) == ["5107925", "5107925"]
    assert list(df["categoria"]) == ["Total", "Soja (em grão)"]
    assert list(df["valor"]) == [8164615.0, 4050250.0]
    assert set(df["periodo"]) == {"2025"} and set(df["variavel_id"]) == {215}
    assert df["territorio"].iloc[0] == "Sorriso - MT"
