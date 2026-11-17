"""Coleta independente de referência oficial PAM por UF (IBGE SIDRA 5457).

Não acessa a Base dos Dados. A API do IBGE pode estar indisponível;
nessa situação falha explicitamente e não inventa valores.
"""
from __future__ import annotations
import argparse
import csv
import json
import urllib.request
from pathlib import Path

BASE = "https://apisidra.ibge.gov.br/values"
# Variável 215: valor da produção (mil reais); classificação 782: produto.
# Os rótulos devem ser conferidos com o metadado retornado pela API.
PRODUTOS = {
    "Soja (em grão)": "Soja (em grão)",
    "Cana-de-açúcar": "Cana-de-açúcar",
    "Milho (em grão)": "Milho (em grão)",
    "Café (em grão) Total": "Café (em grão) Total",
    "Arroz (em casca)": "Arroz (em casca)",
}
CAMPOS = ["ano", "codigo_uf", "produto", "valor_total_mil_reais"]


def interpretar(dados: list[dict], ano: int) -> list[dict]:
    if not isinstance(dados, list) or len(dados) < 2:
        raise ValueError("SIDRA: resposta sem registros")
    cab = dados[0]
    # SIDRA com /f/c fornece identificadores N3, C782, V e D3N.
    if not all(k in cab for k in ("N3", "C782", "D3N", "V")):
        raise ValueError(f"SIDRA: esquema inesperado: {sorted(cab)}")
    resultado = []
    vistos = set()
    for linha in dados[1:]:
        nome = str(linha.get("D3N", "")).strip()
        if nome not in PRODUTOS:
            continue
        uf = str(linha.get("N3", "")).strip().zfill(2)
        if len(uf) != 2 or not uf.isdigit():
            raise ValueError(f"UF inválida: {uf!r}")
        periodo = str(linha.get("D2C", linha.get("D2N", ano))).strip()
        if periodo != str(ano):
            raise ValueError(f"Período inesperado: {periodo}")
        valor_txt = str(linha.get("V", "")).strip()
        if valor_txt in ("", "-", "..", "...", "X"):
            valor = ""
        else:
            try:
                valor = float(valor_txt)
            except ValueError as e:
                raise ValueError(f"Valor SIDRA não numérico: {valor_txt!r}") from e
        chave = (uf, nome)
        if chave in vistos:
            raise ValueError(f"Chave duplicada: {chave}")
        vistos.add(chave)
        resultado.append(dict(ano=ano, codigo_uf=uf, produto=nome,
                              valor_total_mil_reais=valor))
    if not resultado:
        raise ValueError("Nenhuma das cinco culturas encontrada na resposta")
    return sorted(resultado, key=lambda r: (r["codigo_uf"], r["produto"]))


def coletar(ano: int, timeout: int = 90) -> list[dict]:
    url = f"{BASE}/t/5457/n3/all/v/215/p/{ano}/c782/all/f/c"
    req = urllib.request.Request(url, headers={"User-Agent": "atlas-agro-pol/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        dados = json.load(resp)
    return interpretar(dados, ano)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ano", type=int, default=2024)
    ap.add_argument("--saida", required=True, type=Path)
    ap.add_argument("--json-local", type=Path, help="Resposta JSON SIDRA já baixada")
    args = ap.parse_args(argv)
    if args.json_local:
        with args.json_local.open(encoding="utf-8") as f:
            linhas = interpretar(json.load(f), args.ano)
    else:
        linhas = coletar(args.ano)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)
    print(f"Referência oficial: {len(linhas)} linhas em {args.saida}")


if __name__ == "__main__":
    main()
