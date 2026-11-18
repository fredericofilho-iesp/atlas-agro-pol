"""Gera camada pública de qualidade PAM 2024 sem substituir dados brutos.

Entrada: CSV da comparação nacional BD/SIDRA (outer join por município/cultura).
Saída: CSV analítico com valores, fonte, status, diferenças e proveniência.
Nenhum valor ausente é convertido em zero.
"""
from __future__ import annotations
import argparse
import csv
import math
from collections import Counter
from pathlib import Path

CAMPOS = ("ano","codigo_uf","id_municipio","produto",
          "valor_bd_mil_reais","valor_sidra_mil_reais",
          "valor_referencia_mil_reais","fonte_referencia",
          "status_auditoria","diferenca_bd_menos_sidra_mil_reais",
          "diferenca_absoluta_mil_reais","diferenca_relativa_sidra_pct",
          "simbolo_sidra","presenca_bd","presenca_sidra",
          "data_extracao_sidra","data_extracao_bd","unidade")
AUSENTES={"","-","..","...","x","null","none","nan"}


def numero(x):
    txt=str(x if x is not None else "").strip()
    if txt.lower() in AUSENTES:
        return None
    val=float(txt)
    if not math.isfinite(val) or val<0:
        raise ValueError(f"Valor inválido: {txt!r}")
    return val


def construir(linhas, data_sidra, data_bd):
    saida=[]
    chaves=set()
    for r in linhas:
        chave=tuple(str(r[k]).strip() for k in ("ano","codigo_uf","id_municipio","produto"))
        if chave in chaves:
            raise ValueError(f"Chave duplicada: {chave}")
        chaves.add(chave)
        if len(chave[2])!=7 or chave[2][:2]!=chave[1]:
            raise ValueError(f"Município inválido: {chave}")
        bd=numero(r.get("valor_producao_mil_reais_bd"))
        sidra=numero(r.get("valor_producao_mil_reais_sidra"))
        merge=r.get("_merge","both")
        if merge not in ("both","left_only","right_only"):
            raise ValueError(f"Indicador de junção inesperado: {merge}")
        if merge=="left_only":
            status="sem_linha_sidra"
        elif merge=="right_only":
            status="sem_linha_bd"
        elif bd is None and sidra is None:
            status="ausentes_ambas"
        elif bd is None:
            status="ausentes_bd"
        elif sidra is None:
            status="ausentes_sidra"
        elif bd==sidra:
            status="concordante"
        else:
            status="divergente"
        # SIDRA oficial como referência provisória somente quando numérico.
        ref=sidra
        fonte="SIDRA_5457_PROVISORIA" if sidra is not None else "SEM_REFERENCIA_NUMERICA"
        delta=bd-sidra if bd is not None and sidra is not None else None
        pct=100*delta/sidra if delta is not None and sidra!=0 else None
        saida.append(dict(zip(CAMPOS,(
            *chave,bd,sidra,ref,fonte,status,delta,
            abs(delta) if delta is not None else None,pct,
            r.get("simbolo_sidra",""),int(merge!="right_only"),
            int(merge!="left_only"),data_sidra,data_bd,"mil_reais"))))
    return saida


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada",type=Path,required=True)
    ap.add_argument("--saida",type=Path,required=True)
    ap.add_argument("--data-sidra",default="2026-11-17")
    ap.add_argument("--data-bd",default="",help="Data de extração BD; vazio se não confirmada")
    args=ap.parse_args()
    with args.entrada.open(encoding="utf-8-sig",newline="") as f:
        rows=construir(csv.DictReader(f),args.data_sidra,args.data_bd)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} chaves; classificação: {dict(Counter(r['status_auditoria'] for r in rows))}")


if __name__=="__main__":
    main()
