"""
Genera las gráficas del informe como SVG con Plotly + kaleido, usando la
paleta de marca ACCE extraída del logo real (docs/logo.png):
  azul institucional  #013A6F
  naranja de marca    #ED8A22
"""
import os
import sys

import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.data_loader import (
    agregado_temporal,
    aggregate_market,
    buckets_perdida,
    escenarios_competitivos,
    load_all_agents,
    ranking_agentes,
)

# ---- Paleta ACCE (hex extraídos del logo real con PIL) ----
BLUE = "#013A6F"
ORANGE = "#ED8A22"
GRAY = "#F4F4F2"
ALT = "#FBEFE4"
DARK = "#1F2A33"
GREEN = "#2E7D32"
RED = "#C62828"
GRID = "#D9D9D6"

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets_svg")


def _base_layout(fig, title=None, height=340, bg="rgba(0,0,0,0)", font_size=11, showlegend=False):
    fig.update_layout(
        title={"text": title, "x": 0.02, "xanchor": "left", "font": {"color": BLUE, "size": 13}},
        height=height,
        margin=dict(l=8, r=8, t=48 if title else 24, b=8),
        paper_bgcolor=bg,
        plot_bgcolor="white",
        font={"family": "Inter, Arial, sans-serif", "color": DARK, "size": font_size},
        showlegend=showlegend,
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def _write(fig, name):
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    fig.write_image(path, format="svg")
    return path


def _fmt_cop_b(x):
    """Formatea COP en billones (B)."""
    return f"${x/1e12:,.2f} B"


def grafica_impacto_global(market):
    """Barras: giros al CIOR, recaudo efectivo, sobrecosto (agregado)."""
    cats = ["Giros al CIOR", "Recaudo efectivo", "Sobrecosto (faltante)"]
    vals = [market["tot_egreso"], market["tot_recaudo"], market["tot_sobrecosto"]]
    colors = [BLUE, GREEN, RED]
    fig = go.Figure(go.Bar(x=cats, y=[v / 1e12 for v in vals], marker_color=colors,
                           text=[_fmt_cop_b(v) for v in vals], textposition="outside"))
    fig = _base_layout(fig, title="Impacto global del PUI — agregado de mercado (COP)")
    fig.update_yaxes(title="Billones de COP")
    return _write(fig, "impacto_global.svg")


def grafica_cobertura(market):
    """Donut contratos vs bolsa."""
    labels = ["Contratos bilaterales", "Exposición bolsa spot"]
    vals = [market["tot_contratos"], market["tot_bolsa"]]
    colors = [BLUE, ORANGE]
    fig = go.Figure(go.Pie(labels=labels, values=vals, hole=0.55, marker=dict(colors=colors),
                           textinfo="label+percent", textfont={"size": 10}))
    fig = _base_layout(fig, title="Cobertura de demanda — contratos vs bolsa")
    return _write(fig, "cobertura_demanda.svg")


def grafica_ranking(top_n=None):
    """Barra horizontal con el ranking de agentes por sobrecosto (★ Asociado ACCE).
    Incluye TODOS los agentes y fuerza la etiqueta de cada uno (plotly adelgaza
    los ticks del eje Y por defecto, ocultando agentes)."""
    ranking = ranking_agentes(load_all_agents())
    if top_n:
        top = ranking[:top_n][::-1]
    else:
        top = ranking[::-1]  # todos, invertidos para que el mayor quede arriba
    n = len(top)
    labels = [f"{r['agente']}{' ★' if r['es_asociado'] else ''}" for r in top]
    vals = [r["sobrecosto"] / 1e12 for r in top]
    colors = [ORANGE if r["es_asociado"] else BLUE for r in top]
    # etiquetas de valor solo en barras grandes para no saturar las 61
    texts = [f"${v:,.2f} B" if v >= 0.10 else "" for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker_color=colors,
                           text=texts, textposition="outside", cliponaxis=False))
    # altura por agente amplia para que cada etiqueta se lea
    per_bar = 14
    height = max(320, 90 + n * per_bar)
    fig = _base_layout(fig, title=f"Ranking de los {n} agentes por sobrecosto acumulado (★ Asociado ACCE)",
                       height=height, font_size=11)
    # FORZAR la etiqueta de cada agente (evitar el adelgazamiento de ticks de plotly)
    fig.update_yaxes(tickmode="array", tickvals=labels, ticktext=labels,
                     tickfont=dict(size=11), automargin=True)
    fig.update_layout(width=900, height=height,
                      margin=dict(l=10, r=90, t=48, b=8))
    fig.update_xaxes(title="Billones de COP")
    return _write(fig, "ranking_top.svg")


def grafica_temporal():
    """Línea mensual de sobrecosto/flujo (histórico + forecast TimesFM)."""
    ts = agregado_temporal(load_all_agents())
    meses_es = ["ene", "feb", "mar", "abr", "may", "jun",
                "jul", "ago", "sep", "oct", "nov", "dic"]
    mes = []
    for r in ts:
        y, m = r["mes"][:4], int(r["mes"][5:7])
        mes.append(f"{meses_es[m - 1]} {y[2:]}")
    sobre = [r["sobrecosto"] / 1e9 for r in ts]
    flujo = [r["flujo"] / 1e9 for r in ts]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mes, y=sobre, mode="lines+markers", name="Sobrecosto",
                             line=dict(color=RED, width=2)))
    fig.add_trace(go.Scatter(x=mes, y=flujo, mode="lines+markers", name="Flujo neto",
                             line=dict(color=BLUE, width=2, dash="dot")))
    fig = _base_layout(fig, title="Sobrecosto y flujo neto mensual — histórico y pronóstico TimesFM",
                       showlegend=True)
    fig.update_yaxes(title="Miles de millones COP")
    fig.update_xaxes(type="category", tickangle=0, nticks=12)
    return _write(fig, "trayectoria_temporal.svg")


def grafica_escenarios(market):
    """Reducción del faltante según reconocimiento del riesgo de cartera."""
    esc = escenarios_competitivos(market)
    labels = [e["label"] for e in esc]
    falt = [e["faltante"] / 1e12 for e in esc]
    colors = [RED, ORANGE, GREEN, BLUE]
    fig = go.Figure(go.Bar(x=labels, y=falt, marker_color=colors,
                           text=[f"${v:,.2f} B" for v in falt], textposition="outside"))
    fig = _base_layout(fig, title="Faltante de caja por escenario — transitorio vs competitivo")
    fig.update_yaxes(title="Billones de COP")
    return _write(fig, "escenarios.svg")


def grafica_distribucion():
    """Barras por rango de pérdida por incobrabilidad."""
    buckets = buckets_perdida(load_all_agents())
    labels = [b["label"] for b in buckets]
    counts = [b["count"] for b in buckets]
    colors = [BLUE if c else GRAY for c in counts]
    fig = go.Figure(go.Bar(x=labels, y=counts, marker_color=colors,
                           text=counts, textposition="outside"))
    fig = _base_layout(fig, title="Distribución de agentes por rango de pérdida por incobrabilidad")
    fig.update_yaxes(title="N° de agentes")
    return _write(fig, "distribucion.svg")


def generate_all():
    agents = load_all_agents()
    market = aggregate_market(agents)
    paths = {
        "impacto_global": grafica_impacto_global(market),
        "cobertura": grafica_cobertura(market),
        "ranking": grafica_ranking(),
        "temporal": grafica_temporal(),
        "escenarios": grafica_escenarios(market),
        "distribucion": grafica_distribucion(),
    }
    return paths


if __name__ == "__main__":
    print(generate_all())
