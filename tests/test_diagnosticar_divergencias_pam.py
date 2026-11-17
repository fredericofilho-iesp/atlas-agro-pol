import unittest
from pipeline.diagnosticar_divergencias_pam import diagnosticar

class DiagnosticoMunicipal(unittest.TestCase):
    def linha(self, municipio, bd, sidra):
        return dict(ano="2024", codigo_uf="52", id_municipio=municipio,
                    produto="Milho (em grão)",
                    valor_producao_mil_reais_bd=bd,
                    valor_producao_mil_reais_sidra=sidra,
                    simbolo_sidra=sidra)

    def test_diferencas_e_ausencias(self):
        linhas = [self.linha("5200001", "100", "90"),
                  self.linha("5200002", "", "-"),
                  self.linha("5200003", "20", ""),
                  self.linha("5200004", "8", "8")]
        detalhe, ranking, resumo = diagnosticar(linhas)
        self.assertEqual(len(detalhe), 4)
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["delta_bd_menos_sidra"], 10.0)
        self.assertEqual(resumo[0]["nulo_ambas"], 1)
        self.assertEqual(resumo[0]["nulo_sidra"], 1)
        self.assertEqual(resumo[0]["iguais"], 1)
        self.assertEqual(resumo[0]["diferentes"], 1)

    def test_chave_duplicada(self):
        with self.assertRaisesRegex(ValueError, "duplicada"):
            diagnosticar([self.linha("5200001", "1", "1")] * 2)

if __name__ == "__main__":
    unittest.main()
