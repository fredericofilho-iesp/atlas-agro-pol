"""Auditoria nacional municipal entre Base dos Dados (PAM) e SIDRA 5457.

Entrada BD: CSV da consulta docs/sql/pam_bd_municipios_nacional_2024.sql
Entrada SIDRA: CSV do workflow pam-municipios-nacional.yml
Saídas: detalhe por chave, resumo UF/cultura e ranking de divergências.
Sem imputação de zeros e sem alterar dados de produção do atlas.
"""
from __future__ import annotations
import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

CHAVE=("ano","codigo_uf","id_municipio","produto")
AUSENTES={"","-","..","...","x","null","none","nan"}
CAMPOS_DETALHE=(*CHAVE,"presenca_bd","presenca_sidra",
                "valor_bd_mil_reais","valor_sidra_mil_reais",
                "simbolo_sidra","diferenca_bd_menos_sidra",
                "diferenca_absoluta","status")
CAMPOS_RESUMO=("ano","codigo_uf","produto","chaves","iguais","divergentes",
               "ausentes_ambas","ausentes_bd","ausentes_sidra",
               "sem_linha_bd","sem_linha_sidra","soma_diferencas_comparaveis")


def valor(x):
    txt=str(x if x is not None else "").strip()
    if txt.lower() in AUSENTES:
        return None
    z=float(txt)
    if not math.isfinite(z) or z<0:
        raise ValueError(f"Valor inválido: {txt}")
    return z


def indexar(linhas,origem):
    d={}
    for row in linhas:
        chave=(str(row["ano"]),str(row["codigo_uf"]).zfill(2),
               str(row["id_municipio"]),str(row["produto"]))
        if len(chave[2])!=7 or chave[2][:2]!=chave[1]:
            raise ValueError(f"{origem}: código municipal inválido: {chave}")
        if chave in d:
            raise ValueError(f"{origem}: chave duplicada: {chave}")
        d[chave]=row
    return d


def comparar(linhas_bd,linhas_sidra):
    bd=indexar(linhas_bd,"BD")
    sidra=indexar(linhas_sidra,"SIDRA")
    detalhe=[]
    resumos=defaultdict(lambda: dict(chaves=0,iguais=0,divergentes=0,
                     ausentes_ambas=0,ausentes_bd=0,ausentes_sidra=0,
                     sem_linha_bd=0,sem_linha_sidra=0,
                     soma_diferencas_comparaveis=0.0))
    for chave in sorted(set(bd)|set(sidra)):
        a=valor(bd[chave]["valor_producao_mil_reais"]) if chave in bd else None
        b=valor(sidra[chave]["valor_producao_mil_reais"]) if chave in sidra else None
        if chave not in bd:
            status="sem_linha_bd"
        elif chave not in sidra:
            status="sem_linha_sidra"
        elif a is None and b is None:
            status="ausentes_ambas"
        elif a is None:
            status="ausentes_bd"
        elif b is None:
            status="ausentes_sidra"
        elif a==b:
            status="iguais"
        else:
            status="divergentes"
        diff=a-b if a is not None and b is not None else None
        resumo=resumos[chave[:2]+chave[3:]]
        resumo["chaves"]+=1
        resumo[status]+=1
        if diff is not None:
            resumo["soma_diferencas_comparaveis"]+=diff
        detalhe.append(dict(zip(CAMPOS_DETALHE,(
            *chave,int(chave in bd),int(chave in sidra),
            a,b,sidra[chave].get("simbolo_sidra","") if chave in sidra else "",
            diff,abs(diff) if diff is not None else None,status))))
    resumo=[dict(ano=k[0],codigo_uf=k[1],produto=k[2],**v)
            for k,v in sorted(resumos.items())]
    ranking=sorted((r for r in detalhe if r["status"]=="divergentes"),
                   key=lambda r:r["diferenca_absoluta"],reverse=True)
    return detalhe,resumo,ranking


def escrever(path,linhas,campos):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bd",type=Path,required=True)
    ap.add_argument("--sidra",type=Path,required=True)
    ap.add_argument("--saida-dir",type=Path,required=True)
    args=ap.parse_args()
    with args.bd.open(encoding="utf-8-sig",newline="") as f:
        bd=list(csv.DictReader(f))
    with args.sidra.open(encoding="utf-8-sig",newline="") as f:
        sidra=list(csv.DictReader(f))
    detalhe,resumo,ranking=comparar(bd,sidra)
    escrever(args.saida_dir/"comparacao_nacional_detalhe.csv",detalhe,CAMPOS_DETALHE)
    escrever(args.saida_dir/"comparacao_nacional_resumo.csv",resumo,CAMPOS_RESUMO)
    escrever(args.saida_dir/"comparacao_nacional_ranking.csv",ranking,CAMPOS_DETALHE)
    print(f"Comparados {len(detalhe)} registros, {len(ranking)} divergências, "
          f"{len(resumo)} pares UF/produto.",flush=True)


if __name__=="__main__":
    main()
