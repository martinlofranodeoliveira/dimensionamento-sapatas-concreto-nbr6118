from __future__ import annotations

import math
from fractions import Fraction
from typing import Dict, Any, List, Tuple

from sapatas_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    TABELA_CAA_SAPATAS,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
    RHO_MIN_SAPATA,
    ESPACAMENTO_MINIMO_BARRAS_CM,
    ESPACAMENTO_MAXIMO_BARRAS_CM,
)
from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoSapata,
    ResultadoGeometriaSapata,
    ResultadoFlexaoSapata,
    ResultadoPuncaoSapata,
    ResultadoDetalhamentoSapata,
    ResultadoProjetoSapata,
)


def raiz_quadrada_fracao(frac: Fraction, precisao: int = 12) -> Fraction:
    """Calcula a aproximação racional exata de raiz quadrada de uma fração sem usar float."""
    if frac < 0:
        raise ValueError("Raiz quadrada de fração negativa não existe nos reais.")
    if frac == 0:
        return Fraction(0, 1)

    p = frac.numerator
    q = frac.denominator
    fator_escala = 10 ** (2 * precisao)
    radicando_inteiro = p * q * fator_escala
    raiz_int = math.isqrt(radicando_inteiro)
    denominador = q * (10 ** precisao)
    return Fraction(raiz_int, denominador)


def arredondar_cima_multiplo(valor: Fraction, multiplo: int = 5) -> Fraction:
    """Arredonda uma dimensão fracionária para cima em múltiplos de 'multiplo' (ex: 5 cm)."""
    # Exemplo: valor = 142/1 -> teto múltiplo de 5 é 145
    mult_frac = Fraction(multiplo, 1)
    divisao = valor / mult_frac
    # teto
    teto = math.ceil(divisao.numerator / divisao.denominator)
    return Fraction(teto * multiplo, 1)


def obter_cobrimento_nominal(materiais: PropriedadesMateriais) -> Fraction:
    """Determina o cobrimento nominal mínimo da sapata em cm."""
    if materiais.cobrimento_nominal_cm is not None:
        return materiais.cobrimento_nominal_cm
    info = TABELA_CAA_SAPATAS.get(materiais.classe_agressividade, TABELA_CAA_SAPATAS["CAA_II"])
    return info["cobrimento_nominal_cm"]


