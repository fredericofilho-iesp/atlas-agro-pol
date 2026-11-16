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
from collections import defaultdict

from . import config, sidra, tabelas

log = logging.getLogger(__name__)

URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
             "?formato=application/json&qualidade=minima&intrarregiao=municipio")

COLUNAS = ["codigo", "territorio", "ano", "medida", "categoria_codigo", "categoria",
           "unidade", "valor", "tabela"]
REGIOES = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste"}


def _salvar(linhas: list[dict], nome: str, colunas: list[str]) -> None:
    destino = config.INTERIM / f"{nome}.csv.gz"
    n = tabelas.gravar(linhas, destino, colunas)
    log.info("salvo %s (%d linhas)", destino.relative_to(config.RAIZ), n)


# ---------------------------------------------------------------------------
# Municípios e malha
# ---------------------------------------------------------------------------
def municipios() -> list[dict]:
    """Lista de municípios a partir do próprio apisidra (PIB do último ano).

    O apisidra devolve o nome como "Sorriso - MT"; UF e região saem do código.
    """
    meta = sidra.metadados(5938)
    var = meta.variavel_id(["produto interno bruto", "precos correntes"], ["per capita"])
    out = []
    for r in sidra.baixar(5938, "n6", [var], [meta.periodos[-1]]):
        codigo = int(r["codigo"])
        nome, _, uf = r["territorio"].rpartition(" - ")
        out.append({"codigo": codigo, "nome": nome, "uf_codigo": codigo // 100_000, "uf": uf,
                    "regiao": REGIOES.get(codigo // 1_000_000)})
    out.sort(key=lambda r: r["codigo"])
    _salvar(out, "municipios", ["codigo", "nome", "uf_codigo", "uf", "regiao"])
    return out


def malha() -> None:
    """Malha municipal leve (TopoJSON) pela API de malhas do IBGE.

    Essa API costuma recusar conexões de fora do Brasil; nesse caso a etapa é
    pulada sem interromper o resto (a malha pode ser gerada depois).
    """
    try:
        topo = sidra._get_json(URL_MALHA, timeout=120)
    except Exception as exc:  # noqa: BLE001
        log.warning("Malha não baixada (API de malhas indisponível nesta rede): %s", exc)
        return
    destino = config.SITE_DATA / "malha_municipios.topojson"
    destino.write_text(json.dumps(topo, separators=(",", ":")), encoding="utf-8")
    log.info("malha salva em %s (%.1f MB)", destino.relative_to(config.RAIZ),
             destino.stat().st_size / 1e6)


# ---------------------------------------------------------------------------
# Fontes do SIDRA
# ---------------------------------------------------------------------------
def ipca(usar_cache: bool = True) -> list[dict]:
    """IPCA número-índice mensal -> média anual, só anos completos (12 meses)."""
    por_ano: dict[int, list[float]] = defaultdict(list)
    for r in sidra.coletar("ipca", ano_inicio=config.ANO_INICIO, usar_cache=usar_cache):
        if r["valor"] is not None:
            por_ano[int(str(r["periodo"])[:4])].append(r["valor"])
    anual = [{"ano": a, "indice_medio": sum(v) / len(v)} for a, v in sorted(por_ano.items()) if len(v) == 12]
    _salvar(anual, "ipca_anual", ["ano", "indice_medio"])
    return anual


def fonte_sidra(nome: str, usar_cache: bool = True) -> list[dict]:
    linhas = sidra.coletar(nome, usar_cache=usar_cache)
    for r in linhas:
        r["ano"] = int(str(r.pop("periodo"))[:4])
        r["codigo"] = int(r["codigo"])
    if any(r.get("categoria") for r in linhas):
        # Tabelas por produto: guarda só valores positivos e as linhas "Total".
        # Ausência = zero ("-") ou sigilo ("X"); o sigilo fica registrado à parte.
        def eh_total(r):
            return sidra.normalizar(str(r.get("categoria") or "")) == "total"
        sigilo = [r for r in linhas if r["valor"] is None and not eh_total(r)]
        if sigilo:
            _salvar(sigilo, f"{nome}_sigilo", ["codigo", "ano", "medida", "categoria"])
        linhas = [r for r in linhas if eh_total(r) or (r["valor"] or 0) > 0]
    _salvar(linhas, nome, COLUNAS)
    return linhas


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
