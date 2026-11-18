"""Inventário verificável de variáveis e produtos da PAM (agregado 5457).

Consulta metadados oficiais do IBGE; não supõe códigos de variáveis,
produtos ou unidades. A saída é um artefato de diagnóstico, não um dado
incorporado ao mapa.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

URL = "https://servicodados.ibge.gov.br/api/v3/agregados/5457/metadados"


def obter_metadados(url=URL):
    req = urllib.request.Request(url, headers={"User-Agent": "atlas-agro-pol/1.0"})
    with urllib.request.urlopen(req, timeout=90) as resposta:
        dados = json.load(resposta)
    if not isinstance(dados, dict) or not dados.get("variaveis"):
        raise ValueError("Metadados sem lista de variáveis; interrompendo coleta.")
    return dados


def inventariar(dados):
    variaveis = []
    for v in dados["variaveis"]:
        if not isinstance(v, dict) or "id" not in v or "nome" not in v:
            raise ValueError("Variável sem identificação ou nome")
        variaveis.append({"id": str(v["id"]), "nome": v["nome"], "unidade": v.get("unidade")})
    classificacoes = []
    for c in dados.get("classificacoes", []):
        categorias = c.get("categorias", [])
        classificacoes.append({
            "id": str(c.get("id", "")),
            "nome": c.get("nome", ""),
            "categorias": [
                {"id": str(k["id"]), "nome": k["nome"]}
                for k in categorias if isinstance(k, dict) and "id" in k and "nome" in k
            ],
        })
    return {
        "fonte": URL,
        "agregado": "5457",
        "titulo": dados.get("nome"),
        "variaveis": variaveis,
        "classificacoes": classificacoes,
        "observacao": "Inventário de metadados, sem estimar valores ausentes ou selecionar culturas automaticamente.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", type=Path, required=True)
    args = ap.parse_args()
    inventario = inventariar(obter_metadados())
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(inventario, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Variáveis oficiais: {len(inventario['variaveis'])}")
    for v in inventario["variaveis"]:
        print(f"  {v['id']}: {v['nome']} [{v['unidade']}]")
    print(f"Classificações: {len(inventario['classificacoes'])}")
    for c in inventario["classificacoes"]:
        print(f"  {c['id']}: {c['nome']} ({len(c['categorias'])} categorias)")


if __name__ == "__main__":
    main()
