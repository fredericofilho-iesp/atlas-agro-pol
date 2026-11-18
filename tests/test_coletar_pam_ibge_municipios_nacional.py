import unittest
from unittest.mock import patch
from pipeline import coletar_pam_ibge_municipios_nacional as mod


class TestColetaNacional(unittest.TestCase):
    def test_cobertura_e_chaves(self):
        dados=[{"ano":2024,"codigo_uf":"11","id_municipio":"1100015",
                "produto":"Milho (em grão)","valor_producao_mil_reais":None,
                "simbolo_sidra":"-"}]
        with patch.object(mod,"consultar",return_value=[{"cab":"x"},{"row":"x"}]), \
             patch.object(mod,"interpretar",return_value=dados):
            resultado=mod.coletar(ufs=("11",),produtos={"Milho (em grão)":40122})
        self.assertEqual(len(resultado),1)
        self.assertEqual(resultado[0]["simbolo_sidra"],"-")

    def test_rejeita_uf_desconhecida(self):
        with self.assertRaises(ValueError):
            mod.coletar(ufs=("99",),produtos={"Milho (em grão)":40122})

    def test_rejeita_duplicatas(self):
        linha={"ano":2024,"codigo_uf":"11","id_municipio":"1100015",
               "produto":"Milho (em grão)","valor_producao_mil_reais":10,
               "simbolo_sidra":"10"}
        with patch.object(mod,"consultar",return_value=[]), \
             patch.object(mod,"interpretar",return_value=[linha,linha]):
            with self.assertRaisesRegex(ValueError,"duplicadas"):
                mod.coletar(ufs=("11",),produtos={"Milho (em grão)":40122})


if __name__=="__main__":
    unittest.main()