def dimensionar_geometria_sapata(
    pilar: PilarApoiado,
    solo: PropriedadesSolo,
    materiais: PropriedadesMateriais,
) -> ResultadoGeometriaSapata:
    """Dimensiona a base A x B com balanços iguais e altura h para garantir rigidez."""
    # 1. Carga vertical de serviço com peso próprio estimado em 5%
    # N_tot = 1.05 * Nk
    nk = pilar.carga_normal_nk_kn
    n_tot_k = nk * Fraction(105, 100)

    # Tensão admissível em kN/cm² (1 MPa = 0,10 kN/cm²)
    sigma_adm_mpa = solo.tensao_admissivel_sigma_adm_mpa
    sigma_adm_kN_cm2 = sigma_adm_mpa * Fraction(1, 10)

    # Área necessária de base em cm²
    s_nec_cm2 = n_tot_k / sigma_adm_kN_cm2

    ap = pilar.largura_ap_cm
    bp = pilar.comprimento_bp_cm
    delta_p = ap - bp  # cm

    # Dimensão B pela fórmula quadrática: B² + (ap - bp)*B - S_nec = 0
    # B = [ -delta_p + sqrt(delta_p² + 4 * S_nec) ] / 2
    delta_p_sq = delta_p ** 2
    discriminante = delta_p_sq + Fraction(4, 1) * s_nec_cm2
    raiz_disc = raiz_quadrada_fracao(discriminante)
    b_teorico = (-delta_p + raiz_disc) / Fraction(2, 1)
    a_teorico = b_teorico + delta_p

    # Arredondamento executivo para múltiplos de 5 cm
    b_adotado = arredondar_cima_multiplo(b_teorico, 5)
    a_adotado = arredondar_cima_multiplo(a_teorico, 5)

    # Balanços
    ca = (a_adotado - ap) / Fraction(2, 1)
    cb = (b_adotado - bp) / Fraction(2, 1)
    balancos_iguais = (ca == cb)

    # Altura total h da sapata para garantir rigidez (NBR 6118 item 22.4):
    # h >= (A - ap)/3 e h >= (B - bp)/3
    # E para garantir inclinação da biela theta >= 30° (NBR 6118 item 22.4 / NBR 6122):
    # d >= max(ca, cb) * tan(30°) => h >= max(ca, cb) * 577/1000 + cnom + 1 cm
    cnom = obter_cobrimento_nominal(materiais)
    h_min_a = (a_adotado - ap) / Fraction(3, 1)
    h_min_b = (b_adotado - bp) / Fraction(3, 1)
    h_min_biela = max(ca, cb) * Fraction(577, 1000) + cnom + Fraction(1, 1)
    h_min = max(h_min_a, h_min_b, h_min_biela, Fraction(30, 1))
    h_adotado = arredondar_cima_multiplo(h_min, 5)

    # Altura da borda h0 >= h / 3 e >= 15 cm
    h0_min = max(h_adotado / Fraction(3, 1), Fraction(15, 1))
    h0_adotado = arredondar_cima_multiplo(h0_min, 5)

    # Altura útil d (descontando cobrimento e 1 cm de centroide de barras)
    d_util = h_adotado - cnom - Fraction(1, 1)

    # Tensão de contato efetiva no solo
    area_cm2 = a_adotado * b_adotado
    area_m2 = area_cm2 / Fraction(10000, 1)
    tensao_efetiva_kN_cm2 = n_tot_k / area_cm2
    tensao_efetiva_mpa = tensao_efetiva_kN_cm2 * Fraction(10, 1)
    atende_solo = tensao_efetiva_mpa <= sigma_adm_mpa

    e_rigida = (h_adotado >= h_min_a) and (h_adotado >= h_min_b)

    return ResultadoGeometriaSapata(
        dimensao_a_cm=a_adotado,
        dimensao_b_cm=b_adotado,
        area_sapata_m2=area_m2,
        balanco_ca_cm=ca,
        balanco_cb_cm=cb,
        balancos_iguais=balancos_iguais,
        altura_total_h_cm=h_adotado,
        altura_borda_h0_cm=h0_adotado,
        altura_util_d_cm=d_util,
        e_sapata_rigida=e_rigida,
        tensao_efetiva_solo_mpa=tensao_efetiva_mpa,
        tensao_admissivel_solo_mpa=sigma_adm_mpa,
        atende_tensao_solo=atende_solo,
    )


