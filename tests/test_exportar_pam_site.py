import unittest
from pipeline.exportar_pam_site import empacotar


class TestExportacaoSite(unittest.TestCase):
    def test_ausencia_e_codigo_municipal(self):
        r={"id_municipio":"1100015","produto":"Soja (em grão)",
           "status_auditoria":"ausentes_ambas","valor_sidra_mil_reais":"",
           "valor_bd_mil_reais":""}
        data=empacotar([r])
        self.assertEqual(data["rows"],[["1100015",0,None,None,2]])
    def test_rejeita_duplicata(self):
        r={"id_municipio":"1100015","produto":"Soja (em grão)",
           "status_auditoria":"concordante","valor_sidra_mil_reais":"3",
           "valor_bd_mil_reais":"3"}
        with self.assertRaises(ValueError):
            empacotar([r,r])


if __name__=="__main__":
    unittest.main()
