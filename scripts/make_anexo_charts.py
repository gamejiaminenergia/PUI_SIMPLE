"""
Genera las gráficas SVG (Plotly + kaleido) para los PDFs de presentación por
agente (anexos). Reutiliza la paleta de marca ACCE y el enfoque del informe
principal: SVGs vectoriales embebidos con WeasyPrint (sin PNG rasterizados).

Salida: pdf/anexo/_svg/<SIGLA>/<grafica>.svg
"""
import json
import os
import sys

import plotly.graph_objects as go

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- Paleta ACCE ----
BLUE = "#013A6F"
ORANGE = "#ED8A22"
TEAL = "#0D9488"
GREEN = "#2E7D32"
RED = "#C62828"
PURPLE = "#6D5BAE"
DARK = "#1F2A33"
GRID = "#D9D9D6"

ANEXO_SVG = os.path.join(ROOT, "pdf", "anexo", "_svg")


def _mes_es(mes):
    """'2024-03-01' -> 'mar-24'."""
    meses = ["ene", "feb", "mar", "abr", "may", "jun",
             "jul", "ago", "sep", "oct", "nov", "dic"]
    try:
        return f"{meses[int(mes[5:7]) - 1]}-{mes[2:4]}"
    except (ValueError, IndexError):
        return str(mes)[:7]


def _base_layout(fig, title=None, height=250, width=700, font_size=10, showlegend=False, bg="rgba(0,0,0,0)"):
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left",
               "font": {"color": BLUE, "size": 11}},
        height=height,
        width=width,
        margin=dict(l=8, r=8, t=26 if title else 6, b=6),
        paper_bgcolor=bg,
        plot_bgcolor="white",
        font={"family": "Inter, Arial, sans-serif", "color": DARK, "size": font_size},
        showlegend=showlegend,
        legend={"orientation": "h", "y": 1.06, "x": 1, "xanchor": "right",
                "font": {"size": 9}},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(size=9))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(size=9))
    return fig


def _write(fig, sigla, name):
    d = os.path.join(ANEXO_SVG, sigla)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, name)
    fig.write_image(path, format="svg")
    return path


# Dimensiones SVG (px) por tipo de gráfica, calculadas para que al escalarlas
# al ancho de su celda llenen el alto disponible SIN desbordar (evita traslapes):
#   top   : celda 130mm ancho x ~83mm imagen  -> aspect 0.63  -> 900x565
#   bench : celda 255mm ancho x ~99mm imagen  -> aspect 0.39  -> 900x350
#   side  : celda 137mm ancho x ~45mm imagen  -> aspect 0.33  -> 900x295
SIZE_TOP = (900, 565)
SIZE_BENCH = (900, 350)
SIZE_SIDE = (900, 295)


def _tendencia(kpis):
    return kpis.get("tendencia_mensual", [])


def _labels(t):
    return [_mes_es(r["mes"]) for r in t]


def grafica_cobertura(sigla, kpis):
    """Contratos (azul) + bolsa (naranja) apiladas + línea VR (teal)."""
    t = _tendencia(kpis)
    labels = _labels(t)
    contratos = [r.get("energia_contratos_kwh", 0) / 1e9 for r in t]
    bolsa = [r.get("energia_bolsa_kwh", 0) / 1e9 for r in t]
    vr = [r.get("vr_agente_kwh", 0) / 1e9 for r in t]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=contratos, name="Contratos", marker_color=BLUE))
    fig.add_trace(go.Bar(x=labels, y=bolsa, name="Bolsa spot", marker_color=ORANGE))
    fig.add_trace(go.Scatter(x=labels, y=vr, name="VR total", mode="lines",
                             line=dict(color=TEAL, width=2)))
    fig = _base_layout(fig, title="Cobertura de demanda — Contratos vs Bolsa [GWh]",
                       width=SIZE_TOP[0], height=SIZE_TOP[1], showlegend=True)
    fig.update_yaxes(title="GWh")
    fig.update_xaxes(type="category", nticks=12)
    return _write(fig, sigla, "cobertura.svg")


