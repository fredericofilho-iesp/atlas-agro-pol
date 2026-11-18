"""Confronta somas municipais PAM/BD com benchmarks oficiais por UF.

Entrada BD: ano,codigo_uf,produto,valor_total_mil_reais (demais colunas opcionais).
Entrada oficial: ano,codigo_uf,produto,valor_total_mil_reais
Saída: CSV com estado da comparação, diferença e percentual.
Não interpreta NULL como zero. Não baixa nem inventa benchmarks oficiais.
"""
from __future__ import annotations
import argparse
import csv
import math
from pathlib import Path

COLS = ("ano", "codigo_uf", "produto", "valor_total_mil_reais")


def carregar(path: Path) -> dict:
    dados = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames or not set(COLS).issubset(leitor.fieldnames):
            raise ValueError(f"{path}: colunas necessárias: {COLS}")
        for n, row in enumerate(leitor, 2):
            key = (int(row["ano"]), str(row["codigo_uf"]).strip().zfill(2),
                   row["produto"].strip())
            if len(key[1]) != 2 or not key[1].isdigit() or not key[2]:
                raise ValueError(f"{path}:{n}: chave inválida")
            if key in dados:
                raise ValueError(f"{path}:{n}: chave duplicada {key}")
            raw = str(row["valor_total_mil_reais"] or "").strip()
            if raw.lower() in ("", "null", "none", "nan"):
                val = None
            else:
                val = float(raw)
                if not math.isfinite(val) or val < 0:
                    raise ValueError(f"{path}:{n}: valor inválido")
            dados[key] = val
    return dados


def comparar(bd: dict, oficial: dict) -> list[dict]:
    out = []
    for key in sorted(set(bd) | set(oficial)):
        a = bd.get(key)
        b = oficial.get(key)
        if key not in bd:
            status = "sem_linha_bd"
        elif key not in oficial:
            status = "sem_referencia_oficial"
        elif a is None:
            status = "bd_nulo"
        elif b is None:
            status = "oficial_nulo"
        else:
            status = "comparavel"
        dif = a - b if status == "comparavel" else None
        pct = 100 * dif / b if dif is not None and b != 0 else None
        out.append(dict(ano=key[0], codigo_uf=key[1], produto=key[2],
                        bd_mil_reais=a, oficial_mil_reais=b,
                        diferenca_mil_reais=dif, diferenca_pct=pct,
                        status=status))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bd", required=True, type=Path)
    ap.add_argument("--oficial", required=True, type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    args = ap.parse_args(argv)
    linhas = comparar(carregar(args.bd), carregar(args.oficial))
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "ano", "codigo_uf", "produto", "bd_mil_reais",
            "oficial_mil_reais", "diferenca_mil_reais", "diferenca_pct", "status"])
        writer.writeheader()
        writer.writerows(linhas)
    print(f"Validação: {len(linhas)} pares, "
          f"{sum(r['status']=='comparavel' for r in linhas)} comparáveis; "
          f"arquivo: {args.saida}")


if __name__ == "__main__":
    main()
