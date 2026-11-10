"""Testes unitários para exportação de dados (CSV seguro e Memorial Descritivo de sapatas)."""
from fractions import Fraction
import csv
import io
import unittest

from sapatas_concreto_nbr6118.calculator import dimensionar_sapata_concreto
from sapatas_concreto_nbr6118.exporters import (
    sanitizar_campo_csv,
    formatar_fracao_decimal,
    exportar_csv,
    gerar_relatorio_memorial,
)
from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    ProjetoSapata,
)


class TestExporters(unittest.TestCase):
    """Testes de formatação, sanitização e exportação de resultados."""

    def test_sanitizar_campo_csv(self) -> None:
        """Garante que caracteres perigosos de fórmula recebam apóstrofo como prefixo."""
        self.assertEqual(sanitizar_campo_csv("=SOMA(A1:A10)"), "'=SOMA(A1:A10)")
        self.assertEqual(sanitizar_campo_csv("+12345"), "'+12345")
        self.assertEqual(sanitizar_campo_csv("-500"), "'-500")
        self.assertEqual(sanitizar_campo_csv("@CMD"), "'@CMD")
        self.assertEqual(sanitizar_campo_csv("\ttab"), "'\ttab")
        self.assertEqual(sanitizar_campo_csv("\rretorno"), "'\rretorno")
        self.assertEqual(sanitizar_campo_csv("Sapata S101"), "Sapata S101")
        self.assertEqual(sanitizar_campo_csv("CONFORME"), "CONFORME")

    def test_formatar_fracao_decimal(self) -> None:
        """Garante formatação em padrão pt-BR com vírgula."""
        self.assertEqual(formatar_fracao_decimal(Fraction(25, 1)), "25")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 2)), "0,50")
        self.assertEqual(formatar_fracao_decimal(Fraction(3, 4), casas=2), "0,75")
        self.assertEqual(formatar_fracao_decimal(Fraction(1, 8), casas=3), "0,125")
        self.assertEqual(formatar_fracao_decimal(Fraction(-7, 2)), "-3,50")

    def test_exportar_csv_integridade(self) -> None:
        """Valida que o CSV gerado possui estrutura de colunas e dados consistentes."""
        proj = ProjetoSapata(
            identificacao="Sapata Teste CSV",
            pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
            materiais=PropriedadesMateriais(classe_agressividade="CAA_II"),
        )
        res = dimensionar_sapata_concreto(proj)
        csv_texto = exportar_csv(res)

        leitor = csv.reader(io.StringIO(csv_texto), delimiter=";")
        linhas = list(leitor)
        self.assertGreater(len(linhas), 10)

        cabecalho = linhas[0]
        self.assertIn("Categoria", cabecalho)
        self.assertIn("Parâmetro", cabecalho)
        self.assertIn("Valor Calculado / Adotado", cabecalho)
        self.assertIn("Referência Normativa", cabecalho)

        # Não deve haver fórmulas sem prefixo
        for row in linhas:
            for col in row:
                if col.startswith(("=", "@", "+")):
                    self.fail(f"Campo CSV não sanitizado detectado: {col}")

    def test_gerar_relatorio_memorial(self) -> None:
        """Valida a geração do memorial descritivo completo em pt-BR."""
        proj = ProjetoSapata(
            identificacao="Sapata Teste Memorial",
            pilar=PilarApoiado(largura_ap_cm=Fraction(20), comprimento_bp_cm=Fraction(40), carga_normal_nk_kn=Fraction(450)),
            solo=PropriedadesSolo(tensao_admissivel_sigma_adm_mpa=Fraction(2, 10)),
            materiais=PropriedadesMateriais(classe_agressividade="CAA_II"),
        )
        res = dimensionar_sapata_concreto(proj)
        memorial = gerar_relatorio_memorial(res)

        self.assertIn("LOFRANO TECNOLOGIA", memorial)
        self.assertIn("ABNT NBR 6118:2023", memorial)
        self.assertIn("ABNT NBR 6122:2022", memorial)
        self.assertIn("1. CARACTERÍSTICAS GEOMÉTRICAS", memorial)
        self.assertIn("2. DIMENSIONAMENTO À FLEXÃO", memorial)
        self.assertIn("3. VERIFICAÇÃO DE PUNÇÃO", memorial)
        self.assertIn("4. DETALHAMENTO DA MALHA", memorial)
        self.assertIn("5. SÍNTESE DE CONFORMIDADES", memorial)


if __name__ == "__main__":
    unittest.main()
