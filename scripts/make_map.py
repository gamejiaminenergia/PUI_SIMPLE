"""
Genera el mapa coroplético de Colombia por departamento como SVG, usando
Plotly + kaleido. La métrica es la DEMANDA COMERCIAL de los CNIOR por
departamento (kWh agregado de todos los agentes en cada mercado), que varía
geográficamente y refleja dónde se concentra la obligación PUI.

Los mercados de comercialización de la simulación se normalizan a departamentos.
Los bloques regionales 'CARIBE MAR/SOL' se distribuyen entre los departamentos de
la costa caribe presentes en el GeoJSON.
"""
import glob
import json
import os
import sys
from collections import defaultdict

import pandas as pd
import plotly.graph_objects as go

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets_svg")
GEO = os.path.join(ROOT, "static", "geo", "colombia.geo.json")
OUTPUT = os.path.join(ROOT, "output")

BLUE = "#013A6F"
ORANGE = "#ED8A22"

CARIBE_DEPTS = [
    "ATLANTICO", "MAGDALENA", "BOLIVAR", "SUCRE",
    "CORDOBA", "CESAR", "LA GUAJIRA",
]


def _normalize_market_to_dept(market: str):
    """Mapea un nombre de mercado de comercialización a un departamento (o 'CARIBE')."""
    m = market.upper().strip()
    direct = {
        "ANTIOQUIA": "ANTIOQUIA", "SANTANDER": "SANTANDER", "TOLIMA": "TOLIMA",
        "NORTE DE SANTANDER": "NORTE DE SANTANDER", "VALLE DEL CAUCA": "VALLE DEL CAUCA",
        "VALLE": "VALLE DEL CAUCA", "META": "META", "CALDAS": "CALDAS",
        "BOYACA": "BOYACA", "HUILA": "HUILA", "NARIÑO": "NARIÑO", "CAUCA": "CAUCA",
        "CASANARE": "CASANARE", "QUINDIO": "QUINDIO", "CAQUETA": "CAQUETA",
        "ARAUCA": "ARAUCA", "CHOCO": "CHOCO", "GUAVIARE": "GUAVIARE",
        "PUTUMAYO": "PUTUMAYO", "BAJO PUTUMAYO": "PUTUMAYO",
        "BOGOTA": "CUNDINAMARCA", "CUNDINAMARCA": "CUNDINAMARCA",
        "BOGOTA - CUNDINAMARCA": "CUNDINAMARCA",
        "CALI - YUMBO - PUERTO TEJADA": "VALLE DEL CAUCA",
        "TULUA": "VALLE DEL CAUCA", "CARTAGO": "VALLE DEL CAUCA",
        "VALLE DEL SIBUNDOY": "VALLE DEL CAUCA",
        "PEREIRA": "RISARALDA",
        "RUITOQUE": "SANTANDER",
        "POPAYAN - PURACE": "CAUCA",
        "CARIBE MAR": "CARIBE", "CARIBE SOL": "CARIBE",
        "CARIBE_MAR": "CARIBE", "CARIBE_SOL": "CARIBE",
    }
    return direct.get(m, None)


def build_dept_data():
    """Agrega demanda comercial de CNIOR por departamento desde los datasets reales."""
    mkt_dem = defaultdict(float)
    for f in glob.glob(os.path.join(OUTPUT, "*", "pui_dataset_unificado.csv")):
        df = pd.read_csv(f)
        if "Código Mercado Comercialización" not in df.columns:
            continue
        col = "Demanda Comercial Agente (VR - DemaComeReg) [kWh]"
        if col not in df.columns:
            continue
        for _, r in df.iterrows():
            m = str(r.get("Código Mercado Comercialización", "")).strip()
            mkt_dem[m] += float(r.get(col, 0) or 0)

    by_dept = defaultdict(float)
    caribe = 0.0
    for market, v in mkt_dem.items():
        d = _normalize_market_to_dept(market)
        if d is None:
            continue
        if d == "CARIBE":
            caribe += v
        else:
            by_dept[d] += v

    # Distribuir el bloque Caribe entre los departamentos de la costa (equitativo)
    if caribe > 0 and CARIBE_DEPTS:
        share = caribe / len(CARIBE_DEPTS)
        for d in CARIBE_DEPTS:
            by_dept[d] += share
    return by_dept


def _dept_display(name: str) -> str:
    """Capitaliza nombres de departamento en español correcto (Valle del Cauca)."""
    menores = {"del", "de", "la", "las", "los", "y", "e", "san", "santa", "san andres"}
    words = name.lower().split()
    out = []
    for i, w in enumerate(words):
        if w in menores and i > 0:
            out.append(w)
        else:
            out.append(w.capitalize())
    return " ".join(out)


def build_dept_table():
    """Lista ordenada de departamentos con demanda CNIOR (GWh) y % para la tabla."""
    dept_data = build_dept_data()
    total = sum(dept_data.values())
    rows = []
    for d, v in dept_data.items():
        rows.append({
            "dept": _dept_display(d),
            "gwh": v / 1e9,
            "pct": (v / total * 100) if total else 0.0,
        })
    rows.sort(key=lambda r: r["gwh"], reverse=True)
    return rows


def generate_map():
    with open(GEO, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    dept_data = build_dept_data()

    names = []
    values = []
    for feat in geojson["features"]:
        dname = feat["properties"]["NOMBRE_DPT"]
        names.append(dname)
        values.append(round(dept_data.get(dname, 0.0) / 1e9, 2))  # en GWh

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=names,
        z=values,
        featureidkey="properties.NOMBRE_DPT",
        colorscale=[
            [0.0, "#EEF3F8"],
            [0.4, "#9BB8D4"],
            [0.7, "#4C7BA8"],
            [1.0, BLUE],
        ],
        colorbar=dict(title="Demanda CNIOR<br>(GWh)", thickness=15, len=0.7),
        marker_line_color="white",
        marker_line_width=0.6,
        text=[f"{n}: {v:.2f} GWh" for n, v in zip(names, values)],
        hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        title={"text": "Demanda comercial de los CNIOR por departamento (GWh) — concentración de la obligación PUI",
               "x": 0.02, "xanchor": "left", "font": {"color": BLUE, "size": 13}},
        height=560,
        margin=dict(l=8, r=8, t=48, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Arial, sans-serif", "size": 10},
        geo=dict(scope="south america", showframe=False, showcoastlines=True,
                 coastlinecolor="#AAAAAA", projection_type="mercator"),
    )
    os.makedirs(ASSETS, exist_ok=True)
    out = os.path.join(ASSETS, "mapa_colombia.svg")
    fig.write_image(out, format="svg")
    return out


if __name__ == "__main__":
    print(generate_map())
