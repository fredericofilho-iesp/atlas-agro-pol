"""Diagnóstico reproduzível de discrepâncias municipais PAM/BD × SIDRA.

Entrada: CSV resultante do cruzamento municipal, preservando códigos e símbolos.
Saída: ranking completo das divergências, resumo por UF/produto e prioridades.
Não atribui causas nem converte valores ausentes em zero.
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from pathlib import Path

CHAVE = ("ano", "codigo_uf", "id_municipio", "produto")
COLUNAS = ("valor_producao_mil_reais_bd", "valor_producao_mil_reais_sidra")
AUSENTES = {"", "-", "..", "...", "x", "X", "null", "None", "nan"}


def ler_valor(texto):
    bruto = str(texto or "").strip()
    return None if bruto in AUSENTES else float(bruto)


def diagnosticar(linhas):
    chaves = set()
    detalhe = []
    grupos = defaultdict(lambda: dict(total=0, iguais=0, diferentes=0,
                                       nulo_ambas=0, nulo_bd=0, nulo_sidra=0,
                                       delta_comparavel=0.0))
    for row in linhas:
        chave = tuple(str(row[c]).strip() for c in CHAVE)
        if chave in chaves:
            raise ValueError(f"Chave duplicada: {chave}")
        chaves.add(chave)
        a, b = (ler_valor(row[c]) for c in COLUNAS)
        grupo = grupos[(chave[1], chave[3])]
        grupo["total"] += 1
        if a is None and b is None:
            status, delta = "nulo_ambas", None
        elif a is None:
            status, delta = "nulo_bd", None
        elif b is None:
            status, delta = "nulo_sidra", None
        else:
            delta = a - b
            status = "igual" if delta == 0 else "diferente"
            grupo["delta_comparavel"] += delta
        grupo[{"igual": "iguais", "diferente": "diferentes"}.get(status, status)] += 1
        detalhe.append({**{c: row[c] for c in CHAVE},
                        "bd_mil_reais": a if a is not None else "",
                        "sidra_mil_reais": b if b is not None else "",
                        "simbolo_sidra": row.get("simbolo_sidra", ""),
                        "delta_bd_menos_sidra": delta if delta is not None else "",
                        "abs_delta": abs(delta) if delta is not None else "",
                        "status": status})
    ranking = sorted((r for r in detalhe if r["status"] == "diferente"),
                     key=lambda r: r["abs_delta"], reverse=True)
    resumo = [dict(codigo_uf=uf, produto=produto, **dados)
              for (uf, produto), dados in sorted(grupos.items())]
    return detalhe, ranking, resumo


def escrever(path, linhas, campos):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", type=Path, required=True)
    ap.add_argument("--saida-dir", type=Path, required=True)
    args = ap.parse_args()
    with args.entrada.open(encoding="utf-8-sig", newline="") as f:
        detalhe, ranking, resumo = diagnosticar(csv.DictReader(f))
    campos = list(detalhe[0]) if detalhe else list(CHAVE) + ["status"]
    escrever(args.saida_dir / "auditoria_municipal_detalhe.csv", detalhe, campos)
    escrever(args.saida_dir / "auditoria_municipal_ranking.csv", ranking, campos)
    escrever(args.saida_dir / "auditoria_municipal_resumo.csv", resumo,
             list(resumo[0]) if resumo else ["codigo_uf", "produto"])
    print(f"{len(detalhe)} chaves; {len(ranking)} divergências; {len(resumo)} grupos.")


if __name__ == "__main__":
    main()
