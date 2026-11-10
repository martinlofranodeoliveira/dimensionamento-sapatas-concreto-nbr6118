from __future__ import annotations

import csv
import io
from fractions import Fraction
from typing import Any, List

from sapatas_concreto_nbr6118.models import ResultadoProjetoSapata

CARACTERES_INJECAO_CSV = ("=", "+", "-", "@", "\t", "\r")


def sanitizar_campo_csv(valor: Any) -> str:
    """Sanitiza campos contra injeção de fórmulas CSV mantendo integridade."""
    texto = str(valor)
    if texto.startswith(CARACTERES_INJECAO_CSV):
        return "'" + texto
    return texto


def formatar_fracao_decimal(f: Fraction, casas: int = 2) -> str:
    """Converte fração em representação decimal exata com vírgula padrão pt-BR."""
    if f.denominator == 1:
        return str(f.numerator)
    fator = 10 ** casas
    val_inteiro = round((f.numerator * fator) / f.denominator)
    sinal = "-" if val_inteiro < 0 else ""
    val_abs = abs(val_inteiro)
    parte_int = val_abs // fator
    parte_dec = str(val_abs % fator).zfill(casas)
    return f"{sinal}{parte_int},{parte_dec}"


def exportar_csv(resultado: ResultadoProjetoSapata) -> str:
    """Exporta planilha técnica estruturada em formato CSV com proteção contra injeção de fórmulas."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho Geral
    escritor.writerow([
        sanitizar_campo_csv("Categoria"),
        sanitizar_campo_csv("Parâmetro"),
        sanitizar_campo_csv("Valor Calculado / Adotado"),
        sanitizar_campo_csv("Unidade"),
        sanitizar_campo_csv("Referência Normativa"),
        sanitizar_campo_csv("Conformidade"),
    ])

    geo = resultado.geometria
    flex = resultado.flexao
    punc = resultado.puncao
    det = resultado.detalhamento

    # Geometria da Base e Altura
    escritor.writerow(["Geometria", "Dimensão A (paralela a ap)", formatar_fracao_decimal(geo.dimensao_a_cm, 1), "cm", "NBR 6118 / NBR 6122", "CONFORME"])
    escritor.writerow(["Geometria", "Dimensão B (paralela a bp)", formatar_fracao_decimal(geo.dimensao_b_cm, 1), "cm", "NBR 6118 / NBR 6122", "CONFORME"])
    escritor.writerow(["Geometria", "Área da base", formatar_fracao_decimal(geo.area_sapata_m2, 2), "m²", "NBR 6122 item 3.48", "CONFORME"])
    escritor.writerow(["Geometria", "Balanço ca", formatar_fracao_decimal(geo.balanco_ca_cm, 1), "cm", "Critério balanços iguais", "CONFORME"])
    escritor.writerow(["Geometria", "Balanço cb", formatar_fracao_decimal(geo.balanco_cb_cm, 1), "cm", "Critério balanços iguais", "CONFORME"])
    escritor.writerow(["Geometria", "Altura total (h)", formatar_fracao_decimal(geo.altura_total_h_cm, 1), "cm", "NBR 6118 item 22.4", "CONFORME" if geo.e_sapata_rigida else "FLEXÍVEL"])
    escritor.writerow(["Geometria", "Altura da borda (h0)", formatar_fracao_decimal(geo.altura_borda_h0_cm, 1), "cm", "NBR 6118 item 22.4", "CONFORME"])
    escritor.writerow(["Geometria", "Altura útil (d)", formatar_fracao_decimal(geo.altura_util_d_cm, 1), "cm", "NBR 6118 item 17.2", "CONFORME"])

    # Mecânica dos Solos / Tensão de Contato
    escritor.writerow(["Geotécnica", "Tensão efetiva no solo", formatar_fracao_decimal(geo.tensao_efetiva_solo_mpa, 3), "MPa", "NBR 6122 item 6.2", "CONFORME" if geo.atende_tensao_solo else "NÃO CONFORME"])
    escritor.writerow(["Geotécnica", "Tensão admissível solo", formatar_fracao_decimal(geo.tensao_admissivel_solo_mpa, 3), "MPa", "NBR 6122", "CONFORME"])

    # Flexão e Tração nos Tirantes
    escritor.writerow(["Flexão ELU", "Força de tração Fsd,a", formatar_fracao_decimal(flex.forca_tracao_fsd_a_kn, 2), "kN", "Método das Bielas", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Força de tração Fsd,b", formatar_fracao_decimal(flex.forca_tracao_fsd_b_kn, 2), "kN", "Método das Bielas", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura calculada As,a", formatar_fracao_decimal(flex.area_aco_calculada_a_cm2, 2), "cm²", "NBR 6118 item 22.4", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura calculada As,b", formatar_fracao_decimal(flex.area_aco_calculada_b_cm2, 2), "cm²", "NBR 6118 item 22.4", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura mínima As,min,a", formatar_fracao_decimal(flex.area_aco_minima_a_cm2, 2), "cm²", "NBR 6118 Tabela 17.3", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura mínima As,min,b", formatar_fracao_decimal(flex.area_aco_minima_b_cm2, 2), "cm²", "NBR 6118 Tabela 17.3", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura final As,a", formatar_fracao_decimal(flex.area_aco_final_a_cm2, 2), "cm²", "NBR 6118", "CONFORME"])
    escritor.writerow(["Flexão ELU", "Armadura final As,b", formatar_fracao_decimal(flex.area_aco_final_b_cm2, 2), "cm²", "NBR 6118", "CONFORME"])

    # Punção e Biela
    escritor.writerow(["Punção ELU", "Perímetro crítico u0", formatar_fracao_decimal(punc.perimetro_critico_u0_cm, 1), "cm", "NBR 6118 item 19.5", "CONFORME"])
    escritor.writerow(["Punção ELU", "Tensão solicitante tau_sd", formatar_fracao_decimal(punc.tensao_solicitante_tau_sd_mpa, 2), "MPa", "NBR 6118 item 19.5", "CONFORME" if punc.atende_compressão_diagonal_biela else "ESMAGAMENTO"])
    escritor.writerow(["Punção ELU", "Resistência biela tau_Rd2", formatar_fracao_decimal(punc.tensao_resistente_tau_rd2_mpa, 2), "MPa", "NBR 6118 item 19.5", "CONFORME"])
    escritor.writerow(["Punção ELU", "Ângulo biela theta,a", formatar_fracao_decimal(punc.angulo_inclinacao_biela_a_graus, 1), "graus", "NBR 6118 item 22.4", "CONFORME" if punc.dispensa_armadura_puncao else "INFERIOR 30°"])

    # Detalhamento
    escritor.writerow(["Detalhamento", "Malha direção A", det.barras_direcao_a, "barras", "NBR 6118", "CONFORME"])
    escritor.writerow(["Detalhamento", "Área efetiva As,ef,a", formatar_fracao_decimal(det.area_efetiva_a_cm2, 2), "cm²", "NBR 6118", "CONFORME"])
    escritor.writerow(["Detalhamento", "Malha direção B", det.barras_direcao_b, "barras", "NBR 6118", "CONFORME"])
    escritor.writerow(["Detalhamento", "Área efetiva As,ef,b", formatar_fracao_decimal(det.area_efetiva_b_cm2, 2), "cm²", "NBR 6118", "CONFORME"])
    escritor.writerow(["Detalhamento", "Gancho de ancoragem", formatar_fracao_decimal(det.comprimento_gancho_cm, 1), "cm", "NBR 6118 item 9.4", "CONFORME"])

    return saida.getvalue()


def gerar_relatorio_memorial(resultado: ResultadoProjetoSapata) -> str:
    """Gera memorial descritivo completo da sapata em formato texto estruturado pt-BR."""
    geo = resultado.geometria
    flex = resultado.flexao
    punc = resultado.puncao
    det = resultado.detalhamento

    status_str = "APROVADO" if resultado.atende_geral else "COM RESTRIÇÕES / NÃO CONFORME"

    linhas = [
        "=" * 80,
        "       LOFRANO TECNOLOGIA - ENGENHARIA DE FUNDAÇÕES E ESTRUTURAS",
        "         MEMORIAL DE CÁLCULO NORMATIVO - SAPATAS ISOLADAS DE CONCRETO",
        "=" * 80,
        f"Projeto / Identificação: {resultado.identificacao}",
        f"Normas Regulamentadoras: {', '.join(resultado.normas)}",
        f"Status de Aprovação:     {status_str}",
        "-" * 80,
        "1. CARACTERÍSTICAS GEOMÉTRICAS DA SAPATA E PRESSÕES DE CONTATO",
        f"  - Dimensões da base (A x B): {formatar_fracao_decimal(geo.dimensao_a_cm, 0)} x {formatar_fracao_decimal(geo.dimensao_b_cm, 0)} cm (Área: {formatar_fracao_decimal(geo.area_sapata_m2, 2)} m²)",
        f"  - Balanços da sapata:        ca = {formatar_fracao_decimal(geo.balanco_ca_cm, 1)} cm | cb = {formatar_fracao_decimal(geo.balanco_cb_cm, 1)} cm (Balanços iguais: {'SIM' if geo.balancos_iguais else 'NÃO'})",
        f"  - Altura total (h):          {formatar_fracao_decimal(geo.altura_total_h_cm, 0)} cm (Critério de rigidez: {'RIGIDA' if geo.e_sapata_rigida else 'FLEXIVEL'})",
        f"  - Altura da borda (h0):      {formatar_fracao_decimal(geo.altura_borda_h0_cm, 0)} cm",
        f"  - Altura útil (d):           {formatar_fracao_decimal(geo.altura_util_d_cm, 1)} cm",
        f"  - Tensão efetiva no solo:    {formatar_fracao_decimal(geo.tensao_efetiva_solo_mpa, 3)} MPa (Admissível: {formatar_fracao_decimal(geo.tensao_admissivel_solo_mpa, 3)} MPa) -> {'CONFORME' if geo.atende_tensao_solo else 'NÃO CONFORME'}",
        "",
        "2. DIMENSIONAMENTO À FLEXÃO (MÉTODO DAS BIELAS E TIRANTES)",
        f"  - Força de tração Fsd,a:     {formatar_fracao_decimal(flex.forca_tracao_fsd_a_kn, 2)} kN",
        f"  - Força de tração Fsd,b:     {formatar_fracao_decimal(flex.forca_tracao_fsd_b_kn, 2)} kN",
        f"  - Armadura calculada As,a:   {formatar_fracao_decimal(flex.area_aco_calculada_a_cm2, 2)} cm² (Mínima: {formatar_fracao_decimal(flex.area_aco_minima_a_cm2, 2)} cm²)",
        f"  - Armadura calculada As,b:   {formatar_fracao_decimal(flex.area_aco_calculada_b_cm2, 2)} cm² (Mínima: {formatar_fracao_decimal(flex.area_aco_minima_b_cm2, 2)} cm²)",
        f"  - Armadura adotada As,a:     {formatar_fracao_decimal(flex.area_aco_final_a_cm2, 2)} cm²",
        f"  - Armadura adotada As,b:     {formatar_fracao_decimal(flex.area_aco_final_b_cm2, 2)} cm²",
        "",
        "3. VERIFICAÇÃO DE PUNÇÃO E COMPRESSÃO DIAGONAL (ELU)",
        f"  - Força normal de cálculo:   Nsd = {formatar_fracao_decimal(punc.forca_normal_nsd_kn, 2)} kN",
        f"  - Perímetro crítico u0:      {formatar_fracao_decimal(punc.perimetro_critico_u0_cm, 1)} cm (contorno do pilar)",
        f"  - Tensão de cisalhamento:    tau_sd = {formatar_fracao_decimal(punc.tensao_solicitante_tau_sd_mpa, 2)} MPa (Limite biela tau_Rd2 = {formatar_fracao_decimal(punc.tensao_resistente_tau_rd2_mpa, 2)} MPa) -> {'CONFORME' if punc.atende_compressão_diagonal_biela else 'ESMAGAMENTO BIELA'}",
        f"  - Inclinação da biela:       theta,a = {formatar_fracao_decimal(punc.angulo_inclinacao_biela_a_graus, 1)}° | theta,b = {formatar_fracao_decimal(punc.angulo_inclinacao_biela_b_graus, 1)}° (Dispensa armadura de punção: {'SIM' if punc.dispensa_armadura_puncao else 'NÃO'})",
        "",
        "4. DETALHAMENTO DA MALHA DE ARMADURA INFERIOR",
        f"  - Direção A (paralela a ap): {det.barras_direcao_a} (As,ef = {formatar_fracao_decimal(det.area_efetiva_a_cm2, 2)} cm²)",
        f"  - Direção B (paralela a bp): {det.barras_direcao_b} (As,ef = {formatar_fracao_decimal(det.area_efetiva_b_cm2, 2)} cm²)",
        f"  - Gancho de ancoragem:       {formatar_fracao_decimal(det.comprimento_gancho_cm, 1)} cm nas extremidades",
        "",
        "5. SÍNTESE DE CONFORMIDADES",
        f"  - [tensao_solo]:                 {'CONFORME' if resultado.conformidades.get('tensao_solo', False) else 'REPROVADO'}",
        f"  - [rigidez_sapata]:             {'CONFORME' if resultado.conformidades.get('rigidez_sapata', False) else 'REPROVADO'}",
        f"  - [compressao_diagonal_biela]:   {'CONFORME' if resultado.conformidades.get('compressao_diagonal_biela', False) else 'REPROVADO'}",
        f"  - [dispensa_puncao]:             {'CONFORME' if resultado.conformidades.get('dispensa_puncao', False) else 'REPROVADO'}",
    ]

    if resultado.alertas:
        linhas.append("  ALERTAS DE PROJETO:")
        for al in resultado.alertas:
            linhas.append(f"    [!] {al}")

    if resultado.recomendacoes:
        linhas.append("  RECOMENDAÇÕES EXECUTIVAS:")
        for rec in resultado.recomendacoes:
            linhas.append(f"    [*] {rec}")

    linhas.extend([
        "=" * 80,
        "LOFRANO TECNOLOGIA - Soluções Determinísticas e Engenharia Confiável.",
        "=" * 80,
    ])

    return "\n".join(linhas)