def grafica_precios(sigla, kpis):
    """CU (teal), CRPUI (morado), CFPUI (naranja) en COP/kWh."""
    t = _tendencia(kpis)
    labels = _labels(t)
    cu = [r.get("cu_cop_kwh", 0) or 0 for r in t]
    crpui = [r.get("crpui_unitario", 0) or 0 for r in t]
    cfpui = [r.get("cfpui_unitario", 0) or 0 for r in t]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=cu, name="CU (Contratos)", mode="lines",
                             line=dict(color=TEAL, width=2)))
    fig.add_trace(go.Scatter(x=labels, y=crpui, name="CRPUI", mode="lines",
                             line=dict(color=PURPLE, width=1.5, dash="dash")))
    fig.add_trace(go.Scatter(x=labels, y=cfpui, name="CFPUI", mode="lines",
                             line=dict(color=ORANGE, width=1.5, dash="dot")))
    fig = _base_layout(fig, title="Precios de contratos (CU) y cargos PUI [COP/kWh]",
                       width=SIZE_TOP[0], height=SIZE_TOP[1], showlegend=True)
    fig.update_yaxes(title="COP/kWh")
    fig.update_xaxes(type="category", nticks=12)
    return _write(fig, sigla, "precios.svg")


def grafica_pui_cashflow(sigla, kpis):
    """Asignación PUI (barras) + egreso CIOR (rojo) y recaudo (verde) en MM COP."""
    t = _tendencia(kpis)
    labels = _labels(t)
    pui = [r.get("pui_energia_kwh", 0) or 0 for r in t]
    egreso = [r.get("egreso_cop", 0) or 0 for r in t]
    recaudo = [r.get("recaudo_cop", 0) or 0 for r in t]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=pui, name="Asignación PUI [kWh]",
                         marker_color=PURPLE, opacity=0.55, yaxis="y1"))
    fig.add_trace(go.Scatter(x=labels, y=[v / 1e6 for v in egreso], name="Egreso CIOR",
                             mode="lines", line=dict(color=RED, width=2), yaxis="y2"))
    fig.add_trace(go.Scatter(x=labels, y=[v / 1e6 for v in recaudo], name="Recaudo efectivo",
                             mode="lines", line=dict(color=GREEN, width=2), yaxis="y2"))
    fig = _base_layout(fig, title="Asignación PUI, giros al CIOR vs recaudo",
                       width=SIZE_TOP[0], height=SIZE_TOP[1], showlegend=True)
    fig.update_yaxes(title="kWh", gridcolor=GRID)
    fig.update_yaxes(title="MM COP", gridcolor=GRID, overlaying="y", side="right")
    fig.update_xaxes(type="category", nticks=12)
    return _write(fig, sigla, "pui_cashflow.svg")


def grafica_rendimiento(sigla, kpis):
    """CU (teal), sobrecosto (rojo) y recaudo (verde)."""
    t = _tendencia(kpis)
    labels = _labels(t)
    cu = [r.get("cu_cop_kwh", 0) or 0 for r in t]
    sobrecosto = [r.get("sobrecosto_cop", 0) or 0 for r in t]
    recaudo = [r.get("recaudo_cop", 0) or 0 for r in t]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=cu, name="CU m-1 [COP/kWh]", mode="lines",
                             line=dict(color=TEAL, width=2), yaxis="y1"))
    fig.add_trace(go.Scatter(x=labels, y=[v / 1e6 for v in sobrecosto], name="Sobrecosto",
                             mode="lines", line=dict(color=RED, width=2, dash="dash"), yaxis="y2"))
    fig.add_trace(go.Scatter(x=labels, y=[v / 1e6 for v in recaudo], name="Recaudo efectivo",
                             mode="lines", line=dict(color=GREEN, width=2, dash="dot"), yaxis="y2"))
    fig = _base_layout(fig, title="Rendimiento financiero — costos, sobrecosto y recaudo",
                       width=SIZE_SIDE[0], height=SIZE_SIDE[1], showlegend=True)
    fig.update_yaxes(title="COP/kWh", gridcolor=GRID)
    fig.update_yaxes(title="MM COP", gridcolor=GRID, overlaying="y", side="right")
    fig.update_xaxes(type="category", nticks=12)
    return _write(fig, sigla, "rendimiento.svg")


