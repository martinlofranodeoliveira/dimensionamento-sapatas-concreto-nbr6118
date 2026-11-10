from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from typing import Optional, List

from sapatas_concreto_nbr6118 import __version__
from sapatas_concreto_nbr6118.constants import (
    TABELA_CAA_SAPATAS,
    TABELA_CONCRETOS_NBR6118,
    TABELA_ACOS_NBR6118,
    TABELA_BITOLAS_COMERCIAIS,
)
from sapatas_concreto_nbr6118.models import (
    PilarApoiado,
    PropriedadesSolo,
    PropriedadesMateriais,
    PreferenciasDetalhamento,
    ProjetoSapata,
)
from sapatas_concreto_nbr6118.calculator import dimensionar_sapata_concreto
from sapatas_concreto_nbr6118.codecs import (
    carregar_json_canonico,
    salvar_json_canonico,
    deserializar_projeto,
)
from sapatas_concreto_nbr6118.exporters import (
    exportar_csv,
    gerar_relatorio_memorial,
    formatar_fracao_decimal,
)
from sapatas_concreto_nbr6118.svg_generator import gerar_painel_svg


def parse_fracao_cli(texto: str) -> Fraction:
    """Converte string recebida na linha de comando em Fraction sem admitir float."""
    t = texto.strip().replace(",", ".")
    if "/" in t:
        partes = t.split("/")
        if len(partes) == 2:
            return Fraction(int(partes[0].strip()), int(partes[1].strip()))
    if "." in t:
        partes = t.split(".")
        if len(partes) == 2:
            num = int(partes[0] + partes[1])
            den = 10 ** len(partes[1])
            return Fraction(num, den)
    return Fraction(int(t), 1)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sapatas-concreto",
        description="Dimensionamento e verificação de sapatas isoladas de concreto armado segundo ABNT NBR 6118:2023 e NBR 6122:2022. LOFRANO TECNOLOGIA.",
    )
    subparsers = parser.add_subparsers(dest="comando", help="Comandos disponíveis")

    # Comando: dimensionar
    p_dim = subparsers.add_parser("dimensionar", help="Dimensiona sapata aos estados limites ELU e geotécnico")
    p_dim.add_argument("--arquivo", "-a", type=str, help="Caminho do arquivo JSON de projeto")
    p_dim.add_argument("--ap", type=str, default="20", help="Largura do pilar ap em cm (padrão: 20 cm)")
    p_dim.add_argument("--bp", type=str, default="40", help="Comprimento do pilar bp em cm (padrão: 40 cm)")
    p_dim.add_argument("--nk", type=str, help="Carga axial característica Nk em kN (ex: 400)")
    p_dim.add_argument("--sigma-adm", type=str, default="0.20", help="Tensão admissível do solo em MPa (padrão: 0.20 MPa = 200 kPa)")
    p_dim.add_argument("--fck", type=int, default=25, choices=[20, 25, 30, 35, 40, 45, 50], help="Resistência característica do concreto em MPa (padrão: 25)")
    p_dim.add_argument("--caa", type=str, default="CAA_II", choices=["CAA_I", "CAA_II", "CAA_III", "CAA_IV"], help="Classe de Agressividade Ambiental (padrão: CAA_II)")

    # Saídas
    p_dim.add_argument("--saida-json", "-j", type=str, help="Caminho para salvar resultado consolidado em JSON")
    p_dim.add_argument("--saida-csv", "-c", type=str, help="Caminho para salvar planilha estruturada em CSV")
    p_dim.add_argument("--saida-relatorio", "-r", type=str, help="Caminho para salvar memorial descritivo em TXT")
    p_dim.add_argument("--painel-svg", "-s", type=str, help="Caminho para gerar e salvar painel técnico em SVG")

    # Comando: tabelas
    subparsers.add_parser("tabelas", help="Exibe as tabelas normativas de agressividade, cobrimentos e taxas mínimas")

    # Comando: materiais
    subparsers.add_parser("materiais", help="Lista as classes de concreto, aços e bitolas comerciais cadastrados")

    # Comando: versao
    subparsers.add_parser("versao", help="Exibe a versão do pacote")

    return parser


