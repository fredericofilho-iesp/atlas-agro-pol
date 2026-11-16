"""Importa exportação CSV da PAM/Base dos Dados para o esquema do Atlas.

Entrada: resultado da consulta docs/sql/pam_bd_2024.sql, com colunas:
    ano,id_municipio,produto,valor_producao,tipo_lavoura

Uso: python -m pipeline.importar_bd_pam --entrada /caminho/pam_bd_2024.csv
Não usa API do IBGE, BigQuery, pandas nem bibliotecas compiladas.
"""
from __future__ import annotations

import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path

from . import config, tabelas

log = logging.getLogger(__name__)
COLUNAS = [
    "codigo", "territorio", "ano", "medida", "categoria_codigo",
    "categoria", "unidade", "valor", "tabela",
]
TIPOS = {"permanente", "temporaria"}
COLUNAS_ENTRADA = {"ano", "id_municipio", "produto", "valor_producao", "tipo_lavoura"}


def converter_linhas(caminho: Path) -> tuple[list[dict], dict]:
    if not caminho.is_file():
        raise FileNotFoundError(caminho)
    saida = []
    totais = defaultdict(float)
    grupos = set()
    incompletos = set()
    chaves = set()
    n_nulos = 0
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames or not COLUNAS_ENTRADA.issubset(leitor.fieldnames):
            raise ValueError("CSV não contém as colunas exigidas: " + ", ".join(sorted(COLUNAS_ENTRADA)))
        for numero, r in enumerate(leitor, start=2):
            try:
                codigo = str(r["id_municipio"]).strip()
                ano = int(r["ano"])
                tipo = str(r["tipo_lavoura"]).strip().lower()
                produto = str(r["produto"]).strip()
                if len(codigo) != 7 or not codigo.isdigit() or ano < 1974 or ano > 2100:
                    raise ValueError("município ou ano inválido")
                if tipo not in TIPOS or not produto or produto.lower() == "total":
                    raise ValueError("tipo_lavoura ou produto inválido")
                chave = (codigo, ano, tipo, produto)
                if chave in chaves:
                    raise ValueError("linha duplicada (município, ano, tipo, produto)")
                chaves.add(chave)
                valor_txt = str(r["valor_producao"] or "").strip()
                valor = None if valor_txt.lower() in ("", "null", "none", "nan") else float(valor_txt)
                if valor is not None and (valor < 0 or valor != valor or valor == float("inf")):
                    raise ValueError("valor inválido ou negativo")
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Linha {numero} do CSV: {exc}") from exc
            grupo = (int(codigo), ano)
            grupos.add(grupo)
            if valor is None:
                incompletos.add(grupo)
                n_nulos += 1
            else:
                totais[grupo] += valor
            saida.append({
                "codigo": int(codigo), "territorio": "", "ano": ano,
                "medida": "valor_mil_reais", "categoria_codigo": "",
                "categoria": produto, "unidade": "Mil Reais",
                "valor": valor, "tabela": 5457,
            })
    if not saida:
        raise ValueError("CSV vazio: nenhuma observação importada")
    # Não somar valores parciais se houver qualquer componente ausente.
    for codigo, ano in sorted(grupos - incompletos):
        saida.append({
            "codigo": codigo, "territorio": "", "ano": ano,
            "medida": "valor_mil_reais", "categoria_codigo": "",
            "categoria": "Total", "unidade": "Mil Reais",
            "valor": totais[codigo, ano], "tabela": 5457,
        })
    info = {
        "linhas_produtos": len(chaves), "municipio_ano": len(grupos),
        "municipio_ano_completo": len(grupos - incompletos),
        "municipio_ano_incompleto": len(incompletos),
        "valores_nulos": n_nulos,
        "aviso": "Total calculado somente quando todos os produtos observados têm valor. "
                 "Municípios ausentes do CSV não são imputados como zero.",
    }
    return saida, info


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--entrada", required=True, type=Path)
    ap.add_argument("--saida", type=Path, default=config.INTERIM / "pam.csv.gz")
    args = ap.parse_args(argv)
    linhas, info = converter_linhas(args.entrada)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    tabelas.gravar(linhas, args.saida, COLUNAS)
    for chave, valor in info.items():
        log.info("%s: %s", chave, valor)
    print(f"Importação concluída: {args.saida} | {info}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
