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

URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
             "?formato=application/json&qualidade=minima&intrarregiao=municipio")
URL_MALHA_GEOFTP = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
                    "malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip")

COLUNAS = ["codigo", "territorio", "periodo", "medida", "categoria_codigo", "categoria",
           "unidade", "valor", "tabela"]


def _salvar(df: pd.DataFrame, nome: str) -> None:
    destino = config.INTERIM / f"{nome}.csv.gz"
    df.to_csv(destino, index=False, compression="gzip")
    log.info("salvo %s (%d linhas)", destino.relative_to(config.RAIZ), len(df))


# ---------------------------------------------------------------------------
# Municípios e malha
# ---------------------------------------------------------------------------
REGIOES = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}


def municipios() -> pd.DataFrame:
    """Lista de municípios a partir do próprio apisidra (PIB do último ano).

    O apisidra devolve o nome como "Sorriso - MT"; UF e região saem do código.
    """
    meta = sidra.metadados(5938)
    var = meta.variavel_id(["produto interno bruto", "precos correntes"], ["per capita"])
    df = sidra.baixar(5938, "n6", [var], [meta.periodos[-1]])
    nome_uf = df["territorio"].str.rsplit(" - ", n=1, expand=True)
    out = pd.DataFrame({
        "codigo": df["codigo"].astype(int),
        "nome": nome_uf[0],
        "uf": nome_uf[1],
    })
    out["uf_codigo"] = out["codigo"] // 100_000
    out["regiao"] = (out["codigo"] // 1_000_000).map(REGIOES)
    out = out.sort_values("codigo")[["codigo", "nome", "uf_codigo", "uf", "regiao"]]
    _salvar(out, "municipios")
    return out


def malha() -> None:
    """Malha municipal leve para o site.

    1ª tentativa: API de malhas do IBGE (TopoJSON pronto).
    2ª tentativa: shapefile do geoftp, simplificado com geopandas (opcional).
    """
    try:
        topo = sidra._get_json(URL_MALHA, timeout=120)
        destino = config.SITE_DATA / "malha_municipios.topojson"
        destino.write_text(json.dumps(topo, separators=(",", ":")))
    except Exception as exc:  # noqa: BLE001
        log.warning("API de malhas indisponível (%s); usando o shapefile do geoftp", exc)
        destino = _malha_geoftp()
        if destino is None:
            return
    log.info("malha salva em %s (%.1f MB)", destino.relative_to(config.RAIZ),
             destino.stat().st_size / 1e6)


def _malha_geoftp(tolerancia: float = 0.005):
    try:
        import geopandas as gpd  # dependência opcional
    except ImportError:
        log.warning("geopandas não instalado: pule a malha ou rode "
                    "`pip install -r requirements-geo.txt` e repita --fontes malha")
        return None
    zip_local = config.RAW / "geoftp" / URL_MALHA_GEOFTP.rsplit("/", 1)[-1]
    zip_local.parent.mkdir(parents=True, exist_ok=True)
    if not zip_local.exists():
        log.info("baixando %s (~230 MB)", URL_MALHA_GEOFTP)
        with sidra.SESSAO.get(URL_MALHA_GEOFTP, stream=True, timeout=600) as r:
            r.raise_for_status()
            with open(zip_local, "wb") as f:
                for bloco in r.iter_content(1 << 20):
                    f.write(bloco)
    g = gpd.read_file(f"zip://{zip_local}")
    col_cod = next(c for c in g.columns if c.upper().startswith("CD_MUN"))
    g = g[[col_cod, "geometry"]].rename(columns={col_cod: "codigo"}).to_crs(4326)
    g["codigo"] = g["codigo"].astype(int)
    g["geometry"] = g.geometry.simplify(tolerancia, preserve_topology=True)
    destino = config.SITE_DATA / "malha_municipios.geojson"
    destino.write_text(g.to_json(drop_id=True, to_wgs84=True))
    return destino


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
    sidra.testar_conexao()
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
