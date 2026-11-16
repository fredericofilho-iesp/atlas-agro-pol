"""Coleta da Fase 1: municípios, malha, IPCA, PIB, PAM, PPM e PEVS.

Cada fonte vira um arquivo arrumado em data/interim/<fonte>.csv.gz.

    python -m pipeline.coletar                 # tudo
    python -m pipeline.coletar --fontes pib pam
    python -m pipeline.coletar --sem-cache     # força novo download
"""
from __future__ import annotations

import argparse
import json
import logging

import pandas as pd

from . import config, sidra

log = logging.getLogger(__name__)

URL_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
             "?formato=application/json&qualidade=minima&intrarregiao=municipio")

COLUNAS = ["codigo", "territorio", "periodo", "medida", "categoria_codigo", "categoria",
           "unidade", "valor", "tabela"]


def _salvar(df: pd.DataFrame, nome: str) -> None:
    destino = config.INTERIM / f"{nome}.csv.gz"
    df.to_csv(destino, index=False, compression="gzip")
    log.info("salvo %s (%d linhas)", destino.relative_to(config.RAIZ), len(df))


# ---------------------------------------------------------------------------
# Municípios e malha
# ---------------------------------------------------------------------------
def municipios() -> pd.DataFrame:
    dados = sidra._get_json(URL_MUNICIPIOS)
    df = pd.DataFrame(dados)

    def col(trecho: str) -> str:
        return next(c for c in df.columns if c.lower() == trecho.lower())

    out = pd.DataFrame({
        "codigo": df[col("municipio-id")].astype(int),
        "nome": df[col("municipio-nome")],
        "uf_codigo": df[col("UF-id")].astype(int),
        "uf": df[col("UF-sigla")],
        "regiao": df[col("regiao-nome")],
    }).sort_values("codigo")
    _salvar(out, "municipios")
    return out


def malha() -> None:
    """Malha municipal simplificada (TopoJSON) direto da API de malhas do IBGE."""
    topo = sidra._get_json(URL_MALHA, timeout=600)
    destino = config.SITE_DATA / "malha_municipios.topojson"
    destino.write_text(json.dumps(topo, separators=(",", ":")))
    log.info("malha salva em %s (%.1f MB)", destino.relative_to(config.RAIZ),
             destino.stat().st_size / 1e6)


# ---------------------------------------------------------------------------
# Fontes do SIDRA
# ---------------------------------------------------------------------------
def ipca(usar_cache: bool = True) -> pd.DataFrame:
    """IPCA número-índice mensal -> média anual, só anos completos (12 meses)."""
    df = sidra.coletar("ipca", ano_inicio=config.ANO_INICIO, usar_cache=usar_cache)
    df["ano"] = df["periodo"].astype(str).str[:4].astype(int)
    anual = (df.groupby("ano")["valor"].agg(["mean", "count"]).reset_index()
             .query("count == 12").rename(columns={"mean": "indice_medio"})
             [["ano", "indice_medio"]])
    _salvar(anual, "ipca_anual")
    return anual


def fonte_sidra(nome: str, usar_cache: bool = True) -> pd.DataFrame:
    df = sidra.coletar(nome, usar_cache=usar_cache)
    for c in ("categoria_codigo", "categoria"):
        if c not in df:
            df[c] = pd.NA
    df = df[COLUNAS].rename(columns={"periodo": "ano"})
    df["ano"] = df["ano"].astype(str).str[:4].astype(int)
    df["codigo"] = df["codigo"].astype(int)
    if df["categoria"].notna().any():
        # Tabelas por produto: guarda só valores positivos e as linhas "Total".
        # Ausência = zero ("-") ou sigilo ("X"); o sigilo fica registrado à parte.
        total = df["categoria"].fillna("").map(lambda s: sidra.normalizar(str(s)) == "total")
        sigilo = df["valor"].isna() & ~total
        if sigilo.any():
            _salvar(df.loc[sigilo, ["codigo", "ano", "medida", "categoria"]], f"{nome}_sigilo")
        df = df[total | (df["valor"] > 0)]
    _salvar(df, nome)
    return df


FONTES_SIDRA = ["pib", "pam", "ppm_rebanhos", "ppm_origem_animal", "pevs_extracao",
                "pevs_silvicultura"]
TODAS = ["municipios", "malha", "ipca", *FONTES_SIDRA]


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fontes", nargs="+", choices=TODAS, default=TODAS)
    ap.add_argument("--sem-cache", action="store_true")
    args = ap.parse_args(argv)
    cache = not args.sem_cache
    for f in args.fontes:
        log.info("=== %s ===", f)
        if f == "municipios":
            municipios()
        elif f == "malha":
            malha()
        elif f == "ipca":
            ipca(cache)
        else:
            fonte_sidra(f, cache)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    main()
