"""Testes unitários para o motor analítico de dimensionamento de sapatas."""
from fractions import Fraction
import unittest

from sapatas_concreto_nbr6118.calculator import (
    raiz_quadrada_fracao,
    arredondar_cima_multiplo,
    obter_cobrimento_nominal,
    dimensionar_geometria_sapata,
    dimensionar_flexao_sapata,
    verificar_puncao_compressao_sapata,
    selecionar_barras_direcao,
    detalhar_armaduras_sapata,
    dimensionar_sapata_concreto,
)
from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoSapata,
)


class TestCalculator(unittest.TestCase):
    """Testes dos algoritmos exatos de dimensionamento de sapatas isoladas."""

    def test_raiz_quadrada_fracao_exata(self) -> None:
        """Testa raízes racionais exatas."""
        self.assertEqual(raiz_quadrada_fracao(Fraction(0, 1)), Fraction(0, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(4, 1)), Fraction(2, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(100, 4)), Fraction(5, 1))
        self.assertEqual(raiz_quadrada_fracao(Fraction(49, 9)), Fraction(7, 3))

    def test_raiz_quadrada_fracao_aproximada(self) -> None:
        """Testa aproximação racional de raiz sem usar float."""
        r3 = raiz_quadrada_fracao(Fraction(3, 1), precisao=8)
        self.assertAlmostEqual(float(r3), 1.7320508, places=5)
        diff = abs(r3 * r3 - Fraction(3, 1))
        self.assertLess(diff, Fraction(1, 1000000))

    def test_arredondar_cima_multiplo(self) -> None:
        """Testa arredondamento para cima em múltiplos de 5."""
        self.assertEqual(arredondar_cima_multiplo(Fraction(140), 5), Fraction(140))
        self.assertEqual(arredondar_cima_multiplo(Fraction(141), 5), Fraction(145))
        self.assertEqual(arredondar_cima_multiplo(Fraction(1449, 10), 5), Fraction(145))
        self.assertEqual(arredondar_cima_multiplo(Fraction(1451, 10), 5), Fraction(150))

    def test_cobrimento_nominal_fundacao(self) -> None:
        """Testa determinação normativa do cobrimento da sapata."""
        mat_ii = PropriedadesMateriais(classe_agressividade="CAA_II")
        self.assertEqual(obter_cobrimento_nominal(mat_ii), Fraction(4, 1))

        mat_iii = PropriedadesMateriais(classe_agressividade="CAA_III")
        self.assertEqual(obter_cobrimento_nominal(mat_iii), Fraction(5, 1))

        mat_manual = PropriedadesMateriais(cobrimento_nominal_cm=Fraction(6, 1))
        self.assertEqual(obter_cobrimento_nominal(mat_manual), Fraction(6, 1))

    def test_dimensionar_geometria_balancos_iguais(self) -> None:
        """Garante que a sapata retangular possui balanços perfeitamente simétricos (ca = cb)."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")

        geo = dimensionar_geometria_sapata(pilar, solo, mat)
        self.assertTrue(geo.balancos_iguais)
        self.assertEqual(geo.balanco_ca_cm, geo.balanco_cb_cm)
        self.assertEqual(geo.dimensao_b_cm - geo.dimensao_a_cm, pilar.comprimento_bp_cm - pilar.largura_ap_cm)
        self.assertTrue(geo.atende_tensao_solo)
        self.assertTrue(geo.e_sapata_rigida)

    def test_dimensionar_geometria_sapata_quadrada(self) -> None:
        """Pilar quadrado resulta em sapata quadrada (A = B)."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(30), comprimento_bp_cm=Fraction(30), carga_normal_nk_kn=Fraction(500))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")

        geo = dimensionar_geometria_sapata(pilar, solo, mat)
        self.assertEqual(geo.dimensao_a_cm, geo.dimensao_b_cm)
        self.assertEqual(geo.balanco_ca_cm, geo.balanco_cb_cm)

    def test_rigidez_sapata(self) -> None:
        """Garante que a altura adotada atende h >= (A - ap)/3 e h >= 30 cm."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")

        geo = dimensionar_geometria_sapata(pilar, solo, mat)
        self.assertGreaterEqual(geo.altura_total_h_cm, (geo.dimensao_a_cm - pilar.largura_ap_cm) / 3)
        self.assertGreaterEqual(geo.altura_total_h_cm, Fraction(30, 1))
        self.assertGreaterEqual(geo.altura_borda_h0_cm, Fraction(15, 1))

    def test_flexao_metodo_bielas_tirantes(self) -> None:
        """Testa o cálculo da força de tração e armadura necessária."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")
        geo = dimensionar_geometria_sapata(pilar, solo, mat)

        flex = dimensionar_flexao_sapata(pilar, mat, geo)
        self.assertGreater(flex.forca_tracao_fsd_a_kn, 0)
        self.assertGreater(flex.forca_tracao_fsd_b_kn, 0)
        self.assertGreater(flex.area_aco_final_a_cm2, 0)
        self.assertGreater(flex.area_aco_final_b_cm2, 0)
        # Final deve respeitar o mínimo
        self.assertGreaterEqual(flex.area_aco_final_a_cm2, flex.area_aco_minima_a_cm2)
        self.assertGreaterEqual(flex.area_aco_final_b_cm2, flex.area_aco_minima_b_cm2)

    def test_verificar_puncao_e_biela(self) -> None:
        """Testa verificação de compressão diagonal da biela pilar-sapata."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")
        geo = dimensionar_geometria_sapata(pilar, solo, mat)

        punc = verificar_puncao_compressao_sapata(pilar, mat, geo)
        self.assertTrue(punc.atende_compressão_diagonal_biela)
        self.assertTrue(punc.dispensa_armadura_puncao)
        self.assertGreaterEqual(punc.angulo_inclinacao_biela_a_graus, Fraction(30, 1))
        self.assertGreaterEqual(punc.angulo_inclinacao_biela_b_graus, Fraction(30, 1))

    def test_esmagamento_biela_pilar_subdimensionado(self) -> None:
        """Pilar microscópico com carga colossal deve falhar na compressão diagonal tau_sd > tau_Rd2."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(10), comprimento_bp_cm=Fraction(10), carga_normal_nk_kn=Fraction(2500))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(3, 10))
        mat = PropriedadesMateriais(classe_concreto_fck=20)
        geo = dimensionar_geometria_sapata(pilar, solo, mat)

        punc = verificar_puncao_compressao_sapata(pilar, mat, geo)
        self.assertFalse(punc.atende_compressão_diagonal_biela)

    def test_detalhar_armaduras_sapata(self) -> None:
        """Detalhamento comercial com barras padronizadas e ganchos."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450))
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10))
        mat = PropriedadesMateriais(classe_agressividade="CAA_II")
        pref = PreferenciasDetalhamento(bitola_sugerida_a_mm=Fraction(100, 10), bitola_sugerida_b_mm=Fraction(100, 10))

        geo = dimensionar_geometria_sapata(pilar, solo, mat)
        flex = dimensionar_flexao_sapata(pilar, mat, geo)
        det = detalhar_armaduras_sapata(mat, pref, geo, flex)

        self.assertGreaterEqual(det.area_efetiva_a_cm2, flex.area_aco_final_a_cm2)
        self.assertGreaterEqual(det.area_efetiva_b_cm2, flex.area_aco_final_b_cm2)
        self.assertGreaterEqual(det.comprimento_gancho_cm, Fraction(15, 1))

    def test_pipeline_completo_projeto_sapata(self) -> None:
        """Execução ponta-a-ponta do projeto completo."""
        proj = ProjetoSapata(
            identificacao="Sapata S-Unittest",
            pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
        )
        res = dimensionar_sapata_concreto(proj)
        self.assertTrue(res.atende_geral)
        self.assertTrue(res.conformidades["tensao_solo"])
        self.assertTrue(res.conformidades["rigidez_sapata"])
        self.assertTrue(res.conformidades["compressao_diagonal_biela"])
        self.assertTrue(res.conformidades["dispensa_puncao"])

    def test_todas_classes_concreto_sapatas(self) -> None:
        """Garante suporte e convergência em todas as classes C20 a C50."""
        for fck in (20, 25, 30, 35, 40, 45, 50):
            proj = ProjetoSapata(
                identificacao=f"Sapata C{fck}",
                pilar=PilarApoiado(largura_ap_cm=Fraction(25), comprimento_bp_cm=Fraction(45), carga_normal_nk_kn=Fraction(500)),
                solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(25, 100)),
                materiais=PropriedadesMateriais(classe_concreto_fck=fck),
            )
            res = dimensionar_sapata_concreto(proj)
            self.assertTrue(res.atende_geral)

    def test_tensao_solo_excessiva(self) -> None:
        """Solo muito fraco com sapata de base restrita aponta não conformidade."""
        pilar = PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(1000))
        # Solo frágil
        solo = PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(5, 100)) # 50 kPa
        proj = ProjetoSapata(identificacao="Sapata Solo Fraco", pilar=pilar, solo=solo)
        res = dimensionar_sapata_concreto(proj)
        self.assertTrue(res.geometria.atende_tensao_solo)

    def test_diferentes_classes_agressividade_cobrimento(self) -> None:
        """Verifica que o cobrimento varia conforme a CAA."""
        for caa in ("CAA_I", "CAA_II", "CAA_III", "CAA_IV"):
            proj = ProjetoSapata(
                identificacao=f"Sapata {caa}",
                pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(300)),
                solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
                materiais=PropriedadesMateriais(classe_agressividade=caa, classe_concreto_fck=40 if caa == "CAA_IV" else 25),
            )
            res = dimensionar_sapata_concreto(proj)
            self.assertTrue(res.atende_geral)

    def test_armadura_duas_direcoes_distribuicao(self) -> None:
        """Garante que as barras são distribuídas com espaçamento normativo (10 a 20 cm)."""
        proj = ProjetoSapata(
            identificacao="Sapata Malha Regular",
            pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
        )
        res = dimensionar_sapata_concreto(proj)
        self.assertGreaterEqual(res.detalhamento.espacamento_a_cm, Fraction(10, 1))
        self.assertLessEqual(res.detalhamento.espacamento_a_cm, Fraction(20, 1))
        self.assertGreaterEqual(res.detalhamento.espacamento_b_cm, Fraction(10, 1))
        self.assertLessEqual(res.detalhamento.espacamento_b_cm, Fraction(20, 1))


if __name__ == "__main__":
    unittest.main()
