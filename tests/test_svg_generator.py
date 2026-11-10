"""Testes unitários para o gerador de painel técnico vetorial SVG de sapatas."""
from fractions import Fraction
import unittest

from sapatas_concreto_nbr6118.calculator import dimensionar_sapata_concreto
from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    ProjetoSapata,
)
from sapatas_concreto_nbr6118.svg_generator import gerar_painel_svg, escapar_xml


class TestSvgGenerator(unittest.TestCase):
    """Testes de conformidade do gerador SVG."""

    def test_escapar_xml(self) -> None:
        """Verifica escape seguro de caracteres XML."""
        self.assertEqual(escapar_xml("Texto <com> & \"aspas\" 'simples'"), "Texto &lt;com&gt; &amp; &quot;aspas&quot; &#x27;simples&#x27;")

    def test_gerar_painel_svg_estrutura(self) -> None:
        """Garante formato correto de cabeçalho, viewport e tags SVG."""
        proj = ProjetoSapata(
            identificacao="Sapata S-SVG Teste",
            pilar=PilarApoiado(largura_ap_cm=Fraction(25), comprimento_bp_cm=Fraction(45), carga_normal_nk_kn=Fraction(500)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
            materiais=PropriedadesMateriais(classe_agressividade="CAA_II"),
        )
        res = dimensionar_sapata_concreto(proj)
        svg = gerar_painel_svg(res)

        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))
        self.assertIn('viewBox="0 0 1440 900"', svg)
        self.assertIn('width="1440"', svg)
        self.assertIn('height="900"', svg)
        self.assertTrue(svg.strip().endswith('</svg>'))

        # Seções essenciais
        self.assertIn("LOFRANO TECNOLOGIA", svg)
        self.assertIn("ABNT NBR 6118:2023", svg)
        self.assertIn("ABNT NBR 6122:2022", svg)
        self.assertIn("VISTA EM PLANTA DA BASE", svg)
        self.assertIn("CORTE ELEVAÇÃO &amp; MÉTODO DAS BIELAS", svg)
        self.assertIn("DISTRIBUIÇÃO UNIFORME DE TENSÕES NO SOLO", svg)
        self.assertIn("DIMENSIONAMENTO E VERIFICAÇÕES ELU", svg)
        self.assertIn("CONFORMIDADES E GARANTIAS NORMATIVAS", svg)


if __name__ == "__main__":
    unittest.main()
