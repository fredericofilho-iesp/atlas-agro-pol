import unittest
from pipeline.conciliar_pam_sidra_nacional import reconciliar


class TestReconciliacao(unittest.TestCase):
    def m(self,mun,valor):
        return dict(ano=2024,codigo_uf="11",id_municipio=mun,
                    produto="Milho (em grão)",valor_producao_mil_reais=valor)
    def uf(self,val):
        return dict(ano=2024,codigo_uf="11",produto="Milho (em grão)",
                    valor_total_mil_reais=val)
    def test_preserva_ausencia(self):
        r=reconciliar([self.m("1100015","-"),self.m("1100023","5")],[self.uf("5")])[0]
        self.assertEqual(r["municipios_sem_valor"],1)
        self.assertEqual(r["soma_municipal_mil_reais"],5)
        self.assertEqual(r["status"],"concordante")
    def test_todos_ausentes_nao_zerar(self):
        r=reconciliar([self.m("1100015","...")],[self.uf("")])[0]
        self.assertIsNone(r["soma_municipal_mil_reais"])
        self.assertEqual(r["status"],"ambos_ausentes")
    def test_discrepancia(self):
        r=reconciliar([self.m("1100015","7")],[self.uf("5")])[0]
        self.assertEqual(r["diferenca_mil_reais"],2)
        self.assertEqual(r["status"],"divergencia")
    def test_rejeita_duplicata(self):
        with self.assertRaisesRegex(ValueError,"duplicado"):
            reconciliar([self.m("1100015","2"),self.m("1100015","3")],[self.uf("5")])


if __name__=="__main__":
    unittest.main()
