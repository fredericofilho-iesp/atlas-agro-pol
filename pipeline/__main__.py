"""Roda a Fase 1 inteira: coleta + indicadores + exportação para o site.

    python -m pipeline
"""
import logging

from . import coletar, indicadores

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    coletar.main([])
    indicadores.main()
