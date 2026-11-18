"""Validação offline de correspondência entre geometria municipal GeoJSON e PAM.

Não assume que a malha é oficial; imprime contagens e falha com IDs inválidos,
duplicados ou cobertura abaixo do limiar informado.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def codigo(feature):
    p=feature.get("properties") or {}
    val=feature.get("id") or next((p[k] for k in ("id","codarea","codigo_ibge","CD_MUN","CD_GEOCMU","geocodigo") if p.get(k)),None)
    if val is None:
        return None
    return str(val).removesuffix(".0").zfill(7)


def validar(geojson, codigos_pam, minimo=0.99):
    if geojson.get("type")!="FeatureCollection" or not isinstance(geojson.get("features"),list):
        raise ValueError("GeoJSON não é FeatureCollection")
    ids=[codigo(f) for f in geojson["features"]]
    invalidos=[x for x in ids if x is None or len(x)!=7 or not x.isdigit()]
    contagem=Counter(ids)
    duplicados=[k for k,n in contagem.items() if n>1]
    ids_validos={x for x in ids if x and len(x)==7 and x.isdigit()}
    faltantes=sorted(codigos_pam-ids_validos)
    extras=sorted(ids_validos-codigos_pam)
    cobertura=len(codigos_pam&ids_validos)/len(codigos_pam) if codigos_pam else 0
    resultado={"municipios_pam":len(codigos_pam),"geometrias":len(ids),
               "codigos_geo_unicos":len(ids_validos),"cobertura_pam":round(cobertura,6),
               "sem_geometria":faltantes,"geometrias_sem_pam":extras,
               "codigos_invalidos":len(invalidos),"codigos_duplicados":duplicados}
    if invalidos or duplicados or cobertura<minimo:
        raise ValueError(f"Malha reprovada: {json.dumps(resultado,ensure_ascii=False)}")
    return resultado


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--geojson",type=Path,required=True)
    ap.add_argument("--camada",type=Path,required=True)
    ap.add_argument("--saida",type=Path,required=True)
    ap.add_argument("--minimo",type=float,default=0.99)
    args=ap.parse_args()
    with args.camada.open(encoding="utf-8-sig",newline="") as f:
        codigos={r["id_municipio"] for r in csv.DictReader(f)}
    resultado=validar(json.loads(args.geojson.read_text(encoding="utf-8")),codigos,args.minimo)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in resultado.items() if not isinstance(v,list)},ensure_ascii=False))


if __name__=="__main__":
    main()
