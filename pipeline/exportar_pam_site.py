"""Empacota a camada auditada em JSON compacto para o mapa estático.

Entrada: CSV da camada de qualidade PAM 2024.
Saída: site/auditoria-pam/data/pam-2024.json.
Não altera os CSVs originais e preserva valores ausentes como null.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

CULTURAS=("Soja (em grão)","Milho (em grão)","Cana-de-açúcar",
          "Café (em grão) Total","Arroz (em casca)")
STATUS=("concordante","divergente","ausentes_ambas","ausentes_bd",
        "ausentes_sidra","sem_linha_bd","sem_linha_sidra")


def inteiro_ou_nulo(raw):
    if raw is None or str(raw).strip()=="":
        return None
    x=float(raw)
    if not x.is_integer() or x<0:
        raise ValueError(f"Valor não inteiro em mil reais: {raw}")
    return int(x)


def empacotar(linhas):
    rows=[]
    keys=set()
    for r in linhas:
        mun=str(r["id_municipio"])
        crop=CULTURAS.index(r["produto"])
        status=STATUS.index(r["status_auditoria"])
        key=(mun,crop)
        if len(mun)!=7 or not mun.isdigit() or key in keys:
            raise ValueError(f"Município/cultura inválido ou duplicado: {key}")
        keys.add(key)
        rows.append([mun,crop,inteiro_ou_nulo(r["valor_sidra_mil_reais"]),
                     inteiro_ou_nulo(r["valor_bd_mil_reais"]),status])
    return {"schema":"atlas-pam-audit-v1","year":2024,"unit":"mil_reais",
            "sidra_extracted":"2026-11-17","bd_extracted":None,
            "crops":list(CULTURAS),"statuses":list(STATUS),"rows":rows}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada",type=Path,required=True)
    ap.add_argument("--saida",type=Path,required=True)
    args=ap.parse_args()
    with args.entrada.open(encoding="utf-8-sig",newline="") as f:
        data=empacotar(csv.DictReader(f))
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print(f"Gerados {len(data['rows'])} registros em {args.saida}")


if __name__=="__main__":
    main()
