"""
Generador de Datos Sintéticos para Simulación PUI.
Permite ejecutar el sistema MVC y probar la generación de informes sin requerir
una base de datos PostgreSQL activa, incluyendo el balance de Cobertura de Demanda (Contratos vs Bolsa Spot).
"""
from typing import List, Dict, Any
from datetime import datetime
import math

# Lista de mercados representativos del MEM colombiano
MERCADOS = [
    {"code": "ANTIOQUIA", "name": "EPM - ANTIOQUIA", "base_vr": 25000000.0},
    {"code": "BOGOTA", "name": "ENEL - BOGOTA CUNDINAMARCA", "base_vr": 35000000.0},
    {"code": "CARIBE_MAR", "name": "AFINIA - CARIBE MAR", "base_vr": 28000000.0},
    {"code": "CARIBE_SOL", "name": "AIR-E - CARIBE SOL", "base_vr": 22000000.0},
    {"code": "VALLE", "name": "CVC - VALLE DEL CAUCA", "base_vr": 18000000.0},
    {"code": "SANTANDER", "name": "ESSA - SANTANDER", "base_vr": 14000000.0},
    {"code": "CUNDINAMARCA", "name": "EEC - CUNDINAMARCA", "base_vr": 9000000.0},
    {"code": "TOLIMA", "name": "ELET - TOLIMA", "base_vr": 7500000.0},
]

AGENTE_NOMBRES = {
    "ETTC": "ENERTOTAL S.A. E.S.P.",
    "ENDC": "ENEL COLOMBIA S.A. E.S.P.",
    "NRCC": "ENERCO S.A. E.S.P.",
    "EPMC": "EPM S.A. E.S.P."
}

def _demanda_factor(code: str) -> float:
    """
    Factor determinístico de participación de demanda del agente en el sistema.
    Derivado del hash del código para que CADA agente tenga una demanda/sobrecosto
    distinto y realista (rango típico de comercializadores del MEM: 0.5% - 15%).
    Esto permite comparar de forma significativa el PUI/sobrecosto entre agentes.
    """
    h = 0
    for ch in str(code):
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    # Normaliza a un factor entre 0.005 (0.5%) y 0.15 (15%)
    norm = (h % 1000) / 1000.0  # 0.0 - 0.999
    factor = 0.005 + (norm * 0.145)  # 0.5% a 15%
    return round(factor, 6)


def _cobertura_contratos_realista(code: str, month_idx: int, total_months: int) -> float:
    """
    Genera una cobertura de contratos realista y variable por agente/mes.
    Simula tendencias observadas en la BD real: ~100% historically, cayendo a 74-88%
    en meses recientes (2026). Rango acotado [0.55, 1.00].
    """
    h = 0
    for ch in str(code):
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    base = 0.82 + ((h % 180) / 1000.0)  # base 0.82 - 0.99
    seasonal = 0.02 * math.sin(2 * math.pi * month_idx / 12.0)
    trend = -0.015 * max(0, (month_idx - total_months * 0.7)) / total_months
    noise = ((h * 17 + month_idx * 31) % 100 - 50) / 5000.0
    pct = base + seasonal + trend + noise
    return max(0.55, min(1.00, pct))

