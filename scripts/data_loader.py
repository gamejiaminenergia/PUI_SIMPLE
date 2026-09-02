"""
Carga y agregación de los KPIs calculados por la simulación (output/<SIGLA>/kpis.json).

Replica EXACTAMENTE la lógica de agregación de
controllers/executive_summary.py:111-123 para que los números del PDF
coincidan con el resumen ejecutivo generado.
"""
import glob
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.acce import es_asociado_acce


def _safe(k: Dict[str, Any], key: str, default: float = 0.0) -> float:
    v = k.get(key, default)
    return v if v is not None else default


def load_all_agents(output_dir: str = "output") -> List[Dict[str, Any]]:
    """Carga todos los kpis.json de output/<SIGLA>/ como una lista de agentes."""
    agents = []
    for kp in sorted(glob.glob(os.path.join(output_dir, "*", "kpis.json"))):
        sigla = os.path.basename(os.path.dirname(kp))
        with open(kp, "r", encoding="utf-8") as f:
            agents.append({"agente": sigla, "kpis": json.load(f)})
    return agents


def aggregate_market(agents: List[Dict[str, Any]]) -> Dict[str, float]:
    """Totales globales de mercado (misma lógica que executive_summary.py)."""
    tot_demanda = sum(_safe(a["kpis"], "total_pui_kwh", 0) for a in agents)
    tot_pui_kwh = sum(_safe(a["kpis"], "total_pui_kwh_energia", 0) for a in agents)
    tot_pui_cop = sum(_safe(a["kpis"], "total_pui_cop", 0) for a in agents)
    tot_egreso = sum(_safe(a["kpis"], "total_egreso_giro_cop", 0) for a in agents)
    tot_recaudo = sum(_safe(a["kpis"], "total_recaudo_cop", 0) for a in agents)
    tot_sobrecosto = sum(_safe(a["kpis"], "sobrecosto_total_cop", 0) for a in agents)
    tot_flujo = sum(_safe(a["kpis"], "flujo_neto_caja_total_cop", 0) for a in agents)
    tot_contratos = sum(_safe(a["kpis"], "total_energia_contratos_kwh", 0) for a in agents)
    tot_bolsa = sum(_safe(a["kpis"], "total_energia_bolsa_kwh", 0) for a in agents)

    pct_cobertura = _percent(tot_contratos, tot_contratos + tot_bolsa)
    gap = tot_egreso - tot_recaudo
    pct_incob = _percent(tot_sobrecosto, tot_egreso) if tot_egreso > 0 else 0.0
    return {
        "n": len(agents),
        "tot_demanda": tot_demanda,
        "tot_pui_kwh": tot_pui_kwh,
        "tot_pui_cop": tot_pui_cop,
        "tot_egreso": tot_egreso,
        "tot_recaudo": tot_recaudo,
        "tot_sobrecosto": tot_sobrecosto,
        "tot_flujo": tot_flujo,
        "tot_contratos": tot_contratos,
        "tot_bolsa": tot_bolsa,
        "pct_cobertura": pct_cobertura,
        "pct_exposicion": 100.0 - pct_cobertura,
        "gap_recaudo": gap,
        "pct_incob": pct_incob,
    }


def _percent(part, total) -> float:
    return (part / total * 100.0) if total else 0.0


