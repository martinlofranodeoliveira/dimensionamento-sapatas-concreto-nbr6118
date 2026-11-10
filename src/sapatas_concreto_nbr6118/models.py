from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class PilarApoiado:
    """Geometria e solicitação normal de compressão do pilar que descarrega na sapata."""
    largura_ap_cm: Fraction
    comprimento_bp_cm: Fraction
    carga_normal_nk_kn: Fraction
    carga_normal_nsd_kn: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.largura_ap_cm <= 0:
            raise ValueError("Dimensão do pilar ap deve ser estritamente positiva.")
        if self.comprimento_bp_cm <= 0:
            raise ValueError("Dimensão do pilar bp deve ser estritamente positiva.")
        if self.carga_normal_nk_kn <= 0:
            raise ValueError("Carga axial Nk do pilar deve ser estritamente positiva.")


@dataclass(frozen=True)
class PropriedadesSolo:
    """Capacidade de suporte do maciço geotécnico de assentamento segundo NBR 6122."""
    tensao_admissivel_sigma_adm_mpa: Fraction  # MPa (1 MPa = 0,10 kN/cm² = 1000 kPa)
    descricao_camada: str = "Solo firme de fundação"

    def __post_init__(self) -> None:
        if self.tensao_admissivel_sigma_adm_mpa <= 0:
            raise ValueError("Tensão admissível do solo deve ser estritamente positiva.")


@dataclass(frozen=True)
class PropriedadesMateriais:
    """Especificações dos materiais e durabilidade da fundação (NBR 6118 / NBR 6122)."""
    classe_concreto_fck: int = 25  # C25 padrão
    tipo_aco: str = "CA_50"
    classe_agressividade: str = "CAA_II"
    cobrimento_nominal_cm: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.classe_concreto_fck < 20 or self.classe_concreto_fck > 50:
            raise ValueError(f"Classe de concreto C{self.classe_concreto_fck} fora do escopo Grupo I (C20 a C50).")
        if self.classe_agressividade not in ("CAA_I", "CAA_II", "CAA_III", "CAA_IV"):
            raise ValueError(f"Classe de Agressividade Ambiental '{self.classe_agressividade}' inválida.")


@dataclass(frozen=True)
class PreferenciasDetalhamento:
    """Preferências para malha de armadura inferior e geometria da sapata."""
    bitola_sugerida_a_mm: Optional[Fraction] = None
    bitola_sugerida_b_mm: Optional[Fraction] = None
    adotar_ganchos_ancoragem: bool = True
    d_linha_estimado_cm: Optional[Fraction] = None


@dataclass(frozen=True)
class ProjetoSapata:
    """Entrada completa para dimensionamento de sapata isolada de concreto armado."""
    identificacao: str
    pilar: PilarApoiado
    solo: PropriedadesSolo
    materiais: PropriedadesMateriais = field(default_factory=PropriedadesMateriais)
    detalhamento: PreferenciasDetalhamento = field(default_factory=PreferenciasDetalhamento)


@dataclass(frozen=True)
class ResultadoGeometriaSapata:
    """Resultados do dimensionamento geométrico em planta e elevação."""
    dimensao_a_cm: Fraction
    dimensao_b_cm: Fraction
    area_sapata_m2: Fraction
    balanco_ca_cm: Fraction
    balanco_cb_cm: Fraction
    balancos_iguais: bool
    altura_total_h_cm: Fraction
    altura_borda_h0_cm: Fraction
    altura_util_d_cm: Fraction
    e_sapata_rigida: bool
    tensao_efetiva_solo_mpa: Fraction
    tensao_admissivel_solo_mpa: Fraction
    atende_tensao_solo: bool


@dataclass(frozen=True)
class ResultadoFlexaoSapata:
    """Resultados do dimensionamento das armaduras de tração por bielas e tirantes."""
    forca_tracao_fsd_a_kn: Fraction
    forca_tracao_fsd_b_kn: Fraction
    area_aco_calculada_a_cm2: Fraction
    area_aco_calculada_b_cm2: Fraction
    area_aco_minima_a_cm2: Fraction
    area_aco_minima_b_cm2: Fraction
    area_aco_final_a_cm2: Fraction
    area_aco_final_b_cm2: Fraction


@dataclass(frozen=True)
class ResultadoPuncaoSapata:
    """Verificações de punção e compressão diagonal na ligação pilar-sapata."""
    forca_normal_nsd_kn: Fraction
    perimetro_critico_u0_cm: Fraction
    tensao_solicitante_tau_sd_mpa: Fraction
    tensao_resistente_tau_rd2_mpa: Fraction
    atende_compressão_diagonal_biela: bool
    angulo_inclinacao_biela_a_graus: Fraction
    angulo_inclinacao_biela_b_graus: Fraction
    dispensa_armadura_puncao: bool


@dataclass(frozen=True)
class ResultadoDetalhamentoSapata:
    """Detalhamento da malha de armadura inferior nas duas direções ortogonais."""
    barras_direcao_a: str
    numero_barras_a: int
    bitola_a_mm: Fraction
    espacamento_a_cm: Fraction
    area_efetiva_a_cm2: Fraction
    barras_direcao_b: str
    numero_barras_b: int
    bitola_b_mm: Fraction
    espacamento_b_cm: Fraction
    area_efetiva_b_cm2: Fraction
    comprimento_gancho_cm: Fraction
    observacoes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResultadoProjetoSapata:
    """Resultado consolidado do dimensionamento e verificações normativas da sapata."""
    identificacao: str
    normas: List[str]
    geometria: ResultadoGeometriaSapata
    flexao: ResultadoFlexaoSapata
    puncao: ResultadoPuncaoSapata
    detalhamento: ResultadoDetalhamentoSapata
    atende_geral: bool
    conformidades: Dict[str, bool]
    alertas: List[str]
    recomendacoes: List[str]
