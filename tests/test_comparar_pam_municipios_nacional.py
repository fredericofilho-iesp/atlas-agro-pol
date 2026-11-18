import unittest
from pipeline.comparar_pam_municipios_nacional import comparar


def registro(municipio,valor,simbolo=None):
    r={"ano":"2024","codigo_uf":"11","id_municipio":municipio,
       "produto":"Milho (em grão)","valor_producao_mil_reais":valor}
    if simbolo is not None:
        r["simbolo_sidra"]=simbolo
    return r


class TestComparacaoNacional(unittest.TestCase):
    def test_todas_classes(self):
        bd=[registro("1100015","3"),registro("1100023","9"),
            registro("1100031",""),registro("1100049","5"),
            registro("1100056",""),registro("1100064","4")]
        sidra=[registro("1100015","3"),registro("1100023","8"),
               registro("1100031","11"),registro("1100049","-","-"),
               registro("1100056","...","..."),registro("1100072","6")]
        detalhe,resumo,ranking=comparar(bd,sidra)
        self.assertEqual(len(detalhe),7)
        self.assertEqual(len(ranking),1)
        counts=resumo[0]
        self.assertEqual(counts["iguais"],1)
        self.assertEqual(counts["divergentes"],1)
        self.assertEqual(counts["ausentes_bd"],1)
        self.assertEqual(counts["ausentes_sidra"],1)
        self.assertEqual(counts["ausentes_ambas"],1)
        self.assertEqual(counts["sem_linha_bd"],1)
        self.assertEqual(counts["sem_linha_sidra"],1)
    def test_duplicatas_sao_erro(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            comparar([registro("1100015","3"),registro("1100015","3")],[])


if __name__=="__main__":
    unittest.main()
