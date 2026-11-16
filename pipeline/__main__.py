"""Roda a Fase 1 inteira: coleta + indicadores + exportação para o site.

    python -m pipeline

O andamento aparece na tela e também em coleta_log.txt; ao final,
coleta_status.txt recebe OK ou ERRO.
"""
import logging
import traceback

from . import coletar, config, indicadores

if __name__ == "__main__":
    fmt = logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")
    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)
    for h in (logging.StreamHandler(), logging.FileHandler(config.RAIZ / "coleta_log.txt", encoding="utf-8")):
        h.setFormatter(fmt)
        raiz.addHandler(h)
    status = config.RAIZ / "coleta_status.txt"
    status.write_text("RODANDO", encoding="utf-8")
    try:
        coletar.main([])
        indicadores.main()
    except BaseException:
        logging.error(traceback.format_exc())
        status.write_text("ERRO", encoding="utf-8")
        raise
    status.write_text("OK", encoding="utf-8")
    logging.info("Concluído.")
