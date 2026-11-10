from __future__ import annotations

from fractions import Fraction
from typing import Dict, Any

# Coeficientes de ponderação das ações e resistências (ABNT NBR 6118:2023 item 11.7 e 12.3)
GAMMA_C: Fraction = Fraction(14, 10)     # Coeficiente de minoração do concreto (1,40)
GAMMA_S: Fraction = Fraction(115, 100)   # Coeficiente de minoração do aço (1,15)
GAMMA_F: Fraction = Fraction(14, 10)     # Coeficiente de majoração das solicitações normais (1,40)

# Módulo de elasticidade do aço estrutural (NBR 6118 item 8.3.5)
ES_KN_CM2: Fraction = Fraction(21000, 1)  # 210.000 MPa = 21.000 kN/cm²

# Classes de Agressividade Ambiental e Cobrimentos Nominais para Fundações (NBR 6118 item 7.4.7.5 e NBR 6122)
# Em fundações sobre lastro de concreto magro (espessura >= 5 cm), cnom varia de 30 a 50 mm
TABELA_CAA_SAPATAS: Dict[str, Dict[str, Any]] = {
    "CAA_I": {
        "nome": "Classe I - Fraca (Rural / Submersa)",
        "cobrimento_nominal_cm": Fraction(4, 1),  # 40 mm (4 cm)
        "w_limite_mm": Fraction(4, 10),           # 0,40 mm
        "fck_minimo_mpa": 20,
    },
    "CAA_II": {
        "nome": "Classe II - Moderada (Urbana)",
        "cobrimento_nominal_cm": Fraction(4, 1),  # 40 mm (4 cm)
        "w_limite_mm": Fraction(3, 10),           # 0,30 mm
        "fck_minimo_mpa": 25,
    },
    "CAA_III": {
        "nome": "Classe III - Forte (Marinha / Industrial)",
        "cobrimento_nominal_cm": Fraction(5, 1),  # 50 mm (5 cm)
        "w_limite_mm": Fraction(2, 10),           # 0,20 mm
        "fck_minimo_mpa": 30,
    },
    "CAA_IV": {
        "nome": "Classe IV - Muito Forte (Industrial Agressiva / Respingos de Maré)",
        "cobrimento_nominal_cm": Fraction(55, 10), # 55 mm (5.5 cm)
        "w_limite_mm": Fraction(2, 10),            # 0,20 mm
        "fck_minimo_mpa": 40,
    },
}

# Propriedades mecânicas normativas dos concretos Grupo I (20 MPa a 50 MPa)
TABELA_CONCRETOS_NBR6118: Dict[int, Dict[str, Any]] = {
    20: {
        "nome": "C20",
        "fck_mpa": 20,
        "fctm_mpa": Fraction(221, 100),       # 0,3 * 20^(2/3) ~ 2,21 MPa
        "fctk_inf_mpa": Fraction(155, 100),   # 0,7 * fctm ~ 1,55 MPa
        "rho_min": Fraction(15, 10000),       # 0,150% (Tabela 17.3)
    },
    25: {
        "nome": "C25",
        "fck_mpa": 25,
        "fctm_mpa": Fraction(256, 100),       # 0,3 * 25^(2/3) ~ 2,56 MPa
        "fctk_inf_mpa": Fraction(180, 100),   # 0,7 * fctm ~ 1,80 MPa
        "rho_min": Fraction(15, 10000),       # 0,150% (Tabela 17.3)
    },
    30: {
        "nome": "C30",
        "fck_mpa": 30,
        "fctm_mpa": Fraction(290, 100),       # 0,3 * 30^(2/3) ~ 2,90 MPa
        "fctk_inf_mpa": Fraction(203, 100),   # 0,7 * fctm ~ 2,03 MPa
        "rho_min": Fraction(15, 10000),       # 0,150%
    },
    35: {
        "nome": "C35",
        "fck_mpa": 35,
        "fctm_mpa": Fraction(321, 100),       # 0,3 * 35^(2/3) ~ 3,21 MPa
        "fctk_inf_mpa": Fraction(225, 100),   # 0,7 * fctm ~ 2,25 MPa
        "rho_min": Fraction(164, 100000),     # 0,164%
    },
    40: {
        "nome": "C40",
        "fck_mpa": 40,
        "fctm_mpa": Fraction(351, 100),       # 0,3 * 40^(2/3) ~ 3,51 MPa
        "fctk_inf_mpa": Fraction(246, 100),   # 0,7 * fctm ~ 2,46 MPa
        "rho_min": Fraction(179, 100000),     # 0,179%
    },
    45: {
        "nome": "C45",
        "fck_mpa": 45,
        "fctm_mpa": Fraction(380, 100),       # 0,3 * 45^(2/3) ~ 3,80 MPa
        "fctk_inf_mpa": Fraction(266, 100),   # 0,7 * fctm ~ 2,66 MPa
        "rho_min": Fraction(194, 100000),     # 0,194%
    },
    50: {
        "nome": "C50",
        "fck_mpa": 50,
        "fctm_mpa": Fraction(407, 100),       # 0,3 * 50^(2/3) ~ 4,07 MPa
        "fctk_inf_mpa": Fraction(285, 100),   # 0,7 * fctm ~ 2,85 MPa
        "rho_min": Fraction(208, 100000),     # 0,208%
    },
}

