"""Leitura e gravação de tabelas CSV (opcionalmente .gz) só com a biblioteca padrão."""
from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Iterable

INTEIROS = {"codigo", "ano", "tabela", "uf_codigo", "variavel_id"}


def _abrir(caminho: Path, modo: str):
    if str(caminho).endswith(".gz"):
        return gzip.open(caminho, modo + "t", encoding="utf-8", newline="")
    return open(caminho, modo, encoding="utf-8", newline="")


def _texto(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else repr(v)
    if isinstance(v, list):
        return "|".join(str(x) for x in v)
    return str(v)


def gravar(linhas: Iterable[dict], caminho: Path, colunas: list[str]) -> int:
    n = 0
    with _abrir(caminho, "w") as f:
        w = csv.writer(f)
        w.writerow(colunas)
        for r in linhas:
            w.writerow([_texto(r.get(c)) for c in colunas])
            n += 1
    return n


def _converter(chave: str, valor: str):
    if valor == "":
        return None
    if chave in INTEIROS:
        try:
            return int(float(valor))
        except ValueError:
            return valor
    if chave in ("valor", "indice_medio") or chave.startswith(("vbp", "vab", "pib", "part_", "rank_", "fator")):
        try:
            return float(valor)
        except ValueError:
            return valor
    return valor


def ler(caminho: Path) -> list[dict]:
    with _abrir(caminho, "r") as f:
        return [{k: _converter(k, v) for k, v in r.items()} for r in csv.DictReader(f)]
