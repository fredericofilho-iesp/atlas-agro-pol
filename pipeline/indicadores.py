"""Indicadores da Fase 1 e exportação para o site.

Entradas: data/interim/*.csv.gz (geradas por pipeline.coletar)
Saídas:
  data/processed/indicadores_municipio_ano.csv.gz  série completa por município
  data/processed/indicadores_uf_ano.csv            agregados por UF e Brasil
  data/processed/indicadores_municipio_atual.csv   retrato mais recente
  site/data/municipios.json                        versão compacta para o mapa
  site/data/meta.json                              anos de referência e notas

Conceitos:
  VBP  = valor bruto da produção = PAM + PPM (origem animal) + PEVS (extração
         e silvicultura). Não inclui o abate de animais, que não está na PPM.
  VAB agro = valor adicionado bruto da agropecuária (PIB dos Municípios; com
         abertura setorial só até 2021).
  Valores reais em R$ do ano-base do IPCA (média anual).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import config
from .sidra import normalizar

log = logging.getLogger(__name__)

COMPONENTES_VBP = {
    "pam": "vbp_lavouras",
    "ppm_origem_animal": "vbp_origem_animal",
    "pevs_extracao": "vbp_extracao",
    "pevs_silvicultura": "vbp_silvicultura",
}


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------
def ler(nome: str) -> pd.DataFrame:
    caminho = config.INTERIM / f"{nome}.csv.gz"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe. Rode antes: python -m pipeline.coletar --fontes {nome}")
    return pd.read_csv(caminho, dtype={"categoria_codigo": "string"})


def _eh_total(serie: pd.Series) -> pd.Series:
    return serie.fillna("").map(lambda s: normalizar(str(s)) == "total")


def total_por_municipio(df: pd.DataFrame, medida: str = "valor_mil_reais") -> pd.DataFrame:
    """Valor total por município e ano.

    Usa a categoria "Total" quando a tabela a tem; senão soma as categorias.
    """
    d = df[df["medida"] == medida]
    if d.empty:
        return pd.DataFrame(columns=["codigo", "ano", "valor"])
    tot = _eh_total(d["categoria"]) if "categoria" in d else pd.Series(False, index=d.index)
    if tot.any():
        d = d[tot]
    else:
        d = d[d["categoria"].notna()] if "categoria" in d else d
    return (d.groupby(["codigo", "ano"])["valor"].sum(min_count=1).reset_index())


# ---------------------------------------------------------------------------
# Deflação
# ---------------------------------------------------------------------------
def fatores_ipca(ipca_anual: pd.DataFrame, ano_base: int | None = None) -> tuple[pd.Series, int]:
    idx = ipca_anual.set_index("ano")["indice_medio"]
    base = ano_base or int(idx.index.max())
    if base not in idx.index:
        raise ValueError(f"Ano-base {base} fora da série do IPCA ({idx.index.min()}–{idx.index.max()})")
    return idx[base] / idx, base


# ---------------------------------------------------------------------------
# Painel município x ano
# ---------------------------------------------------------------------------
def montar_painel(mun: pd.DataFrame, pib: pd.DataFrame, componentes: dict[str, pd.DataFrame],
                  fatores: pd.Series) -> pd.DataFrame:
    # VBP por componente
    painel = None
    for fonte, coluna in COMPONENTES_VBP.items():
        if fonte not in componentes:
            continue
        t = total_por_municipio(componentes[fonte]).rename(columns={"valor": coluna})
        painel = t if painel is None else painel.merge(t, on=["codigo", "ano"], how="outer")
    cols_vbp = [c for c in COMPONENTES_VBP.values() if c in painel]
    painel["vbp"] = painel[cols_vbp].sum(axis=1, min_count=1)

    # PIB e VAB
    pib_l = (pib.pivot_table(index=["codigo", "ano"], columns="medida", values="valor", aggfunc="first")
             .reset_index())
    painel = painel.merge(pib_l, on=["codigo", "ano"], how="outer")
    for c in ("pib", "vab_total", "vab_agro"):
        if c not in painel:
            painel[c] = np.nan

    painel = painel.merge(mun[["codigo", "nome", "uf", "uf_codigo", "regiao"]], on="codigo", how="left")

    # Valores reais (mil R$ do ano-base)
    painel["fator_ipca"] = painel["ano"].map(fatores)
    for c in [*cols_vbp, "vbp", "pib", "vab_total", "vab_agro"]:
        painel[f"{c}_real"] = painel[c] * painel["fator_ipca"]

    # Pesos no próprio município
    painel["part_vab_agro"] = painel["vab_agro"] / painel["vab_total"]
    painel["vbp_sobre_pib"] = painel["vbp"] / painel["pib"]

    # Pesos no estado e no país
    for c in ("vbp", "vab_agro"):
        uf_tot = painel.groupby(["uf", "ano"])[c].transform("sum")
        br_tot = painel.groupby("ano")[c].transform("sum")
        painel[f"part_uf_{c}"] = painel[c] / uf_tot.replace(0, np.nan)
        painel[f"part_br_{c}"] = painel[c] / br_tot.replace(0, np.nan)
        painel[f"rank_br_{c}"] = painel.groupby("ano")[c].rank(ascending=False, method="min")
        painel[f"rank_uf_{c}"] = painel.groupby(["uf", "ano"])[c].rank(ascending=False, method="min")

    return painel.sort_values(["codigo", "ano"]).reset_index(drop=True)


def agregados_uf(painel: pd.DataFrame) -> pd.DataFrame:
    soma = ["vbp", "vbp_real", "pib", "pib_real", "vab_total", "vab_agro", "vab_agro_real"]
    uf = painel.groupby(["uf", "ano"])[soma].sum(min_count=1).reset_index()
    br = painel.groupby("ano")[soma].sum(min_count=1).reset_index().assign(uf="BR")
    out = pd.concat([uf, br], ignore_index=True)
    out["part_vab_agro"] = out["vab_agro"] / out["vab_total"]
    out["vbp_sobre_pib"] = out["vbp"] / out["pib"]
    return out


# ---------------------------------------------------------------------------
# Retrato atual
# ---------------------------------------------------------------------------
def _ultimo(painel: pd.DataFrame, coluna: str) -> pd.DataFrame:
    d = painel[painel[coluna].notna()]
    return d.loc[d.groupby("codigo")["ano"].idxmax()].set_index("codigo")


def principais_produtos(pam: pd.DataFrame, ano: int, n: int = 3) -> pd.Series:
    d = pam[(pam["medida"] == "valor_mil_reais") & (pam["ano"] == ano) & ~_eh_total(pam["categoria"])]
    d = d[d["valor"] > 0].sort_values(["codigo", "valor"], ascending=[True, False])
    return d.groupby("codigo")["categoria"].apply(lambda s: list(s.head(n)))


def efetivo_bovino(rebanhos: pd.DataFrame, ano: int) -> pd.Series:
    d = rebanhos[(rebanhos["ano"] == ano) & rebanhos["categoria"].fillna("").map(
        lambda s: normalizar(s).startswith("bovino"))]
    return d.groupby("codigo")["valor"].sum(min_count=1)


def retrato_atual(painel: pd.DataFrame, pam: pd.DataFrame | None,
                  rebanhos: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    base = painel.drop_duplicates("codigo").set_index("codigo")[["nome", "uf", "regiao"]]

    ult_vbp = _ultimo(painel, "vbp")
    ult_vab = _ultimo(painel, "vab_agro")
    ult_pib = _ultimo(painel, "pib")
    comum = painel[painel["vbp"].notna() & painel["pib"].notna()]
    ult_comum = comum.loc[comum.groupby("codigo")["ano"].idxmax()].set_index("codigo")

    anos = {
        "vbp": int(ult_vbp["ano"].max()) if len(ult_vbp) else None,
        "vab_agro": int(ult_vab["ano"].max()) if len(ult_vab) else None,
        "pib": int(ult_pib["ano"].max()) if len(ult_pib) else None,
        "vbp_sobre_pib": int(ult_comum["ano"].max()) if len(ult_comum) else None,
    }

    out = base.copy()
    out["vbp_real"] = ult_vbp["vbp_real"]
    out["part_uf_vbp"] = ult_vbp["part_uf_vbp"]
    out["part_br_vbp"] = ult_vbp["part_br_vbp"]
    out["rank_br_vbp"] = ult_vbp["rank_br_vbp"]
    out["vab_agro_real"] = ult_vab["vab_agro_real"]
    out["part_vab_agro"] = ult_vab["part_vab_agro"]
    out["part_uf_vab_agro"] = ult_vab["part_uf_vab_agro"]
    out["part_br_vab_agro"] = ult_vab["part_br_vab_agro"]
    out["vbp_sobre_pib"] = ult_comum["vbp_sobre_pib"]

    # variação real do VBP em 10 anos
    if anos["vbp"]:
        a1, a0 = anos["vbp"], anos["vbp"] - 10
        v = painel.pivot_table(index="codigo", columns="ano", values="vbp_real")
        if a0 in v and a1 in v:
            out["vbp_var_10a"] = v[a1] / v[a0].replace(0, np.nan) - 1
            anos["vbp_var_10a"] = [a0, a1]

    if pam is not None and anos["vbp"]:
        out["principais_lavouras"] = principais_produtos(pam, anos["vbp"])
    if rebanhos is not None and anos["vbp"]:
        out["bovinos_cabecas"] = efetivo_bovino(rebanhos, anos["vbp"])
    return out.reset_index(), anos


# ---------------------------------------------------------------------------
# Exportação para o site
# ---------------------------------------------------------------------------
def _arred(x, casas):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return None
    return round(float(x), casas)


def exportar_site(atual: pd.DataFrame, anos: dict, ano_base: int) -> None:
    registros = {}
    for r in atual.itertuples(index=False):
        d = r._asdict()
        registros[str(d["codigo"])] = {
            "n": d["nome"], "uf": d["uf"],
            "vbp": _arred(d.get("vbp_real"), 0),          # mil R$ (ano-base)
            "vbp_uf": _arred(d.get("part_uf_vbp"), 5),
            "vbp_br": _arred(d.get("part_br_vbp"), 6),
            "vbp_rank": None if pd.isna(d.get("rank_br_vbp")) else int(d["rank_br_vbp"]),
            "vbp_pib": _arred(d.get("vbp_sobre_pib"), 4),
            "vab_agro": _arred(d.get("vab_agro_real"), 0),
            "vab_part": _arred(d.get("part_vab_agro"), 4),
            "vab_uf": _arred(d.get("part_uf_vab_agro"), 5),
            "vab_br": _arred(d.get("part_br_vab_agro"), 6),
            "var10": _arred(d.get("vbp_var_10a"), 4),
            "lav": d.get("principais_lavouras") if isinstance(d.get("principais_lavouras"), list) else [],
            "bov": _arred(d.get("bovinos_cabecas"), 0),
        }
    (config.SITE_DATA / "municipios.json").write_text(
        json.dumps(registros, ensure_ascii=False, separators=(",", ":")))
    meta = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ano_base_ipca": ano_base,
        "anos_referencia": anos,
        "unidades": {"vbp": "mil R$ (IPCA, média anual do ano-base)",
                     "vab_agro": "mil R$ (IPCA, média anual do ano-base)"},
        "notas": [
            "VBP = PAM + PPM (origem animal) + PEVS. Não inclui abate de animais.",
            "VAB da agropecuária por município só existe até 2021 (IBGE).",
            "vbp_pib é uma proporção aproximada de peso econômico, não o VAB.",
        ],
    }
    (config.SITE_DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    log.info("site/data atualizado: %d municípios", len(registros))


# ---------------------------------------------------------------------------
def main() -> None:
    mun = ler("municipios")
    fatores, base = fatores_ipca(ler("ipca_anual"), config.ANO_BASE_IPCA)
    componentes = {}
    for f in COMPONENTES_VBP:
        try:
            componentes[f] = ler(f)
        except FileNotFoundError as e:
            log.warning("%s — componente ignorado no VBP", e)
    pib = ler("pib")
    painel = montar_painel(mun, pib, componentes, fatores)
    painel.to_csv(config.PROCESSED / "indicadores_municipio_ano.csv.gz", index=False, compression="gzip")
    agregados_uf(painel).to_csv(config.PROCESSED / "indicadores_uf_ano.csv", index=False)

    try:
        rebanhos = ler("ppm_rebanhos")
    except FileNotFoundError:
        rebanhos = None
    atual, anos = retrato_atual(painel, componentes.get("pam"), rebanhos)
    atual.to_csv(config.PROCESSED / "indicadores_municipio_atual.csv", index=False)
    exportar_site(atual, anos, base)
    log.info("anos de referência: %s | ano-base IPCA: %s", anos, base)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    main()
