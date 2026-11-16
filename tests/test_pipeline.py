"""Testes offline do pipeline, com a API do IBGE simulada (tests/fake_ibge.py)."""
from __future__ import annotations

import json
import math

import pytest

from pipeline import coletar, config, indicadores, sidra, tabelas
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
    assert sidra.para_numero("X") is None
    assert sidra.para_numero("...") is None
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
    r = sidra.interpretar_resposta([cab, linha])[0]
    assert r["valor"] == 9012142000 and r["periodo"] == "2021"
    assert "categoria" not in r


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
    ipca = tabelas.ler(config.INTERIM / "ipca_anual.csv.gz")
    assert max(r["ano"] for r in ipca) == 2025

    # Sigilo ("X") registrado à parte, não como zero
    sig = tabelas.ler(config.INTERIM / "pam_sigilo.csv.gz")
    assert any(r["codigo"] == 5103403 and r["ano"] == 2020 for r in sig)

    painel = tabelas.ler(config.PROCESSED / "indicadores_municipio_ano.csv.gz")
    sorriso = {r["ano"]: r for r in painel if r["codigo"] == 5107925}

    # VBP = lavouras + origem animal + extração + silvicultura
    a = sorriso[2025]
    assert a["vbp"] == pytest.approx(a["vbp_lavouras"] + a["vbp_origem_animal"] + a["vbp_silvicultura"], rel=1e-9)
    # PEVS hierárquica: o Total não soma "1 - Alimentícios" + "1.1 - Açaí" em dobro
    cuiaba = {r["ano"]: r for r in painel if r["codigo"] == 5103403}
    assert cuiaba[2014]["vbp_extracao"] == pytest.approx(500)

    # deflação: no ano-base, valor real = nominal
    assert a["vbp_real"] == pytest.approx(a["vbp"])
    assert sorriso[2015]["vbp_real"] > sorriso[2015]["vbp"]

    # participações no estado e no país somam 1
    ano = [r for r in painel if r["ano"] == 2025]
    assert sum(r["part_br_vbp"] for r in ano) == pytest.approx(1.0)
    for sigla in ("RJ", "MT"):
        assert sum(r["part_uf_vbp"] for r in ano if r["uf"] == sigla) == pytest.approx(1.0)

    # VAB da agropecuária só até 2021; PIB até 2023
    assert max(k for k, r in sorriso.items() if r["vab_agro"] is not None) == 2021
    assert max(k for k, r in sorriso.items() if r["pib"] is not None) == 2023
    assert sorriso[2021]["part_vab_agro"] == pytest.approx(0.45, rel=1e-3)

    # agregados por UF e Brasil
    uf = tabelas.ler(config.PROCESSED / "indicadores_uf_ano.csv")
    assert {"RJ", "MT", "BR"} <= {r["uf"] for r in uf}

    # site
    site = json.loads((config.SITE_DATA / "municipios.json").read_text(encoding="utf-8"))
    s = site["5107925"]
    assert s["lav"][0].startswith("Soja")
    assert s["vbp_rank"] == 1
    assert s["bov"] > 0
    assert s["vab_part"] == pytest.approx(0.45, rel=1e-3)
    assert s["var10"] == pytest.approx(1.05 ** 10 / 1.004 ** 120 - 1, abs=1e-4)
    meta = json.loads((config.SITE_DATA / "meta.json").read_text(encoding="utf-8"))
    assert meta["ano_base_ipca"] == 2025
    assert meta["anos_referencia"]["vab_agro"] == 2021
    assert meta["anos_referencia"]["vbp_sobre_pib"] == 2023

    # municípios vêm do apisidra ("Nome - UF")
    mun = tabelas.ler(config.INTERIM / "municipios.csv.gz")
    assert {r["uf"] for r in mun} == {"RJ", "MT"} and "Sorriso" in {r["nome"] for r in mun}
    assert next(r for r in mun if r["codigo"] == 5107925)["regiao"] == "Centro-Oeste"

    # Angra: café aparece uma vez só (Total), sem o subproduto Arábica
    assert site["3300100"]["lav"][0] == "Café (em grão) Total"
    assert not any("Arábica" in x for x in site["3300100"]["lav"])

    # Rio de Janeiro não tem bovinos -> None, e o arquivo atual lista as lavouras com "|"
    assert site["3304557"]["bov"] is None
    atual = tabelas.ler(config.PROCESSED / "indicadores_municipio_atual.csv")
    assert next(r for r in atual if r["codigo"] == 5107925)["principais_lavouras"] == "Soja (em grão)|Milho (em grão)"


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
    linhas = sidra.interpretar_resposta(dados)
    assert [r["codigo"] for r in linhas] == ["5107925", "5107925"]
    assert [r["categoria"] for r in linhas] == ["Total", "Soja (em grão)"]
    assert [r["valor"] for r in linhas] == [8164615.0, 4050250.0]
    assert {r["periodo"] for r in linhas} == {"2025"} and {r["variavel_id"] for r in linhas} == {215}
    assert linhas[0]["territorio"] == "Sorriso - MT"


def test_sem_bibliotecas_compiladas(ambiente):
    """O pipeline não pode depender de pandas/numpy/requests (bloqueados por
    políticas de Controle de Aplicativos do Windows)."""
    import subprocess
    import sys
    codigo = ("import sys\n"
              "for m in ('pandas','numpy','requests','urllib3','charset_normalizer'):\n"
              "    sys.modules[m] = None  # qualquer import falha\n"
              "import pipeline.coletar, pipeline.indicadores, pipeline.sidra, pipeline.tabelas\n"
              "print('ok')\n")
    r = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True,
                       cwd=str(__import__("pathlib").Path(__file__).resolve().parents[1]))
    assert r.returncode == 0, r.stderr
