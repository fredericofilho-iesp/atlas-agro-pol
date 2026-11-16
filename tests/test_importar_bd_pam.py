"""Testes offline: importação de dados da Base dos Dados/PAM."""
import csv
import tempfile
import unittest
from pathlib import Path

from pipeline.importar_bd_pam import converter_linhas


class ImportadorPAM(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "pam.csv"

    def tearDown(self):
        self.temp.cleanup()

    def escrever(self, linhas):
        with self.path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "ano", "id_municipio", "produto", "valor_producao", "tipo_lavoura"
            ])
            w.writeheader()
            w.writerows(linhas)

    def base(self):
        return dict(ano="2024", id_municipio="3304557", produto="Café (em grão)",
                    valor_producao="1500.5", tipo_lavoura="permanente")

    def test_total_por_municipio_ano(self):
        r1 = self.base()
        r2 = dict(r1, produto="Soja", valor_producao="200", tipo_lavoura="temporaria")
        self.escrever([r1, r2])
        saida, info = converter_linhas(self.path)
        totais = [x for x in saida if x["categoria"] == "Total"]
        self.assertEqual(len(totais), 1)
        self.assertEqual(totais[0]["valor"], 1700.5)
        self.assertEqual(info["municipio_ano_completo"], 1)

    def test_nulo_impede_total_parcial(self):
        r1 = self.base()
        r2 = dict(r1, produto="Soja", valor_producao="", tipo_lavoura="temporaria")
        self.escrever([r1, r2])
        saida, info = converter_linhas(self.path)
        self.assertFalse(any(x["categoria"] == "Total" for x in saida))
        self.assertEqual(info["valores_nulos"], 1)

    def test_duplicata_rejeitada(self):
        self.escrever([self.base(), self.base()])
        with self.assertRaisesRegex(ValueError, "duplicada"):
            converter_linhas(self.path)

    def test_codigo_invalido_rejeitado(self):
        self.escrever([dict(self.base(), id_municipio="123")])
        with self.assertRaisesRegex(ValueError, "inválido"):
            converter_linhas(self.path)


if __name__ == "__main__":
    unittest.main()
