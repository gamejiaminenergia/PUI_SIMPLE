"""
Genera el informe PDF institucional para ACCE sobre el PUI.

Flujo:
  1. Carga los 61 kpis.json de output/ y recalcula los agregados de mercado
     con la MISMA lógica que controllers/executive_summary.py (coherencia
     total con docs/resumen_ejecutivo_pui.md).
  2. Genera las gráficas SVG (Plotly + kaleido) y el mapa de Colombia.
  3. Renderiza templates/report_pui_acce.html.jinja2 con Jinja2.
  4. Escribe el PDF con WeasyPrint.

Uso:
  python scripts/build_pdf.py
"""
import argparse
import os
import sys
from datetime import datetime

import jinja2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_loader import (
    acce_vs_noacce,
    agregado_temporal,
    aggregate_market,
    buckets_perdida,
    escenarios_competitivos,
    load_all_agents,
    ranking_agentes,
)
from scripts.make_charts import generate_all as generate_charts
from scripts.make_map import build_dept_table, generate_map

from config.acce import (
    ACCE_FULL_NAME,
    RESOLUCION_PUI,
    ARTICULO_11,
    ARTICULO_12,
)
from controllers.executive_summary import _fmt_cop, _fmt_kwh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "static")
ASSETS = os.path.join(ROOT, "assets_svg")
TEMPLATES = os.path.join(ROOT, "templates")
CSS_PATH = os.path.join(STATIC, "css", "report_acce.css")

# ---- Paleta ACCE (hex reales del logo) ----
BLUE = "#013A6F"
ORANGE = "#ED8A22"


def _fecha_es():
    """Fecha en español (strftime usa locale inglés por defecto)."""
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    now = datetime.now()
    return f"{now.day:02d} de {meses[now.month - 1]} de {now.year}"


