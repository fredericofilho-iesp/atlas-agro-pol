import csv
import tempfile
import unittest
from pathlib import Path
from pipeline.validar_pam_uf import carregar, comparar


class ValidarPAMUF(unittest.TestCase):
    def test_comparacao_e_ausencias(self):
        a = {(2024, "51", "Soja"): 100., (2024, "14", "Café"): None}
        b = {(2024, "51", "Soja"): 98., (2024, "14", "Café"): 0.,
             (2024, "35", "Arroz"): 4.}
        r = comparar(a, b)
        d = {(x["codigo_uf"], x["produto"]): x for x in r}
        self.assertAlmostEqual(d["51", "Soja"]["diferenca_pct"], 100*2/98)
        self.assertEqual(d["14", "Café"]["status"], "bd_nulo")
        self.assertEqual(d["35", "Arroz"]["status"], "sem_linha_bd")

    def test_duplicata_rejeitada(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.csv"
            with p.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["ano","codigo_uf","produto","valor_total_mil_reais"])
                w.writerow([2024,51,"Soja",10])
                w.writerow([2024,51,"Soja",11])
            with self.assertRaisesRegex(ValueError, "duplicada"):
                carregar(p)


if __name__ == "__main__":
    unittest.main()
