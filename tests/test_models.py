"""Testes do reconhecimento de modelo (títulos reais vistos em 26/11/2026).

Rodar:  python -m unittest discover -s tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from radar.models import classify_model  # noqa: E402
from radar import pricing, config  # noqa: E402

MAIN = "ps5_slim_disco_1tb"
CASES = [
    ("PlayStation 5 Slim Disk 1TB", 3689, "", MAIN),
    ("Console Playstation 5 Slim 1Tb Com Leitor de Discos", 3671.25, "", MAIN),
    ("Console Sony PlayStation 5 com Leitor de Discos SSD 1TB Controle Sem Fio", 3695, "", MAIN),
    ("GTA VI + PS5 Slim Disk + Astro Bot + GT7", 4524, "", MAIN),
    ("Sony PlayStation 5 Slim 1TB cor branco", 3776, "https://www.mercadolivre.com.br/x/p/MLB28616777", MAIN),
    ("Sony PlayStation 5 Slim 1TB cor branco", 3776, "", "modelo_a_confirmar"),
    ("Console PlayStation 5 Slim 1TB com Controle DualSense", 4480, "", "modelo_a_confirmar"),
    ("PlayStation 5 Slim 1TB Digital Branco 2023", 3321, "", "ps5_slim_digital"),
    ("Console PlayStation 5 Slim Digital 825 GB Branco", 3537, "", "ps5_slim_digital"),
    ("PlayStation 5 SSD 825GB DualSense 2 Jogos", 4083, "", None),
    ("PlayStation®5 Pro", 6885, "", "ps5_pro"),
    ("Tony Hawk's Pro Skater 3+4 PS5", 132, "", None),
    ("Leitor Disco Playstation 5 Slim Ps5 Pro Sony", 497, "", None),
    ("Console PlayStation 5 Slim 1TB Disk CFI-2114 usado", 3000, "", None),
    ("Console PS5 Slim Disk 1TB importado", 3000, "", None),
    ("Controle Sem Fio Sony DualSense PS5 Branco", 295, "", "dualsense"),
    ("Controle PlayStation DualSense Chroma Indigo PS5", 375, "", "dualsense_especial"),
    ("Controle Sony DualSense Edge PS5 Branco", 989, "", "dualsense_edge"),
    ("Controle Access Sony PS5 Slim Pro Sem Fio Branco", 359, "", None),
    ("Bateria Para Controle Ps5 Dualsense Lip1708 2650mah", 33, "", None),
    ("Base Carregamento PS5 DualSense LED Branco", 93, "", None),
]


class TestModels(unittest.TestCase):
    def test_titles(self):
        for title, price, url, expected in CASES:
            with self.subTest(title=title):
                self.assertEqual(classify_model(title, price, url)["model"], expected)


class TestPricing(unittest.TestCase):
    base = {"tipico": 4300.0, "minimo": 3650.0}

    def test_classes(self):
        c = lambda p, t="alta": pricing.classify(p, MAIN, self.base, t, True)["classe"]  # noqa: E731
        self.assertEqual(c(3300), "EXCEPCIONAL")        # -23%
        self.assertEqual(c(3780), "IMPERDÍVEL")         # -R$ 520
        self.assertEqual(c(4050), "BOA OFERTA")         # -5,8%
        self.assertEqual(c(4250), "MONITORAR")
        self.assertEqual(c(4600), "DESCARTAR")
        self.assertEqual(pricing.classify(3300, MAIN, self.base, None, True)["classe"], "DESCARTAR")

    def test_secondary_needs_record_low(self):
        base = {"tipico": 399.9, "minimo": 214.0}
        self.assertEqual(pricing.classify(305, "dualsense", base, "alta", False)["classe"], "IMPERDÍVEL")
        self.assertEqual(pricing.classify(215, "dualsense", base, "alta", False)["classe"], "EXCEPCIONAL")


if __name__ == "__main__":
    unittest.main()
