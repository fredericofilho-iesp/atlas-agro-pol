import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline import coletar_pam_indicadores as mod


HEADER = {
    "D1C": "Município (Código)", "D1N": "Município",
    "D2C": "Ano (Código)", "D2N": "Ano",
    "D3C": "Variável (Código)", "D3N": "Variável",
    "D4C": "Produto das lavouras temporárias e permanentes (Código)",
    "D4N": "Produto das lavouras temporárias e permanentes", "V": "Valor",
}


def linha(variavel="215", valor="100", municipio="1100015", produto="40124"):
    return {"D1C": municipio, "D2C": "2024", "D3C": variavel, "D4C": produto, "V": valor}


class TestIndicadoresPAM(unittest.TestCase):
    def test_variaveis_unidades_ausencias(self):
        dados = [HEADER, linha("8331", "10"), linha("216", "-"),
                 linha("214", "12.5"), linha("112", "1250"),
                 linha("215", "100")]
        result = mod.interpretar(dados, 2024, "11",
                                produtos={"Soja (em grão)": 40124})
        self.assertEqual(len(result), 5)
        por_variavel = {x["codigo_variavel"]: x for x in result}
        self.assertEqual(por_variavel["214"]["valor"], "12.5")
        self.assertEqual(por_variavel["214"]["unidade"], "t")
        self.assertEqual(por_variavel["216"]["valor"], "")
        self.assertEqual(por_variavel["216"]["simbolo_sidra"], "-")
        self.assertEqual(por_variavel["8331"]["unidade"], "ha")

    def test_rejeita_chaves_duplicadas(self):
        with self.assertRaisesRegex(ValueError, "duplicada"):
            mod.interpretar([HEADER, linha(), linha()], 2024, "11")

    def test_rejeita_codigo_produto_nao_solicitado(self):
        with self.assertRaisesRegex(ValueError, "Dimensão inesperada"):
            mod.interpretar([HEADER, linha(produto="99999")], 2024, "11")

    def test_rejeita_valores_negativos_e_invalidos(self):
        for valor in ("-2", "NaN", "Infinity", "texto"):
            with self.subTest(valor=valor), self.assertRaises(ValueError):
                mod.interpretar([HEADER, linha(valor=valor)], 2024, "11")

    def test_coleta_usa_multiplas_variaveis_e_culturas(self):
        with patch.object(mod, "consultar", return_value=[HEADER, linha()]) as consultar:
            registros, por_uf = mod.coletar(
                ano=2024, ufs=["11"], produtos={"Soja (em grão)": 40124},
                variaveis={"215": mod.VARIAVEIS["215"]},
            )
        self.assertEqual(len(registros), 1)
        self.assertEqual(por_uf, {"11": 1})
        url = consultar.call_args.args[0]
        self.assertIn("/v/215/p/2024/c782/40124/f/a", url)

    def test_manifesto_e_csv(self):
        registros = mod.interpretar([HEADER, linha()], 2024, "11")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "indicadores.csv"
            mod.salvar(registros, {"11": 1}, 2024, path)
            self.assertIn("1100015", path.read_text(encoding="utf-8"))
            self.assertIn("municipios", path.with_suffix(".manifesto.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
