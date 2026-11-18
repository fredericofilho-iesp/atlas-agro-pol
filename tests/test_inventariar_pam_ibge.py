import unittest
from pipeline.inventariar_pam_ibge import inventariar


class TestInventarioPAM(unittest.TestCase):
    def test_preserva_codigos_unidades_e_categorias(self):
        dados = {
            "nome": "PAM",
            "variaveis": [
                {"id": 215, "nome": "Valor da produção", "unidade": "Mil Reais"},
                {"id": 214, "nome": "Quantidade produzida", "unidade": "Toneladas"},
            ],
            "classificacoes": [{
                "id": 782, "nome": "Produto das lavouras",
                "categorias": [{"id": 40122, "nome": "Milho (em grão)"}],
            }],
        }
        resultado = inventariar(dados)
        self.assertEqual([v["id"] for v in resultado["variaveis"]], ["215", "214"])
        self.assertEqual(resultado["variaveis"][0]["unidade"], "Mil Reais")
        self.assertEqual(resultado["classificacoes"][0]["categorias"][0]["id"], "40122")

    def test_rejeita_variavel_incompleta(self):
        with self.assertRaises(ValueError):
            inventariar({"variaveis": [{"id": 215}]})


if __name__ == "__main__":
    unittest.main()