def ranking_agentes(agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ranking por sobrecosto absoluto (desc), con marca de asociado ACCE."""
    rows = []
    for a in agents:
        k = a["kpis"]
        rows.append({
            "agente": a["agente"],
            "nombre": k.get("agente_name", ""),
            "rol": k.get("rol_pui", ""),
            "sobrecosto": _safe(k, "sobrecosto_total_cop"),
            "flujo": _safe(k, "flujo_neto_caja_total_cop"),
            "recaudo": _safe(k, "total_recaudo_cop"),
            "pct_perdida": _safe(k, "pct_perdida_promedio"),
            "es_asociado": es_asociado_acce(a["agente"]),
        })
    rows.sort(key=lambda r: r["sobrecosto"], reverse=True)
    return rows


def buckets_perdida(agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Distribución de agentes por rango de pérdida (misma lógica que el resumen)."""
    labels = ["<2%", "2-5%", "5-10%", ">10%"]
    buckets = {l: [] for l in labels}
    for a in agents:
        pct = _safe(a["kpis"], "pct_perdida_promedio", 0)
        if pct < 2:
            buckets["<2%"].append(a["agente"])
        elif pct < 5:
            buckets["2-5%"].append(a["agente"])
        elif pct < 10:
            buckets["5-10%"].append(a["agente"])
        else:
            buckets[">10%"].append(a["agente"])
    return [{"label": l, "count": len(buckets[l]), "agentes": buckets[l]} for l in labels]


def escenarios_competitivos(market: Dict[str, float]) -> List[Dict[str, Any]]:
    """Los 4 escenarios transitorio vs competitivo (misma lógica que executive_summary.py:427-436)."""
    tot_egreso = market["tot_egreso"]
    esc = [
        ("Transitorio hoy (Art. 12)", 0.92),
        ("Competitivo parcial (95%)", 0.95),
        ("Competitivo pleno (97%)", 0.97),
        ("Riesgo 100% remunerado", 1.00),
    ]
    out = []
    for label, fac in esc:
        out.append({
            "label": label,
            "factor": fac,
            "faltante": tot_egreso * (1 - fac),
            "pct": (1 - fac) * 100.0,
        })
    return out


def agregado_temporal(agents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Agrega tendencia_mensual de todos los agentes por mes (histórico + forecast)."""
    by_month: Dict[str, Dict] = {}
    for a in agents:
        for row in a["kpis"].get("tendencia_mensual", []):
            mes = row.get("mes")
            if not mes:
                continue
            b = by_month.setdefault(mes, {
                "mes": mes, "sobrecosto": 0.0, "egreso": 0.0, "recaudo": 0.0,
                "flujo": 0.0, "pronostico": False, "pui_cop": 0.0,
            })
            b["sobrecosto"] += row.get("sobrecosto_cop", 0) or 0
            b["egreso"] += row.get("egreso_cop", 0) or 0
            b["recaudo"] += row.get("recaudo_cop", 0) or 0
            b["flujo"] += row.get("flujo_cop", 0) or 0
            b["pui_cop"] += row.get("pui_cop", 0) or 0
            if row.get("es_pronostico"):
                b["pronostico"] = True
    return sorted(by_month.values(), key=lambda r: r["mes"])


def sobrecosto_por_mercado(agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrega sobrecosto por mercado (para el mapa)."""
    by_mkt: Dict[str, float] = {}
    for a in agents:
        for m in a["kpis"].get("top_mercados_sobrecosto", []):
            code = m.get("code")
            if not code:
                continue
            by_mkt[code] = by_mkt.get(code, 0.0) + m.get("sobrecosto", 0)
    out = [{"mercado": k, "sobrecosto": v} for k, v in by_mkt.items()]
    out.sort(key=lambda r: r["sobrecosto"], reverse=True)
    return out


def acce_vs_noacce(agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compara la pérdida por incobrabilidad entre Asociados ACCE y No asociados."""
    tot = sum(_safe(a["kpis"], "sobrecosto_total_cop") for a in agents)
    groups = {"acce": [], "no_acce": []}
    for a in agents:
        groups["acce" if es_asociado_acce(a["agente"]) else "no_acce"].append(a)

    def _grupo(g: List[Dict[str, Any]]) -> Dict[str, Any]:
        sc = sum(_safe(a["kpis"], "sobrecosto_total_cop") for a in g)
        rec = sum(_safe(a["kpis"], "total_recaudo_cop") for a in g)
        top = max(g, key=lambda a: _safe(a["kpis"], "sobrecosto_total_cop"))
        return {
            "n": len(g),
            "pct_agentes": (len(g) / len(agents) * 100) if agents else 0.0,
            "sobrecosto": sc,
            "pct_sobrecosto": (sc / tot * 100) if tot else 0.0,
            "promedio": (sc / len(g)) if g else 0.0,
            "recaudo": rec,
            "top_agente": top["agente"],
            "top_nombre": top["kpis"].get("agente_name", ""),
            "top_sc": _safe(top["kpis"], "sobrecosto_total_cop"),
        }

    return {
        "total": tot,
        "acce": _grupo(groups["acce"]),
        "no_acce": _grupo(groups["no_acce"]),
    }
