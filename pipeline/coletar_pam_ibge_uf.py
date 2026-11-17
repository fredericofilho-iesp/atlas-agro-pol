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
    """Mapeia dimensões pelo cabeçalho SIDRA, não por posições fixas."""
    if not isinstance(dados, list) or len(dados) < 2:
        raise ValueError("SIDRA: resposta sem registros")
    cab = dados[0]
    if "V" not in cab:
        raise ValueError("SIDRA: esquema inesperado sem valor V")
    # Em /f/a, D1C/D1N designam o território, D2 o período,
    # D3 a variável e D4 a classificação; não assumir ordem fixa.
    nomes = {k: str(v).lower() for k, v in cab.items()}
    cod_uf = next((k for k,v in nomes.items()
                   if k.startswith("D") and k.endswith("C")
                   and ("unidade da federação" in v or "unidade da federacao" in v)), None)
    produto = next((k for k,v in nomes.items()
                    if k.startswith("D") and k.endswith("N")
                    and ("produto" in v or "lavoura" in v)), None)
    periodo = next((k for k,v in nomes.items()
                    if k.startswith("D") and k.endswith("C")
                    and ("ano" in v or "período" in v or "periodo" in v)), None)
    if not cod_uf or not produto or not periodo:
        raise ValueError(f"SIDRA: dimensões não identificadas: {cab}")
    resultado = []
    vistos = set()
    for linha in dados[1:]:
        nome = str(linha.get(produto, "")).strip()
        if nome not in PRODUTOS:
            continue
        uf = str(linha.get(cod_uf, "")).strip().zfill(2)
        if len(uf) != 2 or not uf.isdigit():
            raise ValueError(f"UF inválida: {uf!r}")
        if str(linha.get(periodo, "")).strip() != str(ano):
            raise ValueError(f"Período inesperado: {linha.get(periodo)!r}")
        valor_txt = str(linha.get("V", "")).strip()
        if valor_txt in ("", "-", "..", "...", "X", "x"):
            valor = ""
        else:
            try:
                valor = float(valor_txt)
            except ValueError as e:
                raise ValueError(f"Valor SIDRA não numérico: {valor_txt!r}") from e
            if not __import__("math").isfinite(valor) or valor < 0:
                raise ValueError(f"Valor SIDRA inválido: {valor_txt!r}")
        chave = (uf, nome)
        if chave in vistos:
            raise ValueError(f"Chave duplicada: {chave}")
        vistos.add(chave)
        resultado.append(dict(ano=ano, codigo_uf=uf, produto=nome,
                              valor_total_mil_reais=valor))
    if not resultado:
        raise ValueError("Nenhuma das cinco culturas encontrada na resposta")
    ufs = {r["codigo_uf"] for r in resultado}
    culturas = {r["produto"] for r in resultado}
    if len(ufs) != 27 or culturas != set(PRODUTOS) or len(resultado) != 135:
        raise ValueError(
            f"Cobertura incompleta ou classificação inesperada: "
            f"{len(ufs)} UFs, {len(culturas)} culturas, {len(resultado)} linhas. "
            "Não publicar como referência validada; revisar metadados SIDRA."
        )
    return sorted(resultado, key=lambda r: (r["codigo_uf"], r["produto"]))


def coletar(ano: int, timeout: int = 90) -> list[dict]:
    url = f"{BASE}/t/5457/n3/all/v/215/p/{ano}/c782/all/f/a"
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