def dimensionar_flexao_sapata(
    pilar: PilarApoiado,
    materiais: PropriedadesMateriais,
    geometria: ResultadoGeometriaSapata,
) -> ResultadoFlexaoSapata:
    """Calcula as armaduras de flexão inferior pelo Método das Bielas e Tirantes."""
    # Solicitação normal de cálculo Nsd
    nsd = pilar.carga_normal_nsd_kn if pilar.carga_normal_nsd_kn is not None else pilar.carga_normal_nk_kn * GAMMA_F

    ap = pilar.largura_ap_cm
    bp = pilar.comprimento_bp_cm
    a = geometria.dimensao_a_cm
    b = geometria.dimensao_b_cm
    d = geometria.altura_util_d_cm

    # Forças de tração de cálculo no tirante (Método das Bielas):
    # Fsd,a = [ Nsd * (A - ap) ] / (8 * d)
    # Fsd,b = [ Nsd * (B - bp) ] / (8 * d)
    fsd_a_kn = (nsd * (a - ap)) / (Fraction(8, 1) * d)
    fsd_b_kn = (nsd * (b - bp)) / (Fraction(8, 1) * d)

    # Tensão de cálculo do aço fyd (kN/cm²)
    aco_info = TABELA_ACOS_NBR6118.get(materiais.tipo_aco, TABELA_ACOS_NBR6118["CA_50"])
    fyd_kN_cm2 = aco_info["fyd_kn_cm2"]

    # Áreas de aço calculadas (cm²)
    as_calc_a = fsd_a_kn / fyd_kN_cm2
    as_calc_b = fsd_b_kn / fyd_kN_cm2

    # Armadura mínima da seção de concreto (NBR 6118 Tabela 17.3)
    # rho_min = 0,15% da seção de concreto na direção considerada
    # Para a direção A, a seção transversal que resiste é B x h
    # Para a direção B, a seção transversal que resiste é A x h
    h = geometria.altura_total_h_cm
    as_min_a = RHO_MIN_SAPATA * b * h
    as_min_b = RHO_MIN_SAPATA * a * h

    as_final_a = max(as_calc_a, as_min_a)
    as_final_b = max(as_calc_b, as_min_b)

    return ResultadoFlexaoSapata(
        forca_tracao_fsd_a_kn=fsd_a_kn,
        forca_tracao_fsd_b_kn=fsd_b_kn,
        area_aco_calculada_a_cm2=as_calc_a,
        area_aco_calculada_b_cm2=as_calc_b,
        area_aco_minima_a_cm2=as_min_a,
        area_aco_minima_b_cm2=as_min_b,
        area_aco_final_a_cm2=as_final_a,
        area_aco_final_b_cm2=as_final_b,
    )


def verificar_puncao_compressao_sapata(
    pilar: PilarApoiado,
    materiais: PropriedadesMateriais,
    geometria: ResultadoGeometriaSapata,
) -> ResultadoPuncaoSapata:
    """Verifica a compressão diagonal da biela na ligação pilar-sapata e inclinação da biela."""
    nsd = pilar.carga_normal_nsd_kn if pilar.carga_normal_nsd_kn is not None else pilar.carga_normal_nk_kn * GAMMA_F

    ap = pilar.largura_ap_cm
    bp = pilar.comprimento_bp_cm
    d = geometria.altura_util_d_cm

    # Perímetro crítico u0 no contorno do pilar
    u0_cm = Fraction(2, 1) * (ap + bp)

    # Tensão de cálculo solicitante tau_sd (kN/cm²)
    tau_sd_kN_cm2 = nsd / (u0_cm * d)
    tau_sd_mpa = tau_sd_kN_cm2 * Fraction(10, 1)

    # Resistência de compressão da biela de concreto tau_Rd2 (NBR 6118 item 19.5.1):
    # tau_Rd2 = 0,27 * (1 - fck/250) * fcd
    fck = materiais.classe_concreto_fck
    fcd_kN_cm2 = Fraction(fck, 1) / (Fraction(10, 1) * GAMMA_C)  # kN/cm²
    fator_alpha_v = Fraction(1, 1) - Fraction(fck, 250)
    tau_rd2_kN_cm2 = Fraction(27, 100) * fator_alpha_v * fcd_kN_cm2
    tau_rd2_mpa = tau_rd2_kN_cm2 * Fraction(10, 1)

    atende_esmagamento = tau_sd_mpa <= tau_rd2_mpa

    # Inclinação das bielas comprimidas:
    # tan(theta_a) = d / ca, tan(theta_b) = d / cb
    # Para theta >= 30°, tan(theta) >= sqrt(3)/3 ~ 0,577
    ca = geometria.balanco_ca_cm
    cb = geometria.balanco_cb_cm

    tan_theta_a = d / ca if ca > 0 else Fraction(1, 1)
    tan_theta_b = d / cb if cb > 0 else Fraction(1, 1)

    # Estimativa de ângulo em graus: theta ~ arctan(tan)
    # Usamos razão exata: tan >= 577/1000 garante theta >= 30°
    tan_30_graus = Fraction(577, 1000)
    biela_ok_a = tan_theta_a >= tan_30_graus
    biela_ok_b = tan_theta_b >= tan_30_graus
    dispensa_puncao = biela_ok_a and biela_ok_b and geometria.e_sapata_rigida

    # Ângulo aproximado em graus para exibição
    theta_a_graus = Fraction(round(math.degrees(math.atan(float(tan_theta_a))) * 10), 10)
    theta_b_graus = Fraction(round(math.degrees(math.atan(float(tan_theta_b))) * 10), 10)

    return ResultadoPuncaoSapata(
        forca_normal_nsd_kn=nsd,
        perimetro_critico_u0_cm=u0_cm,
        tensao_solicitante_tau_sd_mpa=tau_sd_mpa,
        tensao_resistente_tau_rd2_mpa=tau_rd2_mpa,
        atende_compressão_diagonal_biela=atende_esmagamento,
        angulo_inclinacao_biela_a_graus=theta_a_graus,
        angulo_inclinacao_biela_b_graus=theta_b_graus,
        dispensa_armadura_puncao=dispensa_puncao,
    )


