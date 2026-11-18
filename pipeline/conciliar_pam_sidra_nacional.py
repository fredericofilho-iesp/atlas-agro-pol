"""Reconcilia somas municipais SIDRA PAM com totais oficiais UF da mesma extração.

Uso:
 python -m pipeline.conciliar_pam_sidra_nacional --municipios M.csv --ufs U.csv --saida C.csv

NULL e símbolos de ausência nunca são convertidos em zero.
Diferenças de arredondamento permanecem explicitadas, sem ajuste ad hoc.
"""
from __future__ import annotations
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

CAMPOS = ("ano","codigo_uf","produto","municipios","municipios_com_valor",
          "municipios_sem_valor","soma_municipal_mil_reais","total_uf_mil_reais",
          "diferenca_mil_reais","diferenca_relativa_pct","status")


def numero(valor):
    bruto = str(valor if valor is not None else "").strip()
    if bruto.lower() in {"","-","..","...","x","null","none","nan"}:
        return None
    res=float(bruto)
    if not math.isfinite(res) or res<0:
        raise ValueError(f"Valor monetário inválido: {valor!r}")
    return res


def reconciliar(municipios,ufs):
    grupos=defaultdict(lambda: {"ids":set(),"valores":[]})
    for r in municipios:
        uf=str(r["codigo_uf"]).zfill(2)
        mun=str(r["id_municipio"])
        if len(mun)!=7 or not mun.startswith(uf):
            raise ValueError(f"Município/UF inválido: {mun}/{uf}")
        chave=(str(r["ano"]),uf,r["produto"])
        if mun in grupos[chave]["ids"]:
            raise ValueError(f"Município duplicado: {chave}/{mun}")
        grupos[chave]["ids"].add(mun)
        grupos[chave]["valores"].append(numero(r["valor_producao_mil_reais"]))
    totais={}
    for r in ufs:
        chave=(str(r["ano"]),str(r["codigo_uf"]).zfill(2),r["produto"])
        if chave in totais:
            raise ValueError(f"UF/produto duplicado: {chave}")
        totais[chave]=numero(r["valor_total_mil_reais"])
    resultado=[]
    for chave in sorted(set(grupos)|set(totais)):
        g=grupos.get(chave)
        valores=g["valores"] if g else []
        validos=[v for v in valores if v is not None]
        soma=sum(validos) if validos else None
        total=totais.get(chave)
        if g is None:
            status="sem_linhas_municipais"
        elif chave not in totais:
            status="sem_total_uf"
        elif soma is None and total is None:
            status="ambos_ausentes"
        elif soma is None:
            status="municipios_ausentes"
        elif total is None:
            status="uf_ausente"
        else:
            status="concordante" if soma==total else "divergencia"
        delta=soma-total if soma is not None and total is not None else None
        pct=100*delta/total if delta is not None and total else None
        resultado.append(dict(zip(CAMPOS,(
            chave[0],chave[1],chave[2],len(valores),len(validos),
            len(valores)-len(validos),soma,total,delta,pct,status))))
    return resultado


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--municipios",required=True,type=Path)
    ap.add_argument("--ufs",required=True,type=Path)
    ap.add_argument("--saida",required=True,type=Path)
    args=ap.parse_args()
    with args.municipios.open(encoding="utf-8-sig",newline="") as f:
        municipais=list(csv.DictReader(f))
    with args.ufs.open(encoding="utf-8-sig",newline="") as f:
        ufs=list(csv.DictReader(f))
    resultados=reconciliar(municipais,ufs)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(resultados)
    print(f"{len(resultados)} pares UF/cultura reconciliados; "
          f"{sum(r['status']=='divergencia' for r in resultados)} diferenças numéricas.",flush=True)


if __name__=="__main__":
    main()
