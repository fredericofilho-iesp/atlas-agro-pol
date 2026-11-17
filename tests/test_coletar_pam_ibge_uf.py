import unittest
from pipeline.coletar_pam_ibge_uf import interpretar


class ColetarPAMIBGEUF(unittest.TestCase):
    def test_resposta_sidra(self):
        dados = [
            {"N3": "UF (Código)", "C782": "Produto (Código)",
             "D3N": "Produto", "V": "Valor", "D2C": "Ano"},
            {"N3": "51", "C782": "40124", "D3N": "Soja (em grão)",
             "V": "123.0", "D2C": "2024"},
            {"N3": "35", "C782": "40124", "D3N": "Soja (em grão)",
             "V": "-", "D2C": "2024"},
        ]
        r = interpretar(dados, 2024)
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0]["valor_total_mil_reais"], "")
        self.assertEqual(r[1]["valor_total_mil_reais"], 123.)

    def test_esquema_invalido(self):
        with self.assertRaisesRegex(ValueError, "esquema"):
            interpretar([{}, {"V": "10"}], 2024)


if __name__ == "__main__":
    unittest.main()
