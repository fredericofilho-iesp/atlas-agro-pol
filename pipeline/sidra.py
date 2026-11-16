"""Cliente mínimo e robusto para as APIs do SIDRA/IBGE.

- Metadados e períodos: https://servicodados.ibge.gov.br/api/v3/agregados/{t}/...
- Valores: https://apisidra.ibge.gov.br/values/t/{t}/...

Pontos de projeto:
* variáveis e categorias são resolvidas pelo nome, ignorando acentos;
* as requisições são fatiadas por UF, variável e blocos de anos para não
  estourar o limite de valores por consulta;
* cada resposta bruta fica em cache (data/raw/sidra), então rodar de novo
  só baixa o que é novo;
* os símbolos especiais do IBGE viram números ou ausência:
  "-" (zero absoluto) -> 0; "X" (sigilo), "..", "..." -> NaN.

Uso de linha de comando para inspecionar uma tabela:
    python -m pipeline.sidra --listar 5457
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import logging
import math
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

log = logging.getLogger(__name__)

URL_DESCRICAO = "https://apisidra.ibge.gov.br/desctabapi.aspx?c={t}"
URL_VALORES = "https://apisidra.ibge.gov.br/values"

# Trechos que nunca interessam ao procurar variáveis pelo nome
EXCLUSOES_PADRAO = ("percentual", "participacao")

SIMBOLOS_ZERO = {"-"}
SIMBOLOS_AUSENTE = {"X", "..", "...", ""}

DIMENSOES_TERRITORIAIS = {"municipio", "unidade da federacao", "brasil", "grande regiao"}
DIMENSOES_TEMPORAIS = ("ano", "mes", "trimestre", "semestre")

# Número máximo de municípios numa UF (MG tem 853); usado para fatiar requisições.
MAX_MUNICIPIOS_UF = 900


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e com espaços simples."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.casefold().split())


def para_numero(valor: str | float | None) -> float:
    if valor is None:
        return math.nan
    if isinstance(valor, (int, float)):
        return float(valor)
    v = valor.strip()
    if v in SIMBOLOS_ZERO:
        return 0.0
    if v in SIMBOLOS_AUSENTE:
        return math.nan
    try:
        return float(v)
    except ValueError:
        return math.nan


def _sessao() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=5, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET",))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "atlas-agrario-politico (pesquisa academica)"
    return s


SESSAO = _sessao()


def _get_json(url: str, timeout: int = 180):
    resp = SESSAO.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} em {url}: {resp.text[:300]}")
    try:
        return resp.json()
    except ValueError as exc:  # a apisidra devolve texto puro em erros
        raise RuntimeError(f"Resposta não-JSON em {url}: {resp.text[:300]}") from exc


# ---------------------------------------------------------------------------
# Metadados
# ---------------------------------------------------------------------------
@dataclass
class Metadados:
    tabela: int
    bruto: dict
    periodos: list[str]

    @property
    def nome(self) -> str:
        return self.bruto.get("nome", "")

    @property
    def variaveis(self) -> list[dict]:
        return self.bruto.get("variaveis", [])

    @property
    def classificacoes(self) -> list[dict]:
        return self.bruto.get("classificacoes", [])

    def variavel_id(self, inclui: Iterable[str], exclui: Iterable[str] = ()) -> int:
        inclui = [normalizar(x) for x in inclui]
        exclui = [normalizar(x) for x in (*exclui, *EXCLUSOES_PADRAO)]
        candidatos = [
            v for v in self.variaveis
            if all(t in normalizar(v["nome"]) for t in inclui)
            and not any(t in normalizar(v["nome"]) for t in exclui)
        ]
        if len(candidatos) != 1:
            disponiveis = "\n".join(f"  {v['id']}: {v['nome']}" for v in self.variaveis)
            raise LookupError(
                f"Tabela {self.tabela}: {len(candidatos)} variáveis casam com "
                f"inclui={inclui} exclui={exclui}. Variáveis disponíveis:\n{disponiveis}"
            )
        return int(candidatos[0]["id"])

    def n_categorias(self) -> int:
        """Produto do número de categorias de todas as classificações."""
        n = 1
        for c in self.classificacoes:
            n *= max(1, len(c.get("categorias", [])))
        return n

    def periodos_desde(self, ano_inicio: int) -> list[str]:
        return [p for p in self.periodos if int(str(p)[:4]) >= ano_inicio]


_SPAN = re.compile(r'<span id="([^"]+)"[^>]*>(.*?)</span>', re.S)
_TAG = re.compile(r"<[^>]+>")


def interpretar_desctabapi(pagina: str) -> dict:
    """Lê a página https://apisidra.ibge.gov.br/desctabapi.aspx?c=<tabela>.

    Devolve um dicionário no mesmo formato dos metadados da API de agregados
    (nome, variaveis, classificacoes) mais a lista de períodos.
    """
    campos = {i: html.unescape(_TAG.sub("", t)).strip() for i, t in _SPAN.findall(pagina)}
    variaveis = []
    for chave, valor in campos.items():
        m = re.fullmatch(r"lstVariaveis_lblIdVariavel_(\d+)", chave)
        if m:
            nome = campos.get(f"lstVariaveis_lblNomeVariavel_{m.group(1)}", "")
            variaveis.append({"id": int(valor), "nome": nome.split(" - casas decimais")[0].strip()})
    classificacoes = []
    for chave, valor in campos.items():
        m = re.fullmatch(r"lstClassificacoes_lblIdClassificacao_(\d+)", chave)
        if not m:
            continue
        i = m.group(1)
        cats = []
        for ck, cv in campos.items():
            mc = re.fullmatch(rf"lstClassificacoes_lstCategorias_{i}_lblIdCategoria_(\d+)", ck)
            if mc:
                cats.append({"id": int(cv),
                             "nome": campos.get(f"lstClassificacoes_lstCategorias_{i}_lblNomeCategoria_{mc.group(1)}", "")})
        classificacoes.append({"id": int(valor), "nome": campos.get(f"lstClassificacoes_lblClassificacao_{i}", ""),
                               "categorias": cats})
    periodos = [p.strip() for p in campos.get("lblPeriodoDisponibilidade", "").split(",") if p.strip()]
    if not variaveis:
        msg = campos.get("lblMensagem") or "página sem variáveis"
        raise RuntimeError(f"Descrição da tabela ilegível: {msg}")
    return {"nome": campos.get("lblNomeTabela", ""), "variaveis": variaveis,
            "classificacoes": classificacoes, "periodos": periodos}


def _get_texto(url: str, timeout: int = 120) -> str:
    resp = SESSAO.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code} em {url}: {resp.text[:300]}")
    return resp.text


def metadados(tabela: int) -> Metadados:
    """Metadados pela página de descrição do apisidra.

    (A API servicodados.ibge.gov.br, que também tem metadados, costuma
    recusar conexões de fora do Brasil; o apisidra não.)
    """
    bruto = interpretar_desctabapi(_get_texto(URL_DESCRICAO.format(t=tabela)))
    destino = config.RAW / "sidra" / str(tabela)
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "metadados.json").write_text(json.dumps(bruto, ensure_ascii=False, indent=1))
    return Metadados(tabela=tabela, bruto=bruto, periodos=bruto["periodos"])


def testar_conexao() -> None:
    """Falha cedo, com mensagem clara, se o apisidra não responder."""
    try:
        _get_texto(URL_DESCRICAO.format(t=1737), timeout=30)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "Não foi possível acessar apisidra.ibge.gov.br. O IBGE costuma bloquear "
            "algumas redes estrangeiras (inclusive servidores do GitHub). Rode o pipeline "
            f"no seu computador ou numa rede com acesso ao IBGE.\nDetalhe: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Valores
# ---------------------------------------------------------------------------
def montar_url(tabela: int, nivel: str, variaveis: list[int], periodos: list[str],
               uf: int | None = None, classificacoes: dict[int, str] | None = None) -> str:
    territorio = f"{nivel}/in n3 {uf}" if (uf is not None and nivel == "n6") else f"{nivel}/all"
    partes = [
        URL_VALORES,
        f"t/{tabela}",
        territorio,
        "v/" + ",".join(str(v) for v in variaveis),
        "p/" + ",".join(periodos),
    ]
    for cid, cats in (classificacoes or {}).items():
        partes.append(f"c{cid}/{cats}")
    partes.append("d/m")  # máximo de casas decimais
    return "/".join(partes)


def interpretar_resposta(dados: list[dict]) -> pd.DataFrame:
    """Converte a resposta da apisidra (cabeçalho + linhas) num DataFrame arrumado.

    Colunas de saída: codigo, territorio, periodo, variavel_id, variavel,
    unidade, valor e, para cada classificação, categoria_codigo / categoria
    (com sufixo _2, _3... quando há mais de uma).
    """
    if not dados or len(dados) < 2:
        return pd.DataFrame()
    cabecalho, linhas = dados[0], dados[1:]
    df = pd.DataFrame(linhas)

    # mapeia rótulo -> chave (D1C, D1N, ...)
    dims: dict[str, dict[str, str]] = {}
    for chave, rotulo in cabecalho.items():
        if rotulo is None:  # dimensões vazias (D4..D9 = null)
            continue
        if chave.startswith("D") and chave[-1] in "CN":
            base = rotulo.replace(" (Código)", "")
            dims.setdefault(base, {})["C" if chave.endswith("C") else "N"] = chave

    saida = pd.DataFrame(index=df.index)
    n_class = 0
    for base, chaves in dims.items():
        b = normalizar(base)
        cod = df[chaves["C"]] if "C" in chaves else None
        nom = df[chaves["N"]] if "N" in chaves else None
        if b in DIMENSOES_TERRITORIAIS:
            saida["codigo"] = cod
            saida["territorio"] = nom
        elif b.startswith(DIMENSOES_TEMPORAIS):
            saida["periodo"] = cod
        elif b == "variavel":
            saida["variavel_id"] = pd.to_numeric(cod)
            saida["variavel"] = nom
        else:
            n_class += 1
            suf = "" if n_class == 1 else f"_{n_class}"
            saida[f"categoria_codigo{suf}"] = cod
            saida[f"categoria{suf}"] = nom
    saida["unidade"] = df.get("MN")
    saida["valor"] = df["V"].map(para_numero)
    return saida


def baixar(tabela: int, nivel: str, variaveis: list[int], periodos: list[str],
           uf: int | None = None, classificacoes: dict[int, str] | None = None,
           usar_cache: bool = True) -> pd.DataFrame:
    url = montar_url(tabela, nivel, variaveis, periodos, uf, classificacoes)
    destino = config.RAW / "sidra" / str(tabela)
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".json")
    if usar_cache and arquivo.exists():
        dados = json.loads(arquivo.read_text())
    else:
        log.info("GET %s", url)
        dados = _get_json(url)
        arquivo.write_text(json.dumps(dados, ensure_ascii=False))
        time.sleep(config.PAUSA_ENTRE_REQUISICOES)
    return interpretar_resposta(dados)


def fatiar_periodos(periodos: list[str], valores_por_periodo: int, limite: int) -> list[list[str]]:
    """Agrupa períodos em blocos que respeitam o limite de valores por requisição."""
    por_bloco = max(1, limite // max(1, valores_por_periodo))
    return [periodos[i:i + por_bloco] for i in range(0, len(periodos), por_bloco)]


def coletar(nome_fonte: str, ano_inicio: int | None = None, usar_cache: bool = True) -> pd.DataFrame:
    """Baixa uma fonte definida em config.TABELAS e devolve um DataFrame arrumado.

    A coluna "medida" recebe o apelido da variável definido no config
    (ex.: "valor_mil_reais"), para que o resto do pipeline não dependa de nomes
    longos do IBGE.
    """
    spec = config.TABELAS[nome_fonte]
    meta = metadados(spec["tabela"])
    ano_inicio = ano_inicio if ano_inicio is not None else config.ANO_INICIO
    periodos = meta.periodos_desde(ano_inicio)
    if not periodos:
        raise RuntimeError(f"Tabela {spec['tabela']} sem períodos a partir de {ano_inicio}")

    apelidos = {meta.variavel_id(**regra): apelido for apelido, regra in spec["variaveis"].items()}
    limite = config.MAX_VALORES_POR_REQUISICAO
    unidades_por_periodo = MAX_MUNICIPIOS_UF if spec["nivel"] == "n6" else 1

    # Conjuntos de classificações a pedir em cada requisição
    grupos_class: list[dict[int, str] | None] = [None]
    n_cat = 1
    nomes_cat = spec.get("classificacao", {}).get("categorias")
    if nomes_cat:
        # só as categorias pedidas pelo nome (ex.: ["Total"]) da 1ª classificação
        c = meta.classificacoes[0]
        alvo = {normalizar(n) for n in nomes_cat}
        ids = [str(cat["id"]) for cat in c["categorias"] if normalizar(cat["nome"]) in alvo]
        if len(ids) != len(alvo):
            raise LookupError(f"Tabela {spec['tabela']}: categorias {nomes_cat} não encontradas em c{c['id']}")
        grupos_class = [{int(c["id"]): ",".join(ids)}]
        n_cat = len(ids)
    elif spec.get("classificacao", {}).get("todas_categorias"):
        n_cat = meta.n_categorias()
        if unidades_por_periodo * n_cat <= limite or len(meta.classificacoes) != 1:
            grupos_class = [{int(c["id"]): "all" for c in meta.classificacoes}]
        else:
            # uma classificação com muitas categorias (ex.: PAM): fatia as categorias
            c = meta.classificacoes[0]
            ids = [str(cat["id"]) for cat in c.get("categorias", [])]
            por_grupo = max(1, limite // unidades_por_periodo)
            grupos_class = [{int(c["id"]): ",".join(ids[i:i + por_grupo])}
                            for i in range(0, len(ids), por_grupo)]
            n_cat = por_grupo

    ufs: list[int | None] = list(config.UFS) if spec["nivel"] == "n6" else [None]
    blocos = fatiar_periodos(periodos, unidades_por_periodo * n_cat, limite)

    partes = []
    total = len(ufs) * len(apelidos) * len(blocos) * len(grupos_class)
    feito = 0
    for uf in ufs:
        for var_id in apelidos:
            for bloco in blocos:
                for classif in grupos_class:
                    feito += 1
                    log.info("[%s] %d/%d  UF=%s var=%s períodos=%s..%s", nome_fonte, feito, total,
                             uf, var_id, bloco[0], bloco[-1])
                    partes.append(baixar(spec["tabela"], spec["nivel"], [var_id], bloco, uf,
                                         classif, usar_cache))
    df = pd.concat([p for p in partes if not p.empty], ignore_index=True)
    df["medida"] = df["variavel_id"].map(apelidos)
    df["fonte"] = nome_fonte
    df["tabela"] = spec["tabela"]
    return df


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------
def _main() -> None:
    ap = argparse.ArgumentParser(description="Inspeciona tabelas do SIDRA")
    ap.add_argument("--listar", type=int, metavar="TABELA", help="lista variáveis e classificações")
    args = ap.parse_args()
    if args.listar:
        m = metadados(args.listar)
        print(f"Tabela {m.tabela}: {m.nome}")
        print(f"Períodos: {m.periodos[0]} a {m.periodos[-1]} ({len(m.periodos)})")
        print("Variáveis:")
        for v in m.variaveis:
            print(f"  {v['id']}: {v['nome']} [{v.get('unidade')}]")
        for c in m.classificacoes:
            print(f"Classificação c{c['id']}: {c['nome']} ({len(c.get('categorias', []))} categorias)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    _main()
