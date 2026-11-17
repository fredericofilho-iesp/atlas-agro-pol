"""Coleta nacional municipal PAM 2024 (SIDRA 5457, variável 215).

27 UFs x 5 culturas, uma requisição por UF/cultura. Preserva símbolos
de ausência e não presume que cada cultura exista em todos os municípios.
"""
from __future__ import annotations
import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from pipeline.coletar_pam_ibge_municipios import interpretar
from pipeline.coletar_pam_ibge_uf import PRODUTOS

UFS = ("11","12","13","14","15","16","17","21","22","23","24","25",
       "26","27","28","29","31","32","33","35","41","42","43","50",
       "51","52","53")
CAMPOS = ("ano","codigo_uf","id_municipio","produto",
          "valor_producao_mil_reais","simbolo_sidra")
BASE = "https://apisidra.ibge.gov.br/values"


def consultar(url, tentativas=4, timeout=120):
    for tentativa in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"atlas-agro-pol/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code not in (429,500,502,503,504):
                raise
            if tentativa == tentativas-1:
                raise RuntimeError(f"Falha definitiva SIDRA: {url}") from exc
            time.sleep(2 ** tentativa)


def coletar(ano=2024, ufs=UFS, produtos=PRODUTOS):
    resultado=[]
    for uf in ufs:
        if uf not in UFS:
            raise ValueError(f"UF não reconhecida: {uf}")
        for nome,codigo in produtos.items():
            url=f"{BASE}/t/5457/n6/in%20n3%20{uf}/v/215/p/{ano}/c782/{codigo}/f/a"
            dados=consultar(url)
            linhas=interpretar(dados,ano,uf,nome)
            if not linhas:
                raise ValueError(f"Consulta sem linhas: {uf}/{nome}")
            resultado.extend(linhas)
            print(f"UF {uf} / {nome}: {len(linhas)} registros",flush=True)
    chaves=[(r["ano"],r["id_municipio"],r["produto"]) for r in resultado]
    if len(chaves)!=len(set(chaves)):
        raise ValueError("Chaves municipais duplicadas")
    return sorted(resultado,key=lambda r:(r["codigo_uf"],r["produto"],r["id_municipio"]))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--ano",type=int,default=2024)
    ap.add_argument("--saida",type=Path,required=True)
    ap.add_argument("--ufs",nargs="*",default=list(UFS))
    args=ap.parse_args()
    linhas=coletar(args.ano,ufs=args.ufs)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    with args.saida.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)
    print(f"Concluído: {len(linhas)} registros, {len(set(r['codigo_uf'] for r in linhas))} UFs",flush=True)


if __name__=="__main__":
    main()