def grafica_benchmark(sigla, kpis):
    """Sobrecosto por agente del mercado (barras, agente actual en naranja)."""
    agents = kpis.get("top_agentes_sobrecosto", [])
    labels = [a["code"] for a in agents]
    vals = [a.get("sobrecosto", 0) or 0 for a in agents]
    colors = [ORANGE if a.get("es_actual") else BLUE for a in agents]

    fig = go.Figure(go.Bar(x=labels, y=[v / 1e6 for v in vals], marker_color=colors,
                           marker_line_width=0))
    fig = _base_layout(fig, title="Benchmark de sobrecosto por agente [MM COP]",
                       width=SIZE_BENCH[0], height=SIZE_BENCH[1])
    fig.update_yaxes(title="MM COP")
    fig.update_xaxes(type="category", tickangle=90, tickfont=dict(size=8),
                     tickmode="array", tickvals=labels, ticktext=labels, automargin=True)
    return _write(fig, sigla, "benchmark.svg")


def grafica_cobertura_demanda(sigla, kpis):
    """Contratos (azul) y bolsa (naranja) + línea VR total (teal). Distinta a cobertura."""
    t = _tendencia(kpis)
    labels = _labels(t)
    contratos = [r.get("energia_contratos_kwh", 0) / 1e9 for r in t]
    bolsa = [r.get("energia_bolsa_kwh", 0) / 1e9 for r in t]
    vr = [r.get("vr_agente_kwh", 0) / 1e9 for r in t]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=contratos, name="Contratos", marker_color=BLUE, opacity=0.8))
    fig.add_trace(go.Bar(x=labels, y=bolsa, name="Bolsa spot", marker_color=ORANGE, opacity=0.8))
    fig.add_trace(go.Scatter(x=labels, y=vr, name="VR total", mode="lines+markers",
                             line=dict(color=TEAL, width=2)))
    fig = _base_layout(fig, title="Cobertura y demanda — Contratos vs Bolsa vs VR [GWh]",
                       width=SIZE_SIDE[0], height=SIZE_SIDE[1], showlegend=True)
    fig.update_yaxes(title="GWh")
    fig.update_xaxes(type="category", nticks=12)
    return _write(fig, sigla, "cobertura_demanda.svg")


def generate_for(sigla: str, kpis: dict) -> dict:
    """Genera las 6 gráficas SVG de un agente. Devuelve rutas."""
    return {
        "cobertura": grafica_cobertura(sigla, kpis),
        "precios": grafica_precios(sigla, kpis),
        "pui_cashflow": grafica_pui_cashflow(sigla, kpis),
        "rendimiento": grafica_rendimiento(sigla, kpis),
        "cobertura_demanda": grafica_cobertura_demanda(sigla, kpis),
        "benchmark": grafica_benchmark(sigla, kpis),
    }


def load_kpis(sigla: str, output_dir: str = None) -> dict:
    output_dir = output_dir or os.path.join(ROOT, "output")
    with open(os.path.join(output_dir, sigla, "kpis.json"), "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    siglas = sys.argv[1:] or [d for d in sorted(os.listdir(os.path.join(ROOT, "output")))
                              if os.path.isfile(os.path.join(ROOT, "output", d, "kpis.json"))]
    for s in siglas:
        k = load_kpis(s)
        paths = generate_for(s, k)
        print(f"{s}: " + ", ".join(os.path.basename(p) for p in paths.values()))