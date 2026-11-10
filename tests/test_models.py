"""Testes unitários para dataclasses e modelos de domínio de sapatas."""
from fractions import Fraction
import unittest

from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoSapata,
)


class TestModels(unittest.TestCase):
    """Validações de integridade dos modelos estruturais e geotécnicos."""

    def test_pilar_apoiado_valido(self) -> None:
        """Criação válida de pilar com carga axial."""
        pilar = PilarApoiado(
            largura_ap_cm=Fraction(25),
            comprimento_bp_cm=Fraction(50),
            carga_normal_nk_kn=Fraction(600),
        )
        self.assertEqual(pilar.largura_ap_cm, Fraction(25))
        self.assertEqual(pilar.comprimento_bp_cm, Fraction(50))
        self.assertEqual(pilar.carga_normal_nk_kn, Fraction(600))

    def test_pilar_apoiado_invalido(self) -> None:
        """Dimensões ou cargas não positivas devem levantar ValueError."""
        with self.assertRaises(ValueError):
            PilarApoiado(largura_ap_cm=Fraction(0), comprimento_bp_cm=Fraction(50), carga_normal_nk_kn=Fraction(600))
        with self.assertRaises(ValueError):
            PilarApoiado(largura_ap_cm=Fraction(25), comprimento_bp_cm=Fraction(-10), carga_normal_nk_kn=Fraction(600))
        with self.assertRaises(ValueError):
            PilarApoiado(largura_ap_cm=Fraction(25), comprimento_bp_cm=Fraction(50), carga_normal_nk_kn=Fraction(0))

    def test_propriedades_solo_validas(self) -> None:
        """Criação válida de solo com tensão admissível."""
        solo = PropriedadesSolo(
            tensao_admissivel_sigma_adm_mpa=Fraction(25, 100),
            descricao_camada="Argila arenosa rija",
        )
        self.assertEqual(solo.tensao_admissivel_sigma_adm_mpa, Fraction(25, 100))

    def test_propriedades_solo_invalidas(self) -> None:
        """Tensão admissível não positiva deve levantar ValueError."""
        with self.assertRaises(ValueError):
            PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(0))
        with self.assertRaises(ValueError):
            PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(-5, 10))

    def test_propriedades_materiais_validas(self) -> None:
        """Validação de materiais C20 a C50 e CAA."""
        mat = PropriedadesMateriais(classe_concreto_fck=30, classe_agressividade="CAA_III")
        self.assertEqual(mat.classe_concreto_fck, 30)
        self.assertEqual(mat.classe_agressividade, "CAA_III")

    def test_propriedades_materiais_invalidas(self) -> None:
        """Concretos fora do Grupo I ou CAA inexistente."""
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_concreto_fck=15)
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_concreto_fck=60)
        with self.assertRaises(ValueError):
            PropriedadesMateriais(classe_agressividade="CAA_INVALIDA")

    def test_projeto_sapata_completo(self) -> None:
        """Instanciação de um projeto de sapata estruturado."""
        proj = ProjetoSapata(
            identificacao="Sapata S01 Teste",
            pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(400)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
        )
        self.assertEqual(proj.identificacao, "Sapata S01 Teste")
        self.assertEqual(proj.materiais.classe_concreto_fck, 25)


if __name__ == "__main__":
    unittest.main()
