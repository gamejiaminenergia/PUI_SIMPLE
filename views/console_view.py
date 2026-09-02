"""
Vista de Consola / Terminal para Informes PUI (Históricos y Pronósticos).
"""
from typing import List, Dict, Any
from views.base_view import BaseReportView
from models.pui_parameters import PUIParameters

class ConsoleReportView(BaseReportView):
    """Renderiza el informe ejecutivo en la terminal con formato ASCII."""

    def render(self, data: List[Dict[str, Any]], kpis: Dict[str, Any], params: PUIParameters, output_path: str = None) -> str:
        if not kpis:
            print("[ConsoleView] WARNING: kpis is None or empty, skipping console render.")
            return "console_skipped_no_kpis"
        es_pronostico = kpis.get("registros_pronosticados", 0) > 0
        titulo_modo = "HISTÓRICO Y PRONÓSTICO (TimesFM)" if es_pronostico else "HISTÓRICO REGULATORIO"

        print("=" * 80)
        print(f"           INFORME EJECUTIVO DE SIMULACIÓN PUI ({titulo_modo})")
        print("=" * 80)
        print(f" Agente Objetivo    : {kpis['agente_code']} - {kpis['agente_name']}")
        print(f" Rol Asignado       : {kpis['rol_pui']}")
        print(f" CIOR Identificado  : {kpis['cior_name']}")
        print(f" Rango de Análisis  : {params.fecha_inicio} a {params.fecha_fin}")
        if es_pronostico:
            print(f" Motor Pronóstico   : Google TimesFM (Predicción Diaria → Agregación Mensual)")
            print(f" Horizonte Futuro   : {kpis.get('horizonte_pronostico', 'N/A')}")
        print("-" * 80)
        print(" PARÁMETROS DE CONFIGURACIÓN")
        print(f"  • Prima Riesgo Cartera (rcpui)    : ${params.rcpui:.3f} / kWh")
        print(f"  • Áreas Especiales (pct_areas)    : {params.pct_areas_especiales * 100:.1f}%")
        print(f"  • Factor Recaudo CNIOR (recaudo)  : {params.factor_recaudo_cnior * 100:.1f}%")
        print(f"  • Esquema Competitivo (cfpui)     : {'SI' if params.esquema_competitivo else 'NO (Transitorio)'} (${params.cfpui:.3f} / kWh)")
        print("-" * 80)
        print(" RESUMEN DE IMPACTO FINANCIERO Y DE CAJA")
        print(f"  • PUI Asignado (Energía)          : {kpis['total_pui_kwh']:,.2f} kWh")
        print(f"  • PUI Asignado (Dinero)           : ${kpis['total_pui_cop']:,.2f} COP")
        print(f"  • Total Egreso por Giros al CIOR  : ${kpis['total_egreso_giro_cop']:,.2f} COP")
        print(f"  • Total Recaudo Efectivo          : ${kpis['total_recaudo_cop']:,.2f} COP")
        print(f"  • FLUJO NETO DE CAJA (PÉRDIDA)    : ${kpis['flujo_neto_caja_total_cop']:,.2f} COP")
        print(f"  • SOBRECOSTO POR INCOBRABILIDAD   : ${kpis['sobrecosto_total_cop']:,.2f} COP ({kpis['pct_perdida_promedio']:.2f}%)")
        print("-" * 80)
        print(" TOP MERCADOS POR SOBRECOSTO (ACUMULADO)")
        print(f" {'MERCADO':<20} | {'EGRESO GIRO (COP)':<22} | {'SOBRECOSTO (COP)':<20}")
        print("-" * 80)
        for m in kpis['top_mercados_sobrecosto'][:5]:
            m_name = (m.get('name') or m.get('code') or 'N/A')[:20]
            print(f" {m_name:<20} | ${m['egreso']:>20,.2f} | ${m['sobrecosto']:>18,.2f}")
        print("=" * 80 + "\n")

        return "console_output_rendered"