def generate_mock_pui_data(params: Any) -> List[Dict[str, Any]]:
    """
    Genera un conjunto de datos sintéticos calculado rigurosamente según
    las fórmulas del PUI definidas en example.sql e integrando la Cobertura de Demanda (Contratos vs Bolsa).
    """
    start_date = datetime.strptime(params.fecha_inicio, "%Y-%m-%d")
    end_date = datetime.strptime(params.fecha_fin, "%Y-%m-%d")

    months = []
    curr = start_date.replace(day=1)
    while curr < end_date:
        months.append(curr.strftime("%Y-%m-%d"))
        if curr.month == 12:
            curr = curr.replace(year=curr.year + 1, month=1)
        else:
            curr = curr.replace(month=curr.month + 1)

    cior_code = "ENDC"
    cior_name = AGENTE_NOMBRES.get(cior_code, "ENEL COLOMBIA S.A. E.S.P.")
    agente_target = params.agente_objetivo
    agente_name = AGENTE_NOMBRES.get(agente_target, f"{agente_target} S.A. E.S.P.")
    rol_pui = "CIOR" if agente_target == cior_code else "CNIOR"

    # Factor de participación de demanda del agente (diferenciado por agente)
    demanda_factor = _demanda_factor(agente_target)
    vr_cior_base = 525000000.0

    # Cobertura por defecto (fallback cuando no hay histórico real)
    default_pct = getattr(params, "pct_cobertura_contratos", 0.85)
    total_months = len(months)

    rows = []

    for month_idx, mes in enumerate(months):
        # Cobertura de contratos REALISTA por agente/mes (no constante)
        pct_contratos = _cobertura_contratos_realista(agente_target, month_idx, total_months)
        pct_bolsa = 1.0 - pct_contratos
        cu = round(280.0 + (month_idx * 2.5) + math.sin(month_idx) * 15, 4)
        cu_m1 = round(280.0 + ((month_idx - 1) * 2.5) + math.sin(max(0, month_idx - 1)) * 15, 4)

        vr_total_todos_agentes = 1500000000.0 + (month_idx * 10000000.0)
        vr_total_cniors = vr_total_todos_agentes * 0.65
        # Demanda del agente objetivo: diferenciada por factor determinístico por agente
        vr_target_mes = vr_total_todos_agentes * demanda_factor if rol_pui == "CNIOR" else vr_cior_base

        for m in MERCADOS:
            m_code = m["code"]
            m_name = m["name"]
            base_vr = m["base_vr"]

            vr_mercado_kwh = base_vr * (1 + 0.01 * month_idx)
            vr_m1 = base_vr * (1 + 0.01 * max(0, month_idx - 1))
            vr_m2 = base_vr * (1 + 0.01 * max(0, month_idx - 2))

            vpui_actual = vr_mercado_kwh * params.pct_areas_especiales
            vpui_m1 = vr_m1 * params.pct_areas_especiales

            if month_idx < 2:
                crpui_unitario = 0.0
                cfpui_unitario = 0.0
            else:
                if params.esquema_competitivo:
                    crpui_unitario = 0.0
                    cfpui_unitario = params.cfpui
                else:
                    crpui_unitario = (params.rcpui * vpui_m1) / (vr_m1 * cu_m1) if (vr_m1 > 0 and cu_m1 > 0) else 0.0
                    cfpui_unitario = 0.0

            pui_mercado_total = (crpui_unitario + cfpui_unitario) * vr_m2
            giro_obligatorio_mercado = pui_mercado_total
            recaudo_real_mercado = giro_obligatorio_mercado * params.factor_recaudo_cnior

            part_total_pct = (vr_target_mes / vr_total_todos_agentes) * 100.0
            part_cnior_pct = (vr_target_mes / vr_total_cniors) * 100.0 if rol_pui == "CNIOR" else 0.0

            pui_energia_kwh = pui_mercado_total * (vr_target_mes / vr_total_todos_agentes)
            pui_dinero_cop = pui_energia_kwh * cu

            if rol_pui == "CNIOR":
                egreso_giro_cior = giro_obligatorio_mercado * (vr_target_mes / vr_total_cniors) if vr_total_cniors > 0 else 0.0
                recaudo_real_agente = recaudo_real_mercado * (vr_target_mes / vr_total_cniors) if vr_total_cniors > 0 else 0.0
                flujo_neto_caja = recaudo_real_agente - egreso_giro_cior
                sobrecosto = egreso_giro_cior - recaudo_real_agente
                pct_perdida = ((egreso_giro_cior - recaudo_real_agente) / egreso_giro_cior * 100.0) if egreso_giro_cior > 0 else 0.0
                ingresos_pui = pui_energia_kwh
            else:
                egreso_giro_cior = 0.0
                recaudo_real_agente = 0.0
                total_giros_recibidos = giro_obligatorio_mercado * 0.95
                flujo_neto_caja = pui_energia_kwh + total_giros_recibidos
                sobrecosto = 0.0
                pct_perdida = 0.0
                ingresos_pui = pui_energia_kwh + total_giros_recibidos

            vr_agente_mercado_kwh = round(vr_target_mes / len(MERCADOS), 2)
            energia_contratos_kwh = round(vr_agente_mercado_kwh * pct_contratos, 2)
            energia_bolsa_kwh = round(vr_agente_mercado_kwh * pct_bolsa, 2)

            rows.append({
                "agente_code": agente_target,
                "agente_name": agente_name,
                "rol_pui": rol_pui,
                "mercado_code": m_code,
                "mercado_name": m_name,
                "mes": mes,
                "tipo_registro": "HISTORICO",
                "es_pronostico": False,
                "vr_agente_kwh": vr_agente_mercado_kwh,
                "energia_contratos_kwh": energia_contratos_kwh,
                "energia_bolsa_kwh": energia_bolsa_kwh,
                "pct_cobertura_contratos": round(pct_contratos * 100.0, 2),
                "pct_exposicion_bolsa": round(pct_bolsa * 100.0, 2),
                "modo_cobertura": "calculo_mock",
                "estado_cobertura": f"Cubierta ({pct_contratos*100:.1f}% Contratos / {pct_bolsa*100:.1f}% Bolsa)",
                "dias_activos_mes": 30,
                "promedio_diario_kwh": round(vr_agente_mercado_kwh / 30.0, 2),
                "precio_prom_contratos_cop_kwh": cu,
                "vr_mercado_kwh": round(vr_mercado_kwh, 2),
                "vr_total_todos_agentes_kwh": round(vr_total_todos_agentes, 2),
                "vr_total_cniors_kwh": round(vr_total_cniors, 2),
                "participacion_ettc_pct_total": round(part_total_pct, 4),
                "participacion_ettc_pct_cniors": round(part_cnior_pct, 4),
                "ranking_vr_mes": 12 if rol_pui == "CNIOR" else 1,
                "vr_mercado_m1_kwh": round(vr_m1, 2),
                "vpui_mercado_m1_kwh": round(vpui_m1, 2),
                "cu_m1_cop_kwh": cu_m1,
                "vr_mercado_m2_kwh": round(vr_m2, 2),
                "vpui_actual_kwh": round(vpui_actual, 2),
                "crpui_unitario": round(crpui_unitario, 8),
                "cfpui_unitario": round(cfpui_unitario, 8),
                "pui_mercado_total": round(pui_mercado_total, 2),
                "giro_obligatorio_mercado": round(giro_obligatorio_mercado, 2),
                "recaudo_real_mercado": round(recaudo_real_mercado, 2),
                "pui_energia_kwh": round(pui_energia_kwh, 2),
                "pui_dinero_cop": round(pui_dinero_cop, 2),
                "ingresos_pui_facturado": round(ingresos_pui, 2),
                "egreso_giro_cior": round(egreso_giro_cior, 2),
                "recaudo_real_agente": round(recaudo_real_agente, 2),
                "flujo_neto_caja_pui": round(flujo_neto_caja, 2),
                "sobrecosto_pui": round(sobrecosto, 2),
                "pct_perdida_incobrabilidad": round(pct_perdida, 2),
                "cior_code": cior_code,
                "cior_name": cior_name,
                "cior_vr_total_historial": 28794000000.0,
                "total_giros_recibidos_cior": round(giro_obligatorio_mercado, 2) if rol_pui == "CIOR" else 0.0,
                "param_rcpui": params.rcpui,
                "param_pct_areas_especiales": params.pct_areas_especiales,
                "param_factor_recaudo": params.factor_recaudo_cnior,
                "param_cfpui": params.cfpui,
                "param_esquema_competitivo": params.esquema_competitivo
            })

    return rows
