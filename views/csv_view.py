"""
Vista CSV para Exportación de Datasets PUI (Históricos y Pronósticos) con nombres de columna del negocio y unidades explícitas.
"""
import os
import csv
from typing import List, Dict, Any
from views.base_view import BaseReportView
from models.pui_parameters import PUIParameters

BUSINESS_COLUMN_MAP = {
    "agente_code": "Código Agente",
    "agente_name": "Nombre Comercializador",
    "rol_pui": "Rol Regulado PUI (CIOR/CNIOR)",
    "es_asociado_acce": "Asociado ACCE (Sí/No)",
    "mercado_code": "Código Mercado Comercialización",
    "mercado_name": "Mercado Comercialización",
    "mes": "Período (Mes)",
    "tipo_registro": "Tipo de Registro",
    "es_pronostico": "Es Pronóstico (Sí/No)",
    "vr_agente_kwh": "Demanda Comercial Agente (VR - DemaComeReg) [kWh]",
    "energia_contratos_kwh": "Cobertura Energía en Contratos (Compras Contrato) [kWh]",
    "energia_bolsa_kwh": "Exposición Energía en Bolsa Spot (Compras Bolsa) [kWh]",
    "pct_cobertura_contratos": "Porcentaje Cobertura por Contratos [%]",
    "pct_exposicion_bolsa": "Porcentaje Exposición en Bolsa Spot [%]",
    "estado_cobertura": "Estado Cobertura de Demanda Agente",
    "dias_activos_mes": "Días Activos Mes",
    "promedio_diario_kwh": "Promedio Diario Agente [kWh/día]",
    "precio_prom_contratos_cop_kwh": "Costo Unitario Prestación (CU - PrecPromCont) [COP/kWh]",
    "vr_mercado_kwh": "Demanda Comercial Mercado Total (VR - DemaCome) [kWh]",
    "vr_total_todos_agentes_kwh": "Demanda Total Sistema (Todos Agentes) [kWh]",
    "vr_total_cniors_kwh": "Demanda Total Sistema (CNIORs) [kWh]",
    "participacion_ettc_pct_total": "Participación Agente en Total Sistema [%]",
    "participacion_ettc_pct_cniors": "Participación Agente entre CNIORs [%]",
    "ranking_vr_mes": "Ranking Demanda Agente en el Mes",
    "vr_mercado_m1_kwh": "Demanda Mercado Rezago m-1 (VR m-1) [kWh]",
    "vpui_mercado_m1_kwh": "Volumen Áreas Especiales Rezago m-1 (VPUI m-1) [kWh]",
    "cu_m1_cop_kwh": "Costo Unitario Rezago m-1 (CU m-1) [COP/kWh]",
    "vr_mercado_m2_kwh": "Demanda Mercado Rezago m-2 (VR m-2) [kWh]",
    "vpui_actual_kwh": "Volumen Áreas Especiales Actual (VPUI) [kWh]",
    "crpui_unitario": "Cargo Unitario Transitorio (CRPUI) [COP/kWh]",
    "cfpui_unitario": "Cargo Unitario Fijo Competitivo (CFPUI) [COP/kWh]",
    "pui_mercado_total": "Valor Total PUI Mercado [COP]",
    "giro_obligatorio_mercado": "Giro Obligatorio Total Mercado [COP]",
    "recaudo_real_mercado": "Recaudo Real Estimado Mercado [COP]",
    "pui_energia_kwh": "Asignación Energía PUI Agente [kWh]",
    "pui_dinero_cop": "Valor Asignación PUI Agente [COP]",
    "ingresos_pui_facturado": "Ingresos PUI Facturados Agente [COP]",
    "egreso_giro_cior": "Egreso Giro Obligatorio al CIOR [COP]",
    "recaudo_real_agente": "Recaudo Real Efectivo Agente [COP]",
    "flujo_neto_caja_pui": "Flujo Neto de Caja PUI [COP]",
    "sobrecosto_pui": "Sobrecosto por Incobrabilidad [COP]",
    "pct_perdida_incobrabilidad": "Pérdida por Incobrabilidad [%]",
    "cior_code": "Código Comercializador CIOR",
    "cior_name": "Nombre Comercializador CIOR",
    "cior_vr_total_historial": "Demanda Acumulada CIOR [kWh]",
    "total_giros_recibidos_cior": "Total Giros Recibidos CIOR [COP]",
    "param_rcpui": "Parámetro Prima Riesgo Cartera (rcpui) [COP/kWh]",
    "param_pct_areas_especiales": "Parámetro % Áreas Especiales [%]",
    "param_factor_recaudo": "Parámetro Factor Recaudo CNIOR [%]",
    "param_cfpui": "Parámetro Cargo Competitivo (cfpui) [COP/kWh]",
    "param_esquema_competitivo": "Parámetro Esquema Competitivo [Sí/No]"
}

class CSVReportView(BaseReportView):
    """Genera informes en formato CSV estructurado con encabezados amigables del negocio y unidades."""

    def render(self, data: List[Dict[str, Any]], kpis: Dict[str, Any], params: PUIParameters, output_path: str = None) -> str:
        if not output_path:
            output_path = f"pui_report_{params.agente_objetivo}.csv"

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        if not data:
            print("[CSV View] No hay datos disponibles para exportar.")
            return output_path

        # Normalizar 'mes' (date/datetime -> str) y descartar keys inconsistentes
        for r in data:
            mes = r.get('mes')
            if mes is not None and not isinstance(mes, str):
                r['mes'] = mes.strftime("%Y-%m-%d") if hasattr(mes, 'strftime') else str(mes)

        mapped_rows = []
        for r in data:
            mapped_row = {BUSINESS_COLUMN_MAP.get(k, k): v for k, v in r.items()}
            mapped_rows.append(mapped_row)

        fieldnames = list(mapped_rows[0].keys())
        clean_rows = [{k: row.get(k, None) for k in fieldnames} for row in mapped_rows]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(clean_rows)

        print(f"[CSV View] Informe exportado exitosamente a: {output_path}")
        return output_path
