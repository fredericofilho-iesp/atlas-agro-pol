"""Indicadores da Fase 1 e exportação para o site (só biblioteca padrão).

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
from collections import defaultdict
from datetime import datetime, timezone

from . import config, tabelas
from .sidra import normalizar

log = logging.getLogger(__name__)

COMPONENTES_VBP = {
    "pam": "vbp_lavouras",
    "ppm_origem_animal": "vbp_origem_animal",
    "pevs_extracao": "vbp_extracao",
    "pevs_silvicultura": "vbp_silvicultura",
}
MONETARIAS = [*COMPONENTES_VBP.values(), "vbp", "pib", "vab_total", "vab_agro"]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def ler(nome: str) -> list[dict]:
    caminho = config.INTERIM / f"{nome}.csv.gz"
    if not caminho.exists():
        raise FileNotFoundError(f"{caminho} não existe. Rode antes: python -m pipeline.coletar --fontes {nome}")
    return tabelas.ler(caminho)


def soma(valores) -> float | None:
    """Soma ignorando ausências; None se todos ausentes (como min_count=1)."""
    vs = [v for v in valores if v is not None]
    return sum(vs) if vs else None


def div(a, b) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def mul(a, b) -> float | None:
    return None if a is None or b is None else a * b


def eh_total(nome) -> bool:
    return normalizar(str(nome or "")) == "total"


def rank_desc(valores: dict) -> dict:
    """Posição (1 = maior), empates com a menor posição; ausentes ficam sem posição."""
    vs = sorted((v for v in valores.values() if v is not None), reverse=True)
    pos = {}
    for i, v in enumerate(vs):
        pos.setdefault(v, i + 1)
    return {k: (pos[v] if v is not None else None) for k, v in valores.items()}


def total_por_municipio(linhas: list[dict], medida: str = "valor_mil_reais") -> dict:
    """{(codigo, ano): valor}. Usa a categoria "Total" se existir; senão soma as categorias."""
    d = [r for r in linhas if r.get("medida") == medida]
    if any(eh_total(r.get("categoria")) for r in d):
        d = [r for r in d if eh_total(r.get("categoria"))]
    grupos: dict[tuple, list] = defaultdict(list)
    for r in d:
        grupos[(r["codigo"], r["ano"])].append(r["valor"])
    return {k: soma(v) for k, v in grupos.items()}


# ---------------------------------------------------------------------------
# Deflação
# ---------------------------------------------------------------------------
def fatores_ipca(ipca_anual: list[dict], ano_base: int | None = None) -> tuple[dict, int]:
    idx = {r["ano"]: r["indice_medio"] for r in ipca_anual}
    base = ano_base or max(idx)
    if base not in idx:
        raise ValueError(f"Ano-base {base} fora da série do IPCA ({min(idx)}–{max(idx)})")
    return {a: idx[base] / v for a, v in idx.items()}, base


# ---------------------------------------------------------------------------
# Painel município x ano
# ---------------------------------------------------------------------------
def montar_painel(mun: list[dict], pib: list[dict], componentes: dict[str, list[dict]],
                  fatores: dict) -> list[dict]:
    linhas: dict[tuple, dict] = defaultdict(dict)
    for fonte, coluna in COMPONENTES_VBP.items():
        if fonte in componentes:
            for k, v in total_por_municipio(componentes[fonte]).items():
                linhas[k][coluna] = v
    for r in pib:
        if r.get("medida") in ("pib", "vab_total", "vab_agro"):
            linhas[(r["codigo"], r["ano"])].setdefault(r["medida"], r["valor"])

    info = {m["codigo"]: m for m in mun}
    painel = []
    for (codigo, ano), d in linhas.items():
        m = info.get(codigo, {})
        r = {"codigo": codigo, "ano": ano, "nome": m.get("nome"), "uf": m.get("uf"),
             "uf_codigo": m.get("uf_codigo"), "regiao": m.get("regiao")}
        for c in [*COMPONENTES_VBP.values(), "pib", "vab_total", "vab_agro"]:
            r[c] = d.get(c)
        r["vbp"] = soma(r[c] for c in COMPONENTES_VBP.values())
        r["fator_ipca"] = fatores.get(ano)
        for c in MONETARIAS:
            r[f"{c}_real"] = mul(r[c], r["fator_ipca"])
        r["part_vab_agro"] = div(r["vab_agro"], r["vab_total"])
        r["vbp_sobre_pib"] = div(r["vbp"], r["pib"])
        painel.append(r)

    # Pesos no estado e no país, e posições
    for c in ("vbp", "vab_agro"):
        tot_uf, tot_br = defaultdict(float), defaultdict(float)
        por_uf, por_br = defaultdict(dict), defaultdict(dict)
        for i, r in enumerate(painel):
            if r[c] is not None:
                tot_uf[(r["uf"], r["ano"])] += r[c]
                tot_br[r["ano"]] += r[c]
            por_uf[(r["uf"], r["ano"])][i] = r[c]
            por_br[r["ano"]][i] = r[c]
        for i, r in enumerate(painel):
            r[f"part_uf_{c}"] = div(r[c], tot_uf.get((r["uf"], r["ano"])))
            r[f"part_br_{c}"] = div(r[c], tot_br.get(r["ano"]))
        for grupos, chave in ((por_br, f"rank_br_{c}"), (por_uf, f"rank_uf_{c}")):
            for g in grupos.values():
                for i, pos in rank_desc(g).items():
                    painel[i][chave] = pos

    painel.sort(key=lambda r: (r["codigo"], r["ano"]))
    return painel


COLUNAS_PAINEL = ["codigo", "ano", "nome", "uf", "uf_codigo", "regiao",
                  *COMPONENTES_VBP.values(), "vbp", "pib", "vab_total", "vab_agro", "fator_ipca",
                  *[f"{c}_real" for c in MONETARIAS], "part_vab_agro", "vbp_sobre_pib",
                  "part_uf_vbp", "part_br_vbp", "rank_br_vbp", "rank_uf_vbp",
                  "part_uf_vab_agro", "part_br_vab_agro", "rank_br_vab_agro", "rank_uf_vab_agro"]


def agregados_uf(painel: list[dict]) -> list[dict]:
    campos = ["vbp", "vbp_real", "pib", "pib_real", "vab_total", "vab_agro", "vab_agro_real"]
    grupos: dict[tuple, list] = defaultdict(list)
    for r in painel:
        grupos[(r["uf"], r["ano"])].append(r)
        grupos[("BR", r["ano"])].append(r)
    out = []
    for (uf, ano), rs in sorted(grupos.items(), key=lambda kv: (kv[0][0] == "BR", str(kv[0][0]), kv[0][1])):
        d = {"uf": uf, "ano": ano, **{c: soma(r[c] for r in rs) for c in campos}}
        d["part_vab_agro"] = div(d["vab_agro"], d["vab_total"])
        d["vbp_sobre_pib"] = div(d["vbp"], d["pib"])
        out.append(d)
    return out


# ---------------------------------------------------------------------------
# Retrato atual
# ---------------------------------------------------------------------------
def _ultimo(painel: list[dict], *colunas: str) -> dict:
    """{codigo: linha do último ano em que todas as colunas existem}."""
    out = {}
    for r in painel:
        if all(r.get(c) is not None for c in colunas):
            if r["codigo"] not in out or r["ano"] > out[r["codigo"]]["ano"]:
                out[r["codigo"]] = r
    return out


def _sem_subprodutos(nomes: set[str]) -> set[str]:
    """Remove subdivisões de um produto que também aparece como "... Total".

    Ex.: na PAM existem "Café (em grão) Total", "... Arábica" e "... Canephora";
    fica só o Total do café.
    """
    prefixos = [normalizar(n)[: -len(" total")] for n in nomes if normalizar(n).endswith(" total")]
    return {n for n in nomes
            if not any(normalizar(n).startswith(p) and not normalizar(n).endswith(" total") for p in prefixos)}


def principais_produtos(pam: list[dict], ano: int, n: int = 3) -> dict:
    d = [r for r in pam if r.get("medida") == "valor_mil_reais" and r["ano"] == ano
         and not eh_total(r.get("categoria")) and (r["valor"] or 0) > 0]
    validos = _sem_subprodutos({r["categoria"] for r in d})
    por_mun: dict[int, list] = defaultdict(list)
    for r in d:
        if r["categoria"] in validos:
            por_mun[r["codigo"]].append((r["valor"], r["categoria"]))
    return {c: [nome for _, nome in sorted(v, key=lambda x: -x[0])[:n]] for c, v in por_mun.items()}


def efetivo_bovino(rebanhos: list[dict], ano: int) -> dict:
    grupos: dict[int, list] = defaultdict(list)
    for r in rebanhos:
        if r["ano"] == ano and normalizar(str(r.get("categoria") or "")).startswith("bovino"):
            grupos[r["codigo"]].append(r["valor"])
    return {c: soma(v) for c, v in grupos.items()}


def retrato_atual(painel: list[dict], pam: list[dict] | None, rebanhos: list[dict] | None):
    ult_vbp, ult_vab = _ultimo(painel, "vbp"), _ultimo(painel, "vab_agro")
    ult_pib, ult_comum = _ultimo(painel, "pib"), _ultimo(painel, "vbp", "pib")

    def maior_ano(d):
        return max((r["ano"] for r in d.values()), default=None)

    anos = {"vbp": maior_ano(ult_vbp), "vab_agro": maior_ano(ult_vab),
            "pib": maior_ano(ult_pib), "vbp_sobre_pib": maior_ano(ult_comum)}

    vbp_real = {(r["codigo"], r["ano"]): r["vbp_real"] for r in painel}
    a1 = anos["vbp"]
    a0 = a1 - 10 if a1 else None
    if a1 and any(k[1] == a0 for k in vbp_real):
        anos["vbp_var_10a"] = [a0, a1]
    lavouras = principais_produtos(pam, a1) if (pam is not None and a1) else {}
    bovinos = efetivo_bovino(rebanhos, a1) if (rebanhos is not None and a1) else {}

    out = []
    for codigo in sorted({r["codigo"] for r in painel}):
        v, b, c = ult_vbp.get(codigo, {}), ult_vab.get(codigo, {}), ult_comum.get(codigo, {})
        ref = v or b or c or next((r for r in painel if r["codigo"] == codigo), {})
        var10 = None
        if "vbp_var_10a" in anos:
            var10 = div(vbp_real.get((codigo, a1)), vbp_real.get((codigo, a0)))
            var10 = None if var10 is None else var10 - 1
        out.append({
            "codigo": codigo, "nome": ref.get("nome"), "uf": ref.get("uf"), "regiao": ref.get("regiao"),
            "vbp_real": v.get("vbp_real"), "part_uf_vbp": v.get("part_uf_vbp"),
            "part_br_vbp": v.get("part_br_vbp"), "rank_br_vbp": v.get("rank_br_vbp"),
            "vab_agro_real": b.get("vab_agro_real"), "part_vab_agro": b.get("part_vab_agro"),
            "part_uf_vab_agro": b.get("part_uf_vab_agro"), "part_br_vab_agro": b.get("part_br_vab_agro"),
            "vbp_sobre_pib": c.get("vbp_sobre_pib"), "vbp_var_10a": var10,
            "principais_lavouras": lavouras.get(codigo, []), "bovinos_cabecas": bovinos.get(codigo),
        })
    return out, anos


COLUNAS_ATUAL = ["codigo", "nome", "uf", "regiao", "vbp_real", "part_uf_vbp", "part_br_vbp", "rank_br_vbp",
                 "vab_agro_real", "part_vab_agro", "part_uf_vab_agro", "part_br_vab_agro",
                 "vbp_sobre_pib", "vbp_var_10a", "principais_lavouras", "bovinos_cabecas"]


# ---------------------------------------------------------------------------
# Exportação para o site
# ---------------------------------------------------------------------------
def _arred(x, casas):
    return None if x is None else round(float(x), casas)


def exportar_site(atual: list[dict], anos: dict, ano_base: int) -> None:
    registros = {}
    for d in atual:
        registros[str(d["codigo"])] = {
            "n": d["nome"], "uf": d["uf"],
            "vbp": _arred(d["vbp_real"], 0),          # mil R$ (ano-base)
            "vbp_uf": _arred(d["part_uf_vbp"], 5),
            "vbp_br": _arred(d["part_br_vbp"], 6),
            "vbp_rank": None if d["rank_br_vbp"] is None else int(d["rank_br_vbp"]),
            "vbp_pib": _arred(d["vbp_sobre_pib"], 4),
            "vab_agro": _arred(d["vab_agro_real"], 0),
            "vab_part": _arred(d["part_vab_agro"], 4),
            "vab_uf": _arred(d["part_uf_vab_agro"], 5),
            "vab_br": _arred(d["part_br_vab_agro"], 6),
            "var10": _arred(d["vbp_var_10a"], 4),
            "lav": d["principais_lavouras"],
            "bov": _arred(d["bovinos_cabecas"], 0),
        }
    (config.SITE_DATA / "municipios.json").write_text(
        json.dumps(registros, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
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
            "O último ano de PAM, PPM e PEVS é preliminar no IBGE.",
        ],
    }
    (config.SITE_DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
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
    painel = montar_painel(mun, ler("pib"), componentes, fatores)
    tabelas.gravar(painel, config.PROCESSED / "indicadores_municipio_ano.csv.gz", COLUNAS_PAINEL)
    uf = agregados_uf(painel)
    tabelas.gravar(uf, config.PROCESSED / "indicadores_uf_ano.csv", list(uf[0].keys()) if uf else ["uf"])

    try:
        rebanhos = ler("ppm_rebanhos")
    except FileNotFoundError:
        rebanhos = None
    atual, anos = retrato_atual(painel, componentes.get("pam"), rebanhos)
    tabelas.gravar(atual, config.PROCESSED / "indicadores_municipio_atual.csv", COLUNAS_ATUAL)
    exportar_site(atual, anos, base)
    log.info("anos de referência: %s | ano-base IPCA: %s", anos, base)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    main()
