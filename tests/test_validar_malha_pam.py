import unittest
from pipeline.validar_malha_pam import validar


class TestMalha(unittest.TestCase):
    def test_cobertura_e_ids(self):
        geo={"type":"FeatureCollection","features":[
            {"type":"Feature","id":"1100015","properties":{},"geometry":None},
            {"type":"Feature","properties":{"codarea":"1100023"},"geometry":None}]}
        res=validar(geo,{"1100015","1100023"},1)
        self.assertEqual(res["cobertura_pam"],1)
    def test_municipio_ausente(self):
        geo={"type":"FeatureCollection","features":[
            {"type":"Feature","id":"1100015","properties":{},"geometry":None}]}
        with self.assertRaisesRegex(ValueError,"reprovada"):
            validar(geo,{"1100015","1100023"},1)
    def test_duplicacao(self):
        f={"type":"Feature","id":"1100015","properties":{},"geometry":None}
        with self.assertRaisesRegex(ValueError,"reprovada"):
            validar({"type":"FeatureCollection","features":[f,f]},{"1100015"},1)


if __name__=="__main__":
    unittest.main()
