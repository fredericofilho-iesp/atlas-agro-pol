"""Diagnóstico leve da API oficial do IBGE (sem dependências externas).

Executar: python -m pipeline.diagnostico_api
Não altera dados nem executa coleta completa.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
TESTES = {
    "metadados_pam_5457": f"{BASE}/5457/metadados",
    "periodos_pam_5457": f"{BASE}/5457/periodos",
    "amostra_pam_rio_2023": (
        f"{BASE}/5457/periodos/2023/variaveis/214"
        "?localidades=N6%5B3304557%5D"
    ),
}

def testar(nome, url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "AtlasAgrarioPolitico/0.1 (pesquisa academica)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as resposta:
            corpo = resposta.read(1_000_000)
            status = resposta.status
        dados = json.loads(corpo)
        resumo = {
            "teste": nome, "status_http": status, "json_valido": True,
            "tipo": type(dados).__name__,
            "itens": len(dados) if isinstance(dados, (list, dict)) else None,
        }
        if nome.startswith("amostra"):
            resumo["amostra_estrutura"] = (
                list(dados[0].keys()) if isinstance(dados, list) and dados
                and isinstance(dados[0], dict) else []
            )
        return resumo
    except urllib.error.HTTPError as exc:
        return {"teste": nome, "erro": "HTTP", "status_http": exc.code}
    except Exception as exc:
        return {"teste": nome, "erro": type(exc).__name__, "detalhe": str(exc)[:220]}

def main():
    resultados = [testar(nome, url) for nome, url in TESTES.items()]
    print(json.dumps(resultados, ensure_ascii=False, indent=2))
    return 0 if all(r.get("json_valido") for r in resultados) else 1

if __name__ == "__main__":
    sys.exit(main())
