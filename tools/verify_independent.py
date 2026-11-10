"""Auditor independente em SQLite para dimensionamento de sapatas ABNT NBR 6118 / NBR 6122.

Este script é 100% autônomo: NÃO importa o pacote `sapatas_concreto_nbr6118`.
Utiliza apenas a biblioteca padrão do Python (`sqlite3`, `json`, `sys`, `math`, `os`).
"""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
from typing import Any, Dict


def criar_banco_auditoria() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE parametros_normativos (
        chave TEXT PRIMARY KEY,
        valor REAL,
        descricao TEXT
    );
    """)

    cur.executescript("""
    INSERT INTO parametros_normativos (chave, valor, descricao) VALUES
        ('gamma_c', 1.40, 'Coeficiente de minoração do concreto'),
        ('gamma_s', 1.15, 'Coeficiente de minoração do aço'),
        ('gamma_f', 1.40, 'Coeficiente de majoração das ações'),
        ('peso_proprio_fator', 1.05, 'Fator de acréscimo de peso próprio da sapata'),
        ('tan_theta_lim', 0.57735, 'Tangente mínima do ângulo da biela (30 graus)'),
        ('rho_min_sapata', 0.0015, 'Taxa geométrica mínima de armadura para sapatas rígidas');
    """)

    cur.execute("""
    CREATE TABLE sapatas_auditadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        identificacao TEXT,
        ap_cm REAL,
        bp_cm REAL,
        nk_kn REAL,
        nsd_kn REAL,
        sigma_adm_mpa REAL,
        dimensao_a_cm REAL,
        dimensao_b_cm REAL,
        balanco_ca_cm REAL,
        balanco_cb_cm REAL,
        altura_h_cm REAL,
        altura_h0_cm REAL,
        altura_d_cm REAL,
        tensao_solo_efetiva_mpa REAL,
        fsd_a_kn REAL,
        fsd_b_kn REAL,
        as_a_cm2 REAL,
        as_b_cm2 REAL,
        tau_sd_mpa REAL,
        tau_rd2_mpa REAL,
        theta_a_graus REAL,
        theta_b_graus REAL,
        status_tensao_solo TEXT,
        status_rigidez TEXT,
        status_biela_compressao TEXT,
        status_dispensa_puncao TEXT,
        status_geral TEXT
    );
    """)

    conn.commit()
    return conn


def fracao_para_float(v: Any) -> float:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, dict) and "num" in v and "den" in v:
        return float(v["num"]) / float(v["den"])
    if isinstance(v, str):
        if "/" in v:
            p = v.split("/")
            return float(p[0]) / float(p[1])
        return float(v)
    raise ValueError(f"Não foi possível converter {v} em número.")


def auditar_arquivo_projeto(caminho_json: str, conn: sqlite3.Connection) -> bool:
    if not os.path.exists(caminho_json):
        print(f"[ERRO] Arquivo não encontrado: {caminho_json}")
        return False

    with open(caminho_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    identificacao = dados.get("identificacao", "Sapata Sem Nome")
    pil = dados.get("pilar", {})
    ap = fracao_para_float(pil["largura_ap_cm"])
    bp = fracao_para_float(pil["comprimento_bp_cm"])
    nk = fracao_para_float(pil["carga_normal_nk_kn"])

    solo = dados.get("solo", {})
    sigma_adm_mpa = fracao_para_float(solo["tensao_admissivel_sigma_adm_mpa"])

    mat = dados.get("materiais", {})
    fck = fracao_para_float(mat.get("classe_concreto_fck", 25))
    caa = mat.get("classe_agressividade", "CAA_II")

    # Cobrimento nominal conforme CAA
    cobrimento_map = {
        "CAA_I": 4.0,
        "CAA_II": 4.0,
        "CAA_III": 5.0,
        "CAA_IV": 5.5,
    }
    cnom = cobrimento_map.get(caa, 4.0)

    # Coeficientes normativos
    gamma_c = 1.40
    gamma_s = 1.15
    gamma_f = 1.40
    peso_proprio_fator = 1.05

    # 1. Geometria da Base com Balanços Iguais
    n_tot_k = nk * peso_proprio_fator  # kN
    sigma_adm_kN_cm2 = sigma_adm_mpa * 0.10  # 1 MPa = 0,10 kN/cm²
    s_nec_cm2 = n_tot_k / sigma_adm_kN_cm2

    delta_p = ap - bp
    # B² + (ap - bp)*B - S_nec = 0
    discriminante = (delta_p ** 2) + 4.0 * s_nec_cm2
    b_teorico = (-delta_p + math.sqrt(discriminante)) / 2.0
    a_teorico = b_teorico + delta_p

    # Arredondamento para múltiplos de 5 cm
    dim_b = math.ceil(b_teorico / 5.0) * 5.0
    dim_a = math.ceil(a_teorico / 5.0) * 5.0

    ca = (dim_a - ap) / 2.0
    cb = (dim_b - bp) / 2.0

    # 2. Altura h e Rigidez
    h_min_a = (dim_a - ap) / 3.0
    h_min_b = (dim_b - bp) / 3.0
    tan_30 = 0.577350269
    h_min_biela = max(ca, cb) * 0.577 + cnom + 1.0
    h_min = max(h_min_a, h_min_b, h_min_biela, 30.0)
    dim_h = math.ceil(h_min / 5.0) * 5.0

    dim_h0 = math.ceil(max(dim_h / 3.0, 15.0) / 5.0) * 5.0
    dim_d = dim_h - cnom - 1.0

    # Verificação de tensões no solo
    area_cm2 = dim_a * dim_b
    tensao_solo_efetiva = (n_tot_k / area_cm2) * 10.0  # MPa
    status_tensao_solo = "CONFORME" if tensao_solo_efetiva <= (sigma_adm_mpa + 1e-6) else "REPROVADO"

    # Verificação de rigidez
    status_rigidez = "CONFORME" if (dim_h >= h_min_a and dim_h >= h_min_b) else "REPROVADO"

    # 3. Flexão (Método das Bielas e Tirantes)
    nsd = nk * gamma_f
    fsd_a = (nsd * (dim_a - ap)) / (8.0 * dim_d)
    fsd_b = (nsd * (dim_b - bp)) / (8.0 * dim_d)

    fyd_kN_cm2 = 50.0 / gamma_s
    as_a_calc = fsd_a / fyd_kN_cm2
    as_b_calc = fsd_b / fyd_kN_cm2

    rho_min = 0.0015
    as_a_min = rho_min * dim_b * dim_h
    as_b_min = rho_min * dim_a * dim_h

    as_a_final = max(as_a_calc, as_a_min)
    as_b_final = max(as_b_calc, as_b_min)

    # 4. Punção / Compressão Diagonal
    u0 = 2.0 * (ap + bp)
    tau_sd_kN_cm2 = nsd / (u0 * dim_d)
    tau_sd_mpa = tau_sd_kN_cm2 * 10.0

    fcd_kN_cm2 = (fck / 10.0) / gamma_c
    fator_alpha_v = 1.0 - (fck / 250.0)
    tau_rd2_kN_cm2 = 0.27 * fator_alpha_v * fcd_kN_cm2
    tau_rd2_mpa = tau_rd2_kN_cm2 * 10.0

    status_biela_comp = "CONFORME" if tau_sd_mpa <= tau_rd2_mpa else "REPROVADO"

    # Ângulo da biela
    tan_theta_a = dim_d / ca if ca > 0 else 1.0
    tan_theta_b = dim_d / cb if cb > 0 else 1.0
    theta_a_graus = math.degrees(math.atan(tan_theta_a))
    theta_b_graus = math.degrees(math.atan(tan_theta_b))

    status_dispensa_puncao = "CONFORME" if (theta_a_graus >= 29.99 and theta_b_graus >= 29.99 and status_rigidez == "CONFORME") else "REPROVADO"

    status_geral = "APROVADO" if all(
        s == "CONFORME" for s in (status_tensao_solo, status_rigidez, status_biela_comp, status_dispensa_puncao)
    ) else "REPROVADO"

    cur = conn.cursor()
    cur.execute("""
    INSERT INTO sapatas_auditadas (
        identificacao, ap_cm, bp_cm, nk_kn, nsd_kn, sigma_adm_mpa,
        dimensao_a_cm, dimensao_b_cm, balanco_ca_cm, balanco_cb_cm,
        altura_h_cm, altura_h0_cm, altura_d_cm, tensao_solo_efetiva_mpa,
        fsd_a_kn, fsd_b_kn, as_a_cm2, as_b_cm2, tau_sd_mpa, tau_rd2_mpa,
        theta_a_graus, theta_b_graus, status_tensao_solo, status_rigidez,
        status_biela_compressao, status_dispensa_puncao, status_geral
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        identificacao, ap, bp, nk, nsd, sigma_adm_mpa,
        dim_a, dim_b, ca, cb,
        dim_h, dim_h0, dim_d, tensao_solo_efetiva,
        fsd_a, fsd_b, as_a_final, as_b_final, tau_sd_mpa, tau_rd2_mpa,
        theta_a_graus, theta_b_graus, status_tensao_solo, status_rigidez,
        status_biela_comp, status_dispensa_puncao, status_geral,
    ))
    conn.commit()

    print(f"\n================================================================================")
    print(f"AUDITORIA INDEPENDENTE SQLITE: {identificacao}")
    print(f"================================================================================")
    print(f" Pilar: {ap:.1f} x {bp:.1f} cm | Carga Nk: {nk:.1f} kN (Nsd: {nsd:.1f} kN)")
    print(f" Base Sapata (A x B): {dim_a:.1f} x {dim_b:.1f} cm (ca={ca:.1f} cm, cb={cb:.1f} cm)")
    print(f" Alturas: h={dim_h:.1f} cm, h0={dim_h0:.1f} cm, d={dim_d:.1f} cm")
    print(f" Pressão Solo: sigma_ef = {tensao_solo_efetiva:.3f} MPa <= {sigma_adm_mpa:.3f} MPa -> [{status_tensao_solo}]")
    print(f" Rigidez Sapata: h >= max({h_min_a:.1f}, {h_min_b:.1f}) cm -> [{status_rigidez}]")
    print(f" Armadura Dir A: Fsd,a = {fsd_a:.2f} kN -> As,a = {as_a_final:.2f} cm²")
    print(f" Armadura Dir B: Fsd,b = {fsd_b:.2f} kN -> As,b = {as_b_final:.2f} cm²")
    print(f" Compressão Diagonal: tau_sd = {tau_sd_mpa:.2f} MPa <= tau_Rd2 = {tau_rd2_mpa:.2f} MPa -> [{status_biela_comp}]")
    print(f" Ângulo Bielas: theta_a = {theta_a_graus:.1f}°, theta_b = {theta_b_graus:.1f}° (>= 30°) -> [{status_dispensa_puncao}]")
    print(f" STATUS GERAL DA AUDITORIA: [{status_geral}]")
    print(f"================================================================================")

    return status_geral == "APROVADO"


def main() -> int:
    conn = criar_banco_auditoria()
    exemplos = [
        "examples/sapata_residencial_pilar_retangular.json",
        "examples/sapata_edificio_carga_elevada.json",
    ]

    sucessos = 0
    for ex in exemplos:
        caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ex)
        if auditar_arquivo_projeto(caminho, conn):
            sucessos += 1

    print(f"\nResumo da Auditoria Independente: {sucessos}/{len(exemplos)} projetos aprovados.")
    return 0 if sucessos == len(exemplos) else 1


if __name__ == "__main__":
    sys.exit(main())
