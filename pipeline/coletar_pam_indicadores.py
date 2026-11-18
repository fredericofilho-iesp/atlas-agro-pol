"""Coleta PAM/SIDRA 5457: cinco indicadores para as cinco culturas auditadas.

Fase de validação anterior à integração ao mapa: arquivos exportados como artefatos
do GitHub Actions, sem sobrescrever o JSON de auditoria 2024 publicado.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pipeline.coletar_pam_ibge_municipios_nacional import UFS, consultar
from pipeline.coletar_pam_ibge_uf import PRODUTOS

BASE = "https://apisidra.ibge.gov.br/values"
VARIAVEIS = {
    "8331": ("area_plantada_ha", "ha"),
    "216": ("area_colhida_ha", "ha"),
    "214": ("quantidade_produzida_t", "t"),
    "112": ("rendimento_medio_kg_ha", "kg/ha"),
    "215": ("valor_producao_mil_reais", "mil R$"),
}
CAMPOS = ("ano", "codigo_uf", "id_municipio", "produto", "codigo_produto",
          "codigo_variavel", "indicador", "unidade", "valor", "simbolo_sidra")
AUSENCIA = {"", "-", "..", "...", "X", "x"}


def identificar_colunas(cab):
    """Descobre os eixos pelos descritores retornados pelo próprio SIDRA."""
    def eixo(tipos, palavras):
        for k, v in cab.items():
            desc = str(v).lower()
            if k.startswith("D") and k.endswith(tipos) and any(x in desc for x in palavras):
                return k
        return None

    colunas = {
        "municipio": eixo("C", ("município", "municipio")),
        "ano": eixo("C", ("ano", "período", "periodo")),
        "produto": eixo("C", ("produto", "lavoura")),
        "variavel": eixo("C", ("variável", "variavel")),
    }
    if "V" not in cab or not all(colunas.values()) or len(set(colunas.values())) != 4:
        raise ValueError(f"Esquema SIDRA inesperado: {cab}")
    return colunas


def interpretar(dados, ano, uf, produtos=PRODUTOS, variaveis=VARIAVEIS):
    if not isinstance(dados, list) or len(dados) < 2 or not isinstance(dados[0], dict):
        raise ValueError(f"SIDRA sem registros para UF {uf}")
    col = identificar_colunas(dados[0])
    codigos_produtos = {str(v): k for k, v in produtos.items()}
    vistos = set()
    registros = []
    for linha in dados[1:]:
        municipio = str(linha.get(col["municipio"], "")).strip()
        codigo_produto = str(linha.get(col["produto"], "")).strip()
        codigo_variavel = str(linha.get(col["variavel"], "")).strip()
        periodo = str(linha.get(col["ano"], "")).strip()
        if len(municipio) != 7 or not municipio.isdigit() or not municipio.startswith(uf):
            raise ValueError(f"Município inválido para {uf}: {municipio!r}")
        if periodo != str(ano) or codigo_produto not in codigos_produtos or codigo_variavel not in variaveis:
            raise ValueError(f"Dimensão inesperada: {periodo}/{codigo_produto}/{codigo_variavel}")
        chave = (municipio, codigo_produto, codigo_variavel)
        if chave in vistos:
            raise ValueError(f"Chave municipal/produto/variável duplicada: {chave}")
        vistos.add(chave)
        bruto = str(linha.get("V", "")).strip()
        if bruto in AUSENCIA:
            valor = ""
        else:
            try:
                numero = Decimal(bruto)
            except InvalidOperation as exc:
                raise ValueError(f"Valor SIDRA não numérico: {bruto!r}") from exc
            if not numero.is_finite() or numero < 0:
                raise ValueError(f"Valor SIDRA inválido: {bruto!r}")
            valor = bruto  # Mantém precisão decimal exata do SIDRA.
        indicador, unidade = variaveis[codigo_variavel]
        registros.append({
            "ano": str(ano), "codigo_uf": uf, "id_municipio": municipio,
            "produto": codigos_produtos[codigo_produto],
            "codigo_produto": codigo_produto, "codigo_variavel": codigo_variavel,
            "indicador": indicador, "unidade": unidade,
            "valor": valor, "simbolo_sidra": bruto,
        })
    return sorted(registros, key=lambda r: (r["id_municipio"], r["codigo_produto"], r["codigo_variavel"]))


def coletar(ano=2024, ufs=UFS, produtos=PRODUTOS, variaveis=VARIAVEIS):
    if not produtos or not variaveis:
        raise ValueError("Selecionar pelo menos um produto e uma variável")
    if any(uf not in UFS for uf in ufs):
        raise ValueError("UF inválida")
    codigos_produtos = ",".join(str(v) for v in produtos.values())
    codigos_variaveis = ",".join(variaveis)
    registros = []
    por_uf = {}
    for uf in ufs:
        url = (f"{BASE}/t/5457/n6/in%20n3%20{uf}/v/{codigos_variaveis}"
               f"/p/{ano}/c782/{codigos_produtos}/f/a")
        parte = interpretar(consultar(url), ano, uf, produtos, variaveis)
        if not parte:
            raise ValueError(f"Sem registros para UF {uf}")
        # Não exigir valor em todos os municípios; ausência não equivale a zero.
        por_uf[uf] = len(parte)
        registros.extend(parte)
        print(f"UF={uf}: {len(parte)} registros", flush=True)
    return registros, por_uf


def salvar(registros, por_uf, ano, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as arq:
        writer = csv.DictWriter(arq, fieldnames=CAMPOS)
        writer.writeheader()
        writer.writerows(registros)
    contagens = Counter(r["codigo_variavel"] for r in registros)
    ausencias = Counter(r["codigo_variavel"] for r in registros if r["valor"] == "")
    manifesto = {
        "fonte": "IBGE/SIDRA, tabela 5457, classificação 782",
        "ano": ano, "registros": len(registros), "municipios": len({r["id_municipio"] for r in registros}),
        "pares_uf_produto_variavel": len({(r["codigo_uf"], r["codigo_produto"], r["codigo_variavel"]) for r in registros}),
        "ufs": por_uf,
        "variaveis": {k: {"indicador": VARIAVEIS[k][0], "unidade": VARIAVEIS[k][1],
                          "registros": contagens[k], "ausentes": ausencias[k]}
                      for k in VARIAVEIS},
        "nota": "Ausência não é zero. Os dados são preliminares e não substituem a auditoria já publicada.",
    }
    destino.with_suffix(".manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifesto, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2024)
    ap.add_argument("--saida", type=Path, required=True)
    args = ap.parse_args()
    registros, por_uf = coletar(ano=args.ano)
    salvar(registros, por_uf, args.ano, args.saida)


if __name__ == "__main__":
    main()