def selecionar_barras_direcao(
    area_necessaria_cm2: Fraction,
    largura_distribuicao_cm: Fraction,
    cobrimento_cm: Fraction,
    bitola_sugerida_mm: Fraction | None,
) -> Tuple[str, int, Fraction, Fraction, Fraction]:
    """Seleciona o número e bitola de barras comerciais com espaçamento adequado."""
    largura_util = largura_distribuicao_cm - Fraction(2, 1) * cobrimento_cm

    bitolas_candidatas = (
        [bitola_sugerida_mm]
        if bitola_sugerida_mm is not None
        else [
            Fraction(100, 10),
            Fraction(125, 10),
            Fraction(160, 10),
            Fraction(80, 10),
            Fraction(200, 10),
        ]
    )

    melhor_opcao = None

    for bitola in bitolas_candidatas:
        if bitola not in TABELA_BITOLAS_COMERCIAIS:
            continue
        area_barra = TABELA_BITOLAS_COMERCIAIS[bitola]["area_cm2"]
        n_barras = math.ceil((area_necessaria_cm2 / area_barra).numerator / (area_necessaria_cm2 / area_barra).denominator)
        if n_barras < 2:
            n_barras = 2

        espacamento = largura_util / Fraction(n_barras - 1, 1)
        area_efetiva = Fraction(n_barras, 1) * area_barra

        if espacamento >= ESPACAMENTO_MINIMO_BARRAS_CM and espacamento <= ESPACAMENTO_MAXIMO_BARRAS_CM:
            melhor_opcao = (n_barras, bitola, espacamento, area_efetiva)
            break
        elif melhor_opcao is None:
            melhor_opcao = (n_barras, bitola, espacamento, area_efetiva)

    if melhor_opcao is None:
        bitola_padrao = Fraction(125, 10)
        area_barra = TABELA_BITOLAS_COMERCIAIS[bitola_padrao]["area_cm2"]
        n_barras = math.ceil((area_necessaria_cm2 / area_barra).numerator / (area_necessaria_cm2 / area_barra).denominator)
        n_barras = max(2, n_barras)
        espacamento = largura_util / Fraction(n_barras - 1, 1)
        area_efetiva = Fraction(n_barras, 1) * area_barra
        melhor_opcao = (n_barras, bitola_padrao, espacamento, area_efetiva)

    n_barras, bitola, espacamento, area_efetiva = melhor_opcao
    descricao = f"{n_barras} Φ {float(bitola):.1f} mm c/ {float(espacamento):.1f} cm"
    return descricao, n_barras, bitola, espacamento, area_efetiva


