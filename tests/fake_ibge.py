"""API do IBGE simulada, no mesmo formato das respostas reais, para testes offline."""
from __future__ import annotations

import re
from urllib.parse import unquote

MUNICIPIOS = {
    3304557: ("Rio de Janeiro", 33, "RJ", "Sudeste"),
    3300100: ("Angra dos Reis", 33, "RJ", "Sudeste"),
    5107925: ("Sorriso", 51, "MT", "Centro-Oeste"),
    5103403: ("Cuiabá", 51, "MT", "Centro-Oeste"),
}

ANOS = list(range(2014, 2026))

META = {
    1737: {"nome": "IPCA", "variaveis": [
        {"id": 2266, "nome": "IPCA - Número-índice (base: dezembro de 1993 = 100)", "unidade": "Número-índice"},
        {"id": 63, "nome": "IPCA - Variação mensal", "unidade": "%"}],
        "classificacoes": [], "periodos": [f"{a}{m:02d}" for a in range(2014, 2027) for m in range(1, 13)
                                          if (a, m) <= (2026, 9)]},
    5938: {"nome": "PIB dos Municípios", "variaveis": [
        {"id": 37, "nome": "Produto Interno Bruto a preços correntes", "unidade": "Mil Reais"},
        {"id": 593, "nome": "Produto Interno Bruto per capita a preços correntes", "unidade": "Reais"},
        {"id": 498, "nome": "Valor adicionado bruto a preços correntes total", "unidade": "Mil Reais"},
        {"id": 513, "nome": "Valor adicionado bruto a preços correntes da agropecuária", "unidade": "Mil Reais"},
        {"id": 497, "nome": "Participação do produto interno bruto a preços correntes no produto interno bruto a preços correntes da unidade da federação (%)", "unidade": "%"},
        {"id": 516, "nome": "Participação do valor adicionado bruto a preços correntes da agropecuária no valor adicionado bruto a preços correntes total (%) [2002 a 2021]", "unidade": "%"}],
        "classificacoes": [], "periodos": [str(a) for a in range(2014, 2024)]},
    5457: {"nome": "PAM", "variaveis": [
        {"id": 8331, "nome": "Área plantada ou destinada à colheita", "unidade": "Hectares"},
        {"id": 1000831, "nome": "Área plantada ou destinada à colheita - percentual do total geral", "unidade": "%"},
        {"id": 216, "nome": "Área colhida", "unidade": "Hectares"},
        {"id": 214, "nome": "Quantidade produzida", "unidade": "Toneladas"},
        {"id": 215, "nome": "Valor da produção", "unidade": "Mil Reais"},
        {"id": 1000215, "nome": "Valor da produção - percentual do total geral", "unidade": "%"}],
        "classificacoes": [{"id": 782, "nome": "Produto das lavouras temporárias e permanentes", "categorias": [
            {"id": 0, "nome": "Total"}, {"id": 40124, "nome": "Soja (em grão)"},
            {"id": 40122, "nome": "Milho (em grão)"}, {"id": 40119, "nome": "Mandioca"},
            {"id": 40139, "nome": "Café (em grão) Total"}, {"id": 40140, "nome": "Café (em grão) Arábica"}]}],
        "periodos": [str(a) for a in ANOS]},
    3939: {"nome": "PPM rebanhos", "variaveis": [
        {"id": 105, "nome": "Efetivo dos rebanhos", "unidade": "Cabeças"}],
        "classificacoes": [{"id": 79, "nome": "Tipo de rebanho", "categorias": [
            {"id": 2670, "nome": "Bovino"}, {"id": 32794, "nome": "Suíno - total"}]}],
        "periodos": [str(a) for a in ANOS]},
    74: {"nome": "PPM origem animal", "variaveis": [
        {"id": 106, "nome": "Produção de origem animal", "unidade": "Mil litros"},
        {"id": 215, "nome": "Valor da produção", "unidade": "Mil Reais"}],
        "classificacoes": [{"id": 80, "nome": "Tipo de produto de origem animal", "categorias": [
            {"id": 0, "nome": "Total"}, {"id": 2682, "nome": "Leite"}, {"id": 2685, "nome": "Ovos de galinha"}]}],
        "periodos": [str(a) for a in ANOS]},
    289: {"nome": "PEVS extração", "variaveis": [
        {"id": 144, "nome": "Quantidade produzida na extração vegetal", "unidade": "Toneladas"},
        {"id": 145, "nome": "Valor da produção na extração vegetal", "unidade": "Mil Reais"}],
        "classificacoes": [{"id": 193, "nome": "Tipo de produto extrativo", "categorias": [
            {"id": 0, "nome": "Total"}, {"id": 3402, "nome": "1 - Alimentícios"},
            {"id": 3403, "nome": "1.1 - Açaí (fruto)"}]}],
        "periodos": [str(a) for a in ANOS]},
    291: {"nome": "PEVS silvicultura", "variaveis": [
        {"id": 143, "nome": "Valor da produção na silvicultura", "unidade": "Mil Reais"}],
        "classificacoes": [{"id": 194, "nome": "Tipo de produto da silvicultura", "categorias": [
            {"id": 0, "nome": "Total"}, {"id": 3455, "nome": "1.1 - Carvão vegetal"}]}],
        "periodos": [str(a) for a in ANOS]},
}

