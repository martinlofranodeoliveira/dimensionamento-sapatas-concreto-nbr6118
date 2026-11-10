"""Testes unitários para as constantes e tabelas normativas de sapatas e fundações."""
from fractions import Fraction
import unittest

from sapatas_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ES_KN_CM2,
    RHO_MIN_SAPATA,
    ESPACAMENTO_MINIMO_BARRAS_CM,
    ESPACAMENTO_MAXIMO_BARRAS_CM,
    TABELA_CAA_SAPATAS,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
)


class TestConstants(unittest.TestCase):
    """Validações das constantes e coeficientes da ABNT NBR 6118:2023 e NBR 6122:2022."""

    def test_coeficientes_ponderacao(self) -> None:
        """Verifica coeficientes de segurança normativos."""
        self.assertEqual(GAMMA_C, Fraction(14, 10))
        self.assertEqual(GAMMA_S, Fraction(115, 100))
        self.assertEqual(GAMMA_F, Fraction(14, 10))
        self.assertEqual(RHO_MIN_SAPATA, Fraction(15, 10000))
        self.assertEqual(ES_KN_CM2, Fraction(21000, 1))

    def test_espacamentos_normativos_barras(self) -> None:
        """Verifica limites construtivos de espaçamento em sapatas."""
        self.assertEqual(ESPACAMENTO_MINIMO_BARRAS_CM, Fraction(10, 1))
        self.assertEqual(ESPACAMENTO_MAXIMO_BARRAS_CM, Fraction(20, 1))

    def test_tabela_caa_sapatas(self) -> None:
        """Verifica as 4 classes de agressividade e cobrimentos de fundação."""
        classes = ["CAA_I", "CAA_II", "CAA_III", "CAA_IV"]
        for caa in classes:
            self.assertIn(caa, TABELA_CAA_SAPATAS)
            info = TABELA_CAA_SAPATAS[caa]
            self.assertGreaterEqual(info["cobrimento_nominal_cm"], Fraction(4, 1))
            self.assertGreater(info["w_limite_mm"], 0)
            self.assertGreaterEqual(info["fck_minimo_mpa"], 20)

    def test_tabela_concretos(self) -> None:
        """Verifica concretos estruturais C20 a C50."""
        classes = [20, 25, 30, 35, 40, 45, 50]
        for fck in classes:
            self.assertIn(fck, TABELA_CONCRETOS_NBR6118)
            dados = TABELA_CONCRETOS_NBR6118[fck]
            self.assertEqual(dados["fck_mpa"], fck)
            self.assertGreater(dados["fctm_mpa"], 0)
            self.assertGreater(dados["fctk_inf_mpa"], 0)

    def test_tabela_acos(self) -> None:
        """Verifica aços CA-50 e CA-60."""
        self.assertIn("CA_50", TABELA_ACOS_NBR6118)
        self.assertIn("CA_60", TABELA_ACOS_NBR6118)
        self.assertEqual(TABELA_ACOS_NBR6118["CA_50"]["fyk_mpa"], 500)
        self.assertEqual(TABELA_ACOS_NBR6118["CA_50"]["fyd_kn_cm2"], Fraction(50, 1) / GAMMA_S)

    def test_tabela_bitolas_comerciais(self) -> None:
        """Verifica bitolas padronizadas de 8.0 a 25.0 mm."""
        bitolas = [
            Fraction(80, 10),
            Fraction(100, 10),
            Fraction(125, 10),
            Fraction(160, 10),
            Fraction(200, 10),
            Fraction(250, 10),
        ]
        for b in bitolas:
            self.assertIn(b, TABELA_BITOLAS_COMERCIAIS)
            info = TABELA_BITOLAS_COMERCIAIS[b]
            self.assertEqual(info["diametro_mm"], b)
            self.assertGreater(info["area_cm2"], 0)


if __name__ == "__main__":
    unittest.main()
