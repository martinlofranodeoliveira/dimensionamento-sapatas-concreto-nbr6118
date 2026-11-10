from __future__ import annotations

"""Pacote de dimensionamento e verificação de sapatas isoladas de concreto armado.

Normas regulamentadoras: ABNT NBR 6118:2023 e ABNT NBR 6122:2022.
Desenvolvido por LOFRANO TECNOLOGIA.
Aritmética 100% exata (Zero Float) com Frações e inteiros.
"""

__version__ = "1.0.0"
__author__ = "Martin Lofrano de Oliveira / LOFRANO TECNOLOGIA"
__license__ = "MIT"

from sapatas_concreto_nbr6118.constants import (
    GAMMA_C,
    GAMMA_S,
    GAMMA_F,
    ES_KN_CM2,
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
from sapatas_concreto_nbr6118.calculator import (
    dimensionar_geometria_sapata,
    dimensionar_flexao_sapata,
    verificar_puncao_compressao_sapata,
    detalhar_armaduras_sapata,
    dimensionar_sapata_concreto,
    raiz_quadrada_fracao,
)
from sapatas_concreto_nbr6118.exporters import (
    exportar_csv,
    gerar_relatorio_memorial,
    formatar_fracao_decimal,
)
from sapatas_concreto_nbr6118.svg_generator import gerar_painel_svg, escapar_xml

__all__ = [
    "__version__",
    "GAMMA_C",
    "GAMMA_S",
    "GAMMA_F",
    "ES_KN_CM2",
    "TABELA_CAA_SAPATAS",
    "TABELA_CONCRETOS_NBR6118",
    "TABELA_ACOS_NBR6118",
    "TABELA_BITOLAS_COMERCIAIS",
    "RHO_MIN_SAPATA",
    "ESPACAMENTO_MINIMO_BARRAS_CM",
    "ESPACAMENTO_MAXIMO_BARRAS_CM",
    "PilarApoiado",
    "PropriedadesSolo",
    "PropriedadesMateriais",
    "PreferenciasDetalhamento",
    "ProjetoSapata",
    "ResultadoGeometriaSapata",
    "ResultadoFlexaoSapata",
    "ResultadoPuncaoSapata",
    "ResultadoDetalhamentoSapata",
    "ResultadoProjetoSapata",
    "dimensionar_geometria_sapata",
    "dimensionar_flexao_sapata",
    "verificar_puncao_compressao_sapata",
    "detalhar_armaduras_sapata",
    "dimensionar_sapata_concreto",
    "raiz_quadrada_fracao",
    "exportar_csv",
    "gerar_relatorio_memorial",
    "formatar_fracao_decimal",
    "gerar_painel_svg",
    "escapar_xml",
]