# valores-base (mil R$ ou unidades) por município, crescendo 5% ao ano
BASE = {
    5457: {40124: {5107925: 3_000_000, 5103403: 0},
           40122: {5107925: 1_000_000, 5103403: 5_000, 3300100: 0},
           40119: {3304557: 800, 3300100: 1_200, 5103403: 4_000},
           40140: {3300100: 2_000}},
    3939: {2670: {5107925: 200_000, 5103403: 90_000, 3300100: 8_000},
           32794: {5107925: 300_000}},
    74: {2682: {5103403: 20_000, 3300100: 3_000}, 2685: {5107925: 1_000}},
    289: {3403: {5103403: 500}},
    291: {3455: {5107925: 15_000}},
}
SIGILO = {(5457, 40119, 5103403, 2020)}  # célula "X"


def _valor_base(t, cat, cod, ano, var):
    if (t, cat, cod, ano) in SIGILO:
        return "X"
    v = BASE.get(t, {}).get(cat, {}).get(cod, 0) * (1.05 ** (ano - 2014))
    if t == 5457 and var == 8331:   # área: escala diferente
        v = v / 2
    return "-" if v == 0 else f"{v:.3f}"


FOLHAS_SOMADAS = {5457: {40124, 40122, 40119, 40140}, 3939: {2670, 32794}, 74: {2682, 2685},
                  289: {3403}, 291: {3455}}
SUBTOTAIS = {(5457, 40139): [40140], (289, 3402): [3403]}


def _valor(t, cat_id, cod, ano, var):
    if (t, cat_id) in SUBTOTAIS:
        partes = [_valor_base(t, c, cod, ano, var) for c in SUBTOTAIS[(t, cat_id)]]
        soma = sum(0 if x in ("-", "X") else float(x) for x in partes)
        return "-" if soma == 0 else f"{soma:.3f}"
    cats = list(FOLHAS_SOMADAS.get(t, [])) + [0]
    total = 0
    if cat_id == total:
        soma = 0.0
        for c in cats:
            if c == total:
                continue
            x = _valor_base(t, c, cod, ano, var)
            soma += 0 if x in ("-", "X") else float(x)
        return "-" if soma == 0 else f"{soma:.3f}"
    return _valor_base(t, cat_id, cod, ano, var)


def _pib(cod, ano, var):
    pib = {3304557: 350e6, 3300100: 12e6, 5107925: 9e6, 5103403: 30e6}[cod] * (1.06 ** (ano - 2014))
    agro = {3304557: 0.0005, 3300100: 0.01, 5107925: 0.45, 5103403: 0.02}[cod]
    if var == 37:
        return f"{pib:.0f}"
    if ano > 2021:   # como no IBGE: sem abertura setorial depois de 2021
        return "..."
    if var == 498:
        return f"{pib * 0.88:.0f}"
    if var == 513:
        return f"{pib * 0.88 * agro:.0f}"
    return "..."


def _ipca(periodo):
    a, m = int(periodo[:4]), int(periodo[4:])
    n = (a - 2014) * 12 + (m - 1)
    return f"{3800 * (1.004 ** n):.2f}"


def resposta(url: str):
    url = unquote(url)
    if "servicodados" in url:
        raise RuntimeError("Connection to servicodados.ibge.gov.br timed out")  # como de fora do Brasil
    if "desctabapi" in url:
        return descricao_html(int(url.rsplit("=", 1)[1]))
    return _values(url)


