#!/usr/bin/env python3
"""
Genera los PDFs de presentación PUI por agente (anexos) en pdf/anexo/.

Flujo por agente:
  1. Carga output/<SIGLA>/kpis.json.
  2. Genera las 6 gráficas SVG (Plotly + kaleido) en pdf/anexo/_svg/<SIGLA>/.
  3. Renderiza templates/report_presentacion_template.html (una sola página
     apaisada, branding ACCE) y escribe el PDF con WeasyPrint.

Las gráficas quedan como vectores SVG dentro del PDF (no se rasterizan).
"""
import argparse
import json
import os
import shutil
import sys

import jinja2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.pui_parameters import PUIParameters  # noqa: E402
from scripts.make_anexo_charts import generate_for, load_kpis  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(ROOT, "templates")
ANEXO_SVG = os.path.join(ROOT, "pdf", "anexo", "_svg")


def build_params(cfg: dict, agente: str) -> PUIParameters:
    pui = cfg.get("pui_params", {})
    return PUIParameters(
        rcpui=float(pui.get("rcpui", 0.03)),
        pct_areas_especiales=float(pui.get("pct_areas_especiales", 0.10)),
        factor_recaudo_cnior=float(pui.get("factor_recaudo_cnior", 0.92)),
        cfpui=float(pui.get("cfpui", 0.025)),
        esquema_competitivo=bool(pui.get("esquema_competitivo", False)),
        pct_cobertura_contratos=float(pui.get("pct_cobertura_contratos", 0.85)),
        derive_cobertura_desde_datos=bool(pui.get("derive_cobertura_desde_datos", True)),
        fecha_inicio=str(cfg.get("train_start_date", "2024-01-01")),
        fecha_fin=str(cfg.get("prediction_end_date", "2027-02-28")),
        agente_objetivo=agente,
        agentes_benchmark=list(cfg.get("agents", []))
    )


def render_html(kpis: dict, params: PUIParameters, charts: dict) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES))
    tpl = env.get_template("report_presentacion_template.html")
    return tpl.render(
        kpis=kpis,
        params=params,
        charts=charts,
        logo_header=os.path.join(ROOT, "static", "img", "logo_header.png"),
    )


def weasyprint_to_pdf(html: str, pdf_path: str) -> bool:
    from weasyprint import HTML
    HTML(string=html, base_url=ROOT).write_pdf(pdf_path)
    return os.path.isfile(pdf_path) and os.path.getsize(pdf_path) > 0


def main():
    ap = argparse.ArgumentParser(description="Genera PDFs de presentación PUI por agente en pdf/anexo/")
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "params.yaml"))
    ap.add_argument("--output_dir", default=os.path.join(ROOT, "output"))
    ap.add_argument("--dest", default=os.path.join(ROOT, "pdf", "anexo"))
    ap.add_argument("--agente", default=None, help="Solo un agente (SIGLA). Default: todos con kpis.json")
    ap.add_argument("--keep-html", action="store_true", help="Conservar el HTML renderizado en _tmp_html")
    args = ap.parse_args()

    import yaml
    with open(args.config, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    os.makedirs(args.dest, exist_ok=True)
    tmpdir = os.path.join(args.dest, "_tmp_html")
    os.makedirs(tmpdir, exist_ok=True)

    agentes = []
    if args.agente:
        agentes = [args.agente]
    else:
        for entry in sorted(os.listdir(args.output_dir)):
            if os.path.isfile(os.path.join(args.output_dir, entry, "kpis.json")):
                agentes.append(entry)
    if not agentes:
        print("No se encontraron agentes con kpis.json en", args.output_dir, file=sys.stderr)
        sys.exit(1)

    ok = 0
    errors = []
    for agente in agentes:
        kpis = load_kpis(agente, args.output_dir)
        params = build_params(cfg, agente)
        charts = generate_for(agente, kpis)
        html = render_html(kpis, params, charts)

        html_path = os.path.join(tmpdir, f"{agente}.html")
        with open(html_path, "w", encoding="utf-8") as hf:
            hf.write(html)

        pdf_path = os.path.join(args.dest, f"informe_pui_{agente}.pdf")
        print(f"Generando presentación de {agente} ...")
        try:
            weasyprint_to_pdf(html, pdf_path)
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f"  ✓ {pdf_path} ({size_kb:.0f} KB)")
            ok += 1
        except Exception as e:
            print(f"  ✗ Falló la conversión de {agente}: {e}", file=sys.stderr)
            errors.append(agente)

    if not args.keep_html:
        shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\nCompletado: {ok}/{len(agentes)} PDFs en {args.dest}")
    if errors:
        print("Con errores:", ", ".join(errors), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()