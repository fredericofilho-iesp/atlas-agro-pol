import unittest
from pipeline.coletar_pam_ibge_uf import interpretar


class ColetarPAMIBGEUF(unittest.TestCase):
    def test_resposta_sidra_com_cobertura_incompleta(self):
        dados = [
            {"D1C": "Unidade da Federação (Código)", "D1N": "Unidade da Federação",
             "D2C": "Ano (Código)", "D2N": "Ano",
             "D3C": "Variável (Código)", "D3N": "Variável",
             "D4C": "Produto das lavouras temporárias e permanentes (Código)",
             "D4N": "Produto das lavouras temporárias e permanentes",
             "V": "Valor"},
            {"D1C": "51", "D2C": "2024", "D3N": "Valor da produção",
             "D4N": "Soja (em grão)", "V": "123.0"},
            {"D1C": "35", "D2C": "2024", "D3N": "Valor da produção",
             "D4N": "Soja (em grão)", "V": "-"},
        ]
        with self.assertRaisesRegex(ValueError, "Cobertura incompleta"):
            interpretar(dados, 2024)

    def test_esquema_invalido(self):
        with self.assertRaisesRegex(ValueError, "esquema"):
            interpretar([{}, {"V": "10"}], 2024)


if __name__ == "__main__":
    unittest.main()