def descricao_html(t: int) -> str:
    """Página desctabapi.aspx no mesmo formato de spans do IBGE."""
    m = META[t]
    spans = [f'<span id="lblNumeroTabela" class="tituloTabelaNro">{t}</span>',
             f'<span id="lblNomeTabela" class="tituloTabelaDesc">{m["nome"]}</span>',
             f'<span id="lblPeriodoDisponibilidade" style="color:Red;">{", ".join(m["periodos"])}</span>']
    for i, v in enumerate(m["variaveis"]):
        spans.append(f'<span id="lstVariaveis_lblIdVariavel_{i}" style="color:Red">{v["id"]}</span>')
        spans.append(f'<span id="lstVariaveis_lblNomeVariavel_{i}">{v["nome"]} ({v["unidade"]}) '
                     f'- casas decimais:  padrão = 0, máximo = 0</span>')
    for i, c in enumerate(m["classificacoes"]):
        spans.append(f'<span id="lstClassificacoes_lblIdClassificacao_{i}" style="color:Red; font-weight:bold">{c["id"]}</span>')
        spans.append(f'<span id="lstClassificacoes_lblClassificacao_{i}" class="tituloLinha">{c["nome"]}</span>')
        for j, cat in enumerate(c["categorias"]):
            spans.append(f'<span id="lstClassificacoes_lstCategorias_{i}_lblIdCategoria_{j}" style="color:Red">{cat["id"]}</span>')
            spans.append(f'<span id="lstClassificacoes_lstCategorias_{i}_lblNomeCategoria_{j}">{cat["nome"]}</span>')
    return "<html><body>" + "\n".join(spans) + "</body></html>"


def _values(url):
    t = int(re.search(r"/t/(\d+)/", url).group(1))
    vars_ = [int(x) for x in re.search(r"/v/([\d,]+)/", url).group(1).split(",")]
    pers = re.search(r"/p/([\d,]+)", url).group(1).split(",")
    mc = re.search(r"/c(\d+)/([\w,]+)", url)
    uf = re.search(r"in n3 (\d+)", url)
    meta = META[t]
    header = {"NC": "Nível Territorial (Código)", "NN": "Nível Territorial", "MC": "Unidade de Medida (Código)",
              "MN": "Unidade de Medida", "V": "Valor"}
    header.update({f"D{k}{x}": None for k in range(4, 10) for x in "CN"})  # como no apisidra real
    if t == 1737:
        header.update({"D1C": "Brasil (Código)", "D1N": "Brasil", "D2C": "Variável (Código)", "D2N": "Variável",
                       "D3C": "Mês (Código)", "D3N": "Mês"})
        rows = [{"NC": "1", "NN": "Brasil", "MC": "30", "MN": "Número-índice", "V": _ipca(p),
                 "D1C": "1", "D1N": "Brasil", "D2C": str(v), "D2N": "IPCA", "D3C": p, "D3N": p}
                for v in vars_ for p in pers]
        return [header, *rows]

    header.update({"D1C": "Município (Código)", "D1N": "Município", "D2C": "Variável (Código)",
                   "D2N": "Variável", "D3C": "Ano (Código)", "D3N": "Ano"})
    cats = [None]
    if mc:
        classif = meta["classificacoes"][0]
        header.update({"D4C": f"{classif['nome']} (Código)", "D4N": classif["nome"]})
        todas = {c["id"]: c["nome"] for c in classif["categorias"]}
        pedidas = list(todas) if mc.group(2) == "all" else [int(x) for x in mc.group(2).split(",")]
        cats = [(c, todas[c]) for c in pedidas]
    nomes_var = {v["id"]: v["nome"] for v in meta["variaveis"]}
    munis = [c for c, info in MUNICIPIOS.items() if uf is None or info[1] == int(uf.group(1))]
    rows = []
    for cod in munis:
        for v in vars_:
            for p in pers:
                for cat in cats:
                    if t == 5938:
                        val = _pib(cod, int(p), v)
                    else:
                        val = _valor(t, cat[0], cod, int(p), v)
                    r = {"NC": "6", "NN": "Município", "MC": "1", "MN": "Mil Reais", "V": val,
                         "D1C": str(cod), "D1N": f"{MUNICIPIOS[cod][0]} - {MUNICIPIOS[cod][2]}", "D2C": str(v), "D2N": nomes_var[v],
                         "D3C": p, "D3N": p}
                    r.update({f"D{k}{x}": None for k in range(4, 10) for x in "CN"})
                    if cat:
                        r.update({"D4C": str(cat[0]), "D4N": cat[1]})
                    rows.append(r)
    return [header, *rows]
