import unittest
from pipeline.gerar_camada_qualidade_pam import construir


class TestCamadaQualidade(unittest.TestCase):
    def row(self,bd,sidra,merge="both",simbolo=""):
        return {"ano":"2024","codigo_uf":"11","id_municipio":"1100015",
                "produto":"Milho (em grão)","valor_producao_mil_reais_bd":bd,
                "valor_producao_mil_reais_sidra":sidra,
                "simbolo_sidra":simbolo,"_merge":merge}
    def test_divergente_preserva_duas_fontes(self):
        x=construir([self.row("15","10")],"2026-11-17","")[0]
        self.assertEqual(x["status_auditoria"],"divergente")
        self.assertEqual(x["valor_referencia_mil_reais"],10)
        self.assertEqual(x["diferenca_relativa_sidra_pct"],50)
    def test_ausencia_nao_e_zero(self):
        x=construir([self.row("4","","both","-")],"2026-11-17","")[0]
        self.assertEqual(x["status_auditoria"],"ausentes_sidra")
        self.assertIsNone(x["valor_referencia_mil_reais"])
    def test_falta_linha_bd(self):
        x=construir([self.row("","","right_only","...")],"2026-11-17","")[0]
        self.assertEqual(x["status_auditoria"],"sem_linha_bd")
    def test_chave_duplicada(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            construir([self.row("1","1"),self.row("1","1")],"2026-11-17","")


if __name__=="__main__":
    unittest.main()
