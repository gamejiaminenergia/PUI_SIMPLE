"""
Vista HTML Interactivas para Informes PUI.
"""
import os
import json
from typing import List, Dict, Any
from views.base_view import BaseReportView
from models.pui_parameters import PUIParameters

class HTMLReportView(BaseReportView):
    """Genera un informe Web/HTML estilizado y ejecutivo con gráficos interactivos Chart.js."""

    def __init__(self, template_path: str = "templates/report_template.html"):
        self.template_path = template_path

    def render(self, data: List[Dict[str, Any]], kpis: Dict[str, Any], params: PUIParameters, output_path: str = None) -> str:
        if not output_path:
            output_path = f"pui_report_{params.agente_objetivo}.html"

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"No se encontró la plantilla HTML en: {self.template_path}")

        kpis_json = json.dumps(kpis, default=str)

        try:
            from jinja2 import Template
            with open(self.template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            template = Template(template_content)
            rendered_html = template.render(data=data, kpis=kpis, kpis_json=kpis_json, params=params)
        except ImportError:
            rendered_html = self._render_fallback(kpis, params)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        print(f"[HTML View] Reporte HTML interactivo generado en: {output_path}")
        return output_path

    def _render_fallback(self, kpis: Dict[str, Any], params: PUIParameters) -> str:
        """Renderizado alternativo básico en HTML sin jinja2."""
        return f"""<!DOCTYPE html>
<html>
<head><title>Informe PUI - {kpis['agente_code']}</title></head>
<body style="font-family:sans-serif; background:#0a0e17; color:#fff; padding:2rem;">
<h1>Informe PUI - {kpis['agente_code']} ({kpis['agente_name']})</h1>
<p>Rol: {kpis['rol_pui']} | CIOR: {kpis['cior_name']}</p>
<h2>Resumen Financiero</h2>
<ul>
  <li>PUI Energía: {kpis['total_pui_kwh']:,.2f} kWh</li>
  <li>PUI COP: ${kpis['total_pui_cop']:,.2f} COP</li>
  <li>Flujo Neto: ${kpis['flujo_neto_caja_total_cop']:,.2f} COP</li>
  <li>Sobrecosto: ${kpis['sobrecosto_total_cop']:,.2f} COP ({kpis['pct_perdida_promedio']:.2f}%)</li>
</ul>
</body>
</html>"""
