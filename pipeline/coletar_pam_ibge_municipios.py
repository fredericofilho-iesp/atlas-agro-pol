"""Coleta SIDRA PAM 5457 em nível municipal para seis pares críticos (2024).

A fonte é independente da Base dos Dados. Mantém o símbolo original do
SIDRA e não converte ausências em zero. Não exige cobertura municipal
completa, mas falha em respostas vazias, códigos inesperados e duplicatas.
"""
from __future__ import annotations
import argparse
import csv
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE = "https://apisidra.ibge.gov.br/values"
ALVOS = {
    "52": {"Milho (em grão)": 40122, "Cana-de-açúcar": 40106},
    "11": {"Café (em grão) Total": 40139},
    "26": {"Milho (em grão)": 40122},
    "41": {"Café (em grão) Total": 40139},
    "12": {"Arroz (em casca)": 40102},
}
COLUNAS = ["ano", "codigo_uf", "id_municipio", "produto", "valor_producao_mil_reais", "simbolo_sidra"]


def interpretar(dados, ano, uf, produto_esperado):
    if not isinstance(dados, list) or len(dados) < 2:
        raise ValueError(f"SIDRA: resposta vazia para {uf}/{produto_esperado}")
    cab = dados[0]
    nomes = {k: str(v).lower() for k, v in cab.items()}
    def coluna(sufixo, termos):
        return next((k for k, v in nomes.items() if k.startswith("D")
                     and k.endswith(sufixo) and any(t in v for t in termos)), None)
    municipio = coluna("C", ("município", "municipio"))
    periodo = coluna("C", ("ano", "período", "periodo"))
    produto = coluna("N", ("produto", "lavoura"))
    if not all((municipio, periodo, produto, "V" in cab)):
        raise ValueError(f"SIDRA: esquema municipal inesperado: {cab}")
    out = []
    vistos = set()
    for linha in dados[1:]:
        nome = str(linha.get(produto, "")).strip()
        if nome != produto_esperado:
            raise ValueError(f"Produto inesperado: {nome!r} != {produto_esperado!r}")
        codigo = str(linha.get(municipio, "")).strip()
        if len(codigo) != 7 or not codigo.isdigit() or not codigo.startswith(uf):
            raise ValueError(f"Município inválido para UF {uf}: {codigo!r}")
        if str(linha.get(periodo, "")).strip() != str(ano):
            raise ValueError(f"Período inesperado: {linha.get(periodo)!r}")
        if codigo in vistos:
            raise ValueError(f"Município duplicado: {codigo}")
        vistos.add(codigo)
        bruto = str(linha.get("V", "")).strip()
        if bruto in ("", "-", "..", "...", "X", "x"):
            valor = ""
        else:
            valor = float(bruto)
            if not 0 <= valor < float("inf"):
                raise ValueError(f"Valor inválido: {bruto!r}")
        out.append(dict(ano=ano, codigo_uf=uf, id_municipio=codigo,
                        produto=nome, valor_producao_mil_reais=valor,
                        simbolo_sidra=bruto))
    return sorted(out, key=lambda r: r["id_municipio"])


def coletar(ano=2024, timeout=90):
    resultado = []
    for uf, produtos in ALVOS.items():
        for nome, codigo in produtos.items():
            url = f"{BASE}/t/5457/n6/in%20n3%20{uf}/v/215/p/{ano}/c782/{codigo}/f/a"
            req = urllib.request.Request(url, headers={"User-Agent": "atlas-agro-pol/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    dados = json.load(resp)
            except urllib.error.HTTPError as exc:
                detalhe = exc.read(2500).decode("utf-8", errors="replace")
                raise RuntimeError(f"SIDRA HTTP {exc.code} na consulta {uf}/{nome}; URL={url}; resposta={detalhe}") from exc
            linhas = interpretar(dados, ano, uf, nome)
            if not linhas:
                raise ValueError(f"Nenhum município retornado: {uf}/{nome}")
            resultado.extend(linhas)
            print(f"UF={uf}, produto={nome}: {len(linhas)} municípios", flush=True)
    return resultado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, default=2024)
    ap.add_argument("--saida", required=True, type=Path)
    args = ap.parse_args()
    linhas = coletar(args.ano)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        w.writeheader()
        w.writerows(linhas)
    print(f"Coleta municipal oficial: {len(linhas)} linhas", flush=True)


if __name__ == "__main__":
    main()