# Aço CA-50 para armaduras passivas de fundação
TABELA_ACOS_NBR6118: Dict[str, Dict[str, Any]] = {
    "CA_50": {
        "nome": "Aço CA-50 (Nervurado)",
        "fyk_mpa": 500,
        "fyk_kn_cm2": Fraction(50, 1),
        "fyd_kn_cm2": Fraction(50, 1) / GAMMA_S,  # 43,478... kN/cm²
    },
    "CA_60": {
        "nome": "Aço CA-60 (Nervurado)",
        "fyk_mpa": 600,
        "fyk_kn_cm2": Fraction(60, 1),
        "fyd_kn_cm2": Fraction(60, 1) / GAMMA_S,  # 52,173... kN/cm²
    },
}

# Bitolas padronizadas comerciais para sapatas
TABELA_BITOLAS_COMERCIAIS: Dict[Fraction, Dict[str, Any]] = {
    Fraction(80, 10): {   # 8,0 mm
        "diametro_mm": Fraction(80, 10),
        "area_cm2": Fraction(50265, 100000),  # ~ 0,503 cm²
    },
    Fraction(100, 10): {  # 10,0 mm
        "diametro_mm": Fraction(100, 10),
        "area_cm2": Fraction(78540, 100000),  # ~ 0,785 cm²
    },
    Fraction(125, 10): {  # 12,5 mm
        "diametro_mm": Fraction(125, 10),
        "area_cm2": Fraction(122718, 100000), # ~ 1,227 cm²
    },
    Fraction(160, 10): {  # 16,0 mm
        "diametro_mm": Fraction(160, 10),
        "area_cm2": Fraction(201062, 100000), # ~ 2,011 cm²
    },
    Fraction(200, 10): {  # 20,0 mm
        "diametro_mm": Fraction(200, 10),
        "area_cm2": Fraction(314159, 100000), # ~ 3,142 cm²
    },
    Fraction(250, 10): {  # 25,0 mm
        "diametro_mm": Fraction(250, 10),
        "area_cm2": Fraction(490874, 100000), # ~ 4,909 cm²
    },
}

# Taxa mínima de armadura para sapatas (NBR 6118 item 19.5.3.1 e Tabela 17.3)
RHO_MIN_SAPATA: Fraction = Fraction(15, 10000)  # 0,15% da seção

# Espaçamento mínimo e máximo entre barras de sapatas
ESPACAMENTO_MINIMO_BARRAS_CM = Fraction(10, 1)  # 10 cm
ESPACAMENTO_MAXIMO_BARRAS_CM = Fraction(20, 1)  # 20 cm