def detalhar_armaduras_sapata(
    materiais: PropriedadesMateriais,
    detalhamento_pref: PreferenciasDetalhamento,
    geometria: ResultadoGeometriaSapata,
    flexao: ResultadoFlexaoSapata,
) -> ResultadoDetalhamentoSapata:
    """Detalhamento completo da malha ortogonal inferior e ganchos de ancoragem."""
    cnom = obter_cobrimento_nominal(materiais)

    # Direção A: barras estendem-se ao longo de A, distribuídas na largura B
    desc_a, n_a, bit_a, s_a, as_ef_a = selecionar_barras_direcao(
        flexao.area_aco_final_a_cm2,
        geometria.dimensao_b_cm,
        cnom,
        detalhamento_pref.bitola_sugerida_a_mm,
    )

    # Direção B: barras estendem-se ao longo de B, distribuídas na largura A
    desc_b, n_b, bit_b, s_b, as_ef_b = selecionar_barras_direcao(
        flexao.area_aco_final_b_cm2,
        geometria.dimensao_a_cm,
        cnom,
        detalhamento_pref.bitola_sugerida_b_mm,
    )

    # Comprimento do gancho vertical nas pontas das barras
    gancho_cm = max(geometria.altura_total_h_cm - Fraction(2, 1) * cnom, Fraction(15, 1))

    obs: List[str] = [
        f"Armadura inferior disposta em malha cruzada sobre lastro de concreto magro (cnom = {float(cnom):.1f} cm).",
        f"Ganchos verticais de {float(gancho_cm):.1f} cm previstos nas extremidades para ancoragem total no concreto.",
    ]

    return ResultadoDetalhamentoSapata(
        barras_direcao_a=desc_a,
        numero_barras_a=n_a,
        bitola_a_mm=bit_a,
        espacamento_a_cm=s_a,
        area_efetiva_a_cm2=as_ef_a,
        barras_direcao_b=desc_b,
        numero_barras_b=n_b,
        bitola_b_mm=bit_b,
        espacamento_b_cm=s_b,
        area_efetiva_b_cm2=as_ef_b,
        comprimento_gancho_cm=gancho_cm,
        observacoes=obs,
    )


def dimensionar_sapata_concreto(projeto: ProjetoSapata) -> ResultadoProjetoSapata:
    """Executa o dimensionamento completo de sapata isolada de concreto armado sob NBR 6118 / NBR 6122."""
    geo = dimensionar_geometria_sapata(projeto.pilar, projeto.solo, projeto.materiais)
    flex = dimensionar_flexao_sapata(projeto.pilar, projeto.materiais, geo)
    punc = verificar_puncao_compressao_sapata(projeto.pilar, projeto.materiais, geo)
    det = detalhar_armaduras_sapata(projeto.materiais, projeto.detalhamento, geo, flex)

    conf: Dict[str, bool] = {
        "tensao_solo": geo.atende_tensao_solo,
        "rigidez_sapata": geo.e_sapata_rigida,
        "compressao_diagonal_biela": punc.atende_compressão_diagonal_biela,
        "dispensa_puncao": punc.dispensa_armadura_puncao,
    }

    alertas: List[str] = []
    if not geo.atende_tensao_solo:
        alertas.append("Tensão efetiva de contato no solo superior à tensão admissível normatizada.")
    if not geo.e_sapata_rigida:
        alertas.append("Sapata flexível: a hipótese de distribuição uniforme de tensões não se aplica.")
    if not punc.atende_compressão_diagonal_biela:
        alertas.append("Tensão solicitante na ligação pilar-sapata excede a resistência de cálculo da biela de concreto.")
    if not punc.dispensa_armadura_puncao:
        alertas.append("Bielas com inclinação inferior a 30°: necessária verificação de armadura de punção.")

    recomendacoes: List[str] = []
    if all(conf.values()):
        recomendacoes.append("Sapata isolada e detalhamento plenamente conformes às normas ABNT NBR 6118:2023 e ABNT NBR 6122:2022.")
    else:
        recomendacoes.append("Ajuste as dimensões geométricas ou a classe de resistência fck para mitigar as restrições indicadas.")

    atende_geral = all(conf.values())

    return ResultadoProjetoSapata(
        identificacao=projeto.identificacao,
        normas=["ABNT NBR 6118:2023", "ABNT NBR 6122:2022"],
        geometria=geo,
        flexao=flex,
        puncao=punc,
        detalhamento=det,
        atende_geral=atende_geral,
        conformidades=conf,
        alertas=alertas,
        recomendacoes=recomendacoes,
    )