def _build_context(agents):
    market = aggregate_market(agents)
    ranking = ranking_agentes(agents)
    buckets = buckets_perdida(agents)
    escenarios = escenarios_competitivos(market)
    temporal = agregado_temporal(agents)

    n_acce = sum(1 for r in ranking if r["es_asociado"])
    top1 = ranking[0] if ranking else None
    top1_share = (top1["sobrecosto"] / market["tot_sobrecosto"] * 100) if market["tot_sobrecosto"] else 0

    n_hist = sum(1 for a in agents if a["kpis"].get("total_registros_forecast", 0) <= 0)
    n_fcst = len(agents) - n_hist

    all_agents_alpha = sorted(a["agente"] for a in agents)
    dept_table = build_dept_table()
    tot_gwh = sum(r["gwh"] for r in dept_table)

    # Tabla de la trayectoria temporal: misma ventana que la gráfica (desde
    # 3 meses antes del inicio del PUI), con valores formateados como el resumen.
    temporal_rows = []
    first_fc = next((i for i, r in enumerate(temporal) if r["pronostico"]), 0)
    window = temporal[max(0, first_fc - 3):]
    meses_full = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    for r in window:
        m = int(r["mes"][5:7])
        temporal_rows.append({
            "mes": f"{meses_full[m - 1]} {r['mes'][:4]}",
            "tipo": "Pronóstico" if r["pronostico"] else "Histórico",
            "pui": "PUI activo" if r["pronostico"] else "—",
            "egreso": _fmt_cop(r["egreso"]),
            "recaudo": _fmt_cop(r["recaudo"]),
            "sobrecosto": _fmt_cop(r["sobrecosto"]),
            "flujo": _fmt_cop(r["flujo"]),
        })

    # Distribución de la pérdida: Asociados ACCE vs No asociados
    an = acce_vs_noacce(agents)
    acce_noacce = {
        "total": _fmt_cop(an["total"]),
        "acce": {
            "n": an["acce"]["n"],
            "pct_agentes": an["acce"]["pct_agentes"],
            "sobrecosto": _fmt_cop(an["acce"]["sobrecosto"]),
            "pct_sobrecosto": an["acce"]["pct_sobrecosto"],
            "promedio": _fmt_cop(an["acce"]["promedio"]),
            "recaudo": _fmt_cop(an["acce"]["recaudo"]),
            "top_agente": an["acce"]["top_agente"],
            "top_nombre": an["acce"]["top_nombre"],
            "top_sc": _fmt_cop(an["acce"]["top_sc"]),
        },
        "no_acce": {
            "n": an["no_acce"]["n"],
            "pct_agentes": an["no_acce"]["pct_agentes"],
            "sobrecosto": _fmt_cop(an["no_acce"]["sobrecosto"]),
            "pct_sobrecosto": an["no_acce"]["pct_sobrecosto"],
            "promedio": _fmt_cop(an["no_acce"]["promedio"]),
            "recaudo": _fmt_cop(an["no_acce"]["recaudo"]),
            "top_agente": an["no_acce"]["top_agente"],
            "top_nombre": an["no_acce"]["top_nombre"],
            "top_sc": _fmt_cop(an["no_acce"]["top_sc"]),
        },
    }

    return {
        "meta": {
            "fecha": _fecha_es(),
            "fecha_corta": datetime.now().strftime("%Y-%m-%d"),
            "resolucion": RESOLUCION_PUI,
            "articulo_11": ARTICULO_11,
            "articulo_12": ARTICULO_12,
            "acce": ACCE_FULL_NAME,
        },
        "market": {
            "n": market["n"],
            "n_acce": n_acce,
            "tot_pui_cop": _fmt_cop(market["tot_pui_cop"]),
            "tot_egreso": _fmt_cop(market["tot_egreso"]),
            "tot_recaudo": _fmt_cop(market["tot_recaudo"]),
            "tot_sobrecosto": _fmt_cop(market["tot_sobrecosto"]),
            "gap": _fmt_cop(market["gap_recaudo"]),
            "pct_incob": market["pct_incob"],
            "tot_contratos": _fmt_kwh(market["tot_contratos"]),
            "tot_bolsa": _fmt_kwh(market["tot_bolsa"]),
            "pct_cobertura": market["pct_cobertura"],
            "pct_exposicion": market["pct_exposicion"],
            "flujo": _fmt_cop(market["tot_flujo"]),
        },
        "ranking": ranking,
        "top1": {
            "agente": top1["agente"] if top1 else "",
            "nombre": top1["nombre"] if top1 else "",
            "share": top1_share,
        } if top1 else None,
        "buckets": buckets,
        "escenarios": escenarios,
        "temporal": temporal,
        "cobertura_temporal": {"hist": n_hist, "fcst": n_fcst},
        "dept_table": dept_table,
        "dept_total_gwh": tot_gwh,
        "temporal_rows": temporal_rows,
        "acce_noacce": acce_noacce,
        "all_agents": all_agents_alpha,
        "assets": {
            "impacto_global": os.path.join(ASSETS, "impacto_global.svg"),
            "cobertura": os.path.join(ASSETS, "cobertura_demanda.svg"),
            "ranking": os.path.join(ASSETS, "ranking_top.svg"),
            "temporal": os.path.join(ASSETS, "trayectoria_temporal.svg"),
            "escenarios": os.path.join(ASSETS, "escenarios.svg"),
            "acce_noacce": os.path.join(ASSETS, "acce_noacce.svg"),
            "mapa": os.path.join(ASSETS, "mapa_colombia.svg"),
            "logo": os.path.join(STATIC, "img", "logo.png"),
        },
    }


def _render_html(ctx):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES),
        autoescape=True,
    )
    env.filters["fmt_cop"] = _fmt_cop
    template = env.get_template("report_pui_acce.html.jinja2")
    return template.render(**ctx)


def build_pdf(out_path, regenerate_assets=True):
    agents = load_all_agents()
    if not agents:
        raise SystemExit("No se encontraron kpis.json en output/")

    if regenerate_assets:
        print("Generando gráficas SVG...")
        generate_charts()
        print("Generando mapa...")
        generate_map()

    ctx = _build_context(agents)
    html = _render_html(ctx)

    from weasyprint import HTML
    HTML(string=html, base_url=ROOT).write_pdf(out_path, stylesheets=[CSS_PATH])
    print(f"PDF generado: {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera informe PDF PUI para ACCE")
    ap.add_argument("--out", default=os.path.join(ROOT, "pdf", "informe", "informe_pui_acce.pdf"))
    ap.add_argument("--no-assets", action="store_true", help="No regenerar SVGs")
    args = ap.parse_args()
    build_pdf(args.out, regenerate_assets=not args.no_assets)
