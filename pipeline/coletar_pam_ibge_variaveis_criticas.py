"""Coleta oficial SIDRA de variáveis produtivas em seis casos críticos da PAM 2024."""
from __future__ import annotations
import argparse
import csv
import json
import urllib.error
import urllib.request
from pathlib import Path
from pipeline.coletar_pam_ibge_municipios import interpretar

CASOS = [
    ("52", "5205471", "Milho (em grão)", 40122),
    ("52", "5205471", "Cana-de-açúcar", 40106),
    ("52", "5202502", "Cana-de-açúcar", 40106),
    ("11", "1100098", "Café (em grão) Total", 40139),
    ("11", "1100452", "Café (em grão) Total", 40139),
    ("11", "1100502", "Café (em grão) Total", 40139),
]
VARIAVEIS = {
    8331: "area_referencia_ha",
    216: "area_colhida_ha",
    214: "quantidade_produzida_t",
    112: "rendimento_medio_kg_ha",
    215: "valor_producao_mil_reais",
}
COLUNAS = ["ano", "codigo_uf", "id_municipio", "produto"]
for nome in VARIAVEIS.values():
    COLUNAS.extend([nome, f"simbolo_{nome}"])


def coletar(ano=2024, timeout=90):
    resultado = []
    for uf, municipio, produto, categoria in CASOS:
        linha = dict(ano=ano, codigo_uf=uf, id_municipio=municipio, produto=produto)
        for variavel, campo in VARIAVEIS.items():
            url = (f"https://apisidra.ibge.gov.br/values/t/5457/n6/{municipio}"
                   f"/v/{variavel}/p/{ano}/c782/{categoria}/f/a")
            req = urllib.request.Request(url, headers={"User-Agent": "atlas-agro-pol/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    dados = json.load(resp)
            except urllib.error.HTTPError as exc:
                detalhe = exc.read(1200).decode("utf-8", errors="replace")
                raise RuntimeError(f"SIDRA HTTP {exc.code}; URL={url}; {detalhe}") from exc
            registros = interpretar(dados, ano, uf, produto)
            if len(registros) != 1 or registros[0]["id_municipio"] != municipio:
                raise ValueError(f"Resposta não corresponde ao município: {url}")
            registro = registros[0]
            linha[campo] = registro["valor_producao_mil_reais"]
            linha[f"simbolo_{campo}"] = registro["simbolo_sidra"]
        resultado.append(linha)
        print(f"OK {municipio} / {produto}", flush=True)
    return resultado


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", type=int, default=2024)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    linhas = coletar(args.ano)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUNAS)
        writer.writeheader()
        writer.writerows(linhas)
    print(f"Coletadas {len(linhas)} observações com {len(VARIAVEIS)} variáveis", flush=True)


if __name__ == "__main__":
    main()