def comando_tabelas() -> int:
    print("=" * 80)
    print("TABELAS NORMATIVAS — FUNDAÇÕES E SAPATAS (ABNT NBR 6118 / NBR 6122)")
    print("=" * 80)
    print("\nCLASSES DE AGRESSIVIDADE AMBIENTAL E COBRIMENTOS NOMINAIS (COM LASTRO 5 CM):")
    print("-" * 80)
    print(f"{'Classe':<10} | {'Agressividade':<30} | {'Cobrimento':<18} | {'w_lim (Fissura)'}")
    print("-" * 80)
    for caa, dados in TABELA_CAA_SAPATAS.items():
        cnom_cm = formatar_fracao_decimal(dados["cobrimento_nominal_cm"], 1)
        wlim = formatar_fracao_decimal(dados["w_limite_mm"], 2)
        print(f"{caa:<10} | {dados['nome']:<30} | {cnom_cm} cm (40 mm)    | {wlim} mm")
    print("=" * 80)
    return 0


def comando_materiais() -> int:
    print("=" * 80)
    print("CATÁLOGO DE MATERIAIS ESTRUTURAIS E BITOLAS COMERCIAIS PARA SAPATAS")
    print("=" * 80)
    print("\n1. AÇOS ESTRUTURAIS")
    print("-" * 60)
    for cod, dados in TABELA_ACOS_NBR6118.items():
        fyd_str = formatar_fracao_decimal(dados["fyd_kn_cm2"], 2)
        print(f"{cod:<10} | {dados['nome']:<35} | fyd = {fyd_str} kN/cm²")

    print("\n2. BITOLAS PADRONIZADAS COMERCIAIS")
    print("-" * 60)
    print(f"{'Diâmetro Nominal':<20} | {'Área da Seção (cm²)'}")
    print("-" * 60)
    for bitola, dados in TABELA_BITOLAS_COMERCIAIS.items():
        d_str = formatar_fracao_decimal(bitola, 1)
        a_str = formatar_fracao_decimal(dados["area_cm2"], 3)
        print(f"Φ {d_str} mm{'':<12} | {a_str} cm²")
    print("=" * 80)
    return 0


def executar_dimensionamento_cli(args: argparse.Namespace) -> int:
    if args.arquivo:
        dados = carregar_json_canonico(args.arquivo)
        projeto = deserializar_projeto(dados)
    elif args.nk:
        ap = parse_fracao_cli(args.ap)
        bp = parse_fracao_cli(args.bp)
        nk = parse_fracao_cli(args.nk)
        sigma_adm = parse_fracao_cli(args.sigma_adm)

        pilar = PilarApoiado(
            largura_ap_cm=ap,
            comprimento_bp_cm=bp,
            carga_normal_nk_kn=nk,
        )
        solo = PropriedadesSolo(
            tensao_admissivel_sigma_adm_mpa=sigma_adm,
        )
        materiais = PropriedadesMateriais(
            classe_concreto_fck=args.fck,
            classe_agressividade=args.caa,
        )
        projeto = ProjetoSapata(
            identificacao=f"Sapata Pilar {float(ap):.0f}x{float(bp):.0f} cm - Nk={float(nk):.0f}kN",
            pilar=pilar,
            solo=solo,
            materiais=materiais,
        )
    else:
        print("Erro: Forneça um arquivo JSON (--arquivo) ou informe a carga normal do pilar (--nk).")
        return 1

    resultado = dimensionar_sapata_concreto(projeto)

    relatorio = gerar_relatorio_memorial(resultado)
    if args.saida_relatorio:
        with open(args.saida_relatorio, "w", encoding="utf-8") as f:
            f.write(relatorio)
        print(f"Memorial descritivo salvo em: {args.saida_relatorio}")
    else:
        print(relatorio)

    if args.saida_json:
        salvar_json_canonico(args.saida_json, resultado)
        print(f"Resultado JSON canônico salvo em: {args.saida_json}")

    if args.saida_csv:
        csv_texto = exportar_csv(resultado)
        with open(args.saida_csv, "w", encoding="utf-8") as f:
            f.write(csv_texto)
        print(f"Planilha CSV salva em: {args.saida_csv}")

    if args.painel_svg:
        svg_conteudo = gerar_painel_svg(resultado)
        with open(args.painel_svg, "w", encoding="utf-8") as f:
            f.write(svg_conteudo)
        print(f"Painel técnico SVG salvo em: {args.painel_svg}")

    return 0 if resultado.atende_geral else 1


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass
    parser = criar_parser()
    args = parser.parse_args(argv)

    if args.comando == "tabelas":
        return comando_tabelas()
    elif args.comando == "materiais":
        return comando_materiais()
    elif args.comando == "versao":
        print(f"sapatas-concreto v{__version__} — ABNT NBR 6118:2023 / ABNT NBR 6122:2022 (LOFRANO TECNOLOGIA)")
        return 0
    elif args.comando == "dimensionar":
        return executar_dimensionamento_cli(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
