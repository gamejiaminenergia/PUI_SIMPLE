"""
Controlador Principal de Informes PUI (ReportController).
Coordina el modelo de datos históricos y pronósticos (Forecast) con la generación de vistas y exportación en carpeta 'output/'
utilizando nombres de columna amigables del negocio y la base de datos con unidades explícitas y balance de Cobertura de Demanda (Contratos vs Bolsa).
"""
import os
import csv
import logging
from typing import List, Dict, Any
import pandas as pd

from models.pui_parameters import PUIParameters
from models.pui_model import PUIModel
from models.pui_forecast_model import PUIForecastModel
from views.console_view import ConsoleReportView
from views.html_view import HTMLReportView
from views.csv_view import CSVReportView

logger = logging.getLogger(__name__)

# Mapeo de nombres técnicos a nombres familiares de negocio/BD con unidades explícitas
BUSINESS_COLUMN_MAP = {
    "agente_code": "Código Agente",
    "agente_name": "Nombre Comercializador",
    "rol_pui": "Rol Regulado PUI (CIOR/CNIOR)",
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

class ReportController:
    """Controlador de generación y gestión de informes PUI (Histórico y Pronóstico)."""

    def __init__(self, model: PUIModel = None, forecast_model: PUIForecastModel = None):
        self.model = model or PUIModel()
        self.forecast_model = forecast_model or PUIForecastModel()
        self.views = {
            "console": ConsoleReportView(),
            "html": HTMLReportView(),
            "csv": CSVReportView()
        }

    def generate_report(
        self,
        params: PUIParameters = None,
        formats: List[str] = None,
        output_dir: str = "output",
        mode: str = "both"
    ) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo MVC:
        1. Consulta y procesa los datos mediante el Modelo (Histórico + Forecast).
        2. Garantiza la exportación de múltiples CSVs detallados de auditoría en 'output/' con nombres de negocio, unidades y cobertura de demanda.
        3. Genera el reporte HTML interactivo completo con metodología, fórmulas, auditoría y cobertura de demanda.
        """
        formats = formats or ["console", "html", "csv"]
        os.makedirs(output_dir, exist_ok=True)

        if params is None:
            params = self.forecast_model.get_forecast_params()

        print(f"\n[MVC Controller] Iniciando generación de informes PUI (Modo: '{mode.upper()}') para agente '{params.agente_objetivo}'...")

        if mode.lower() in ["forecast", "both"]:
            daily_df, raw_data, kpis = self.forecast_model.generate_daily_and_monthly_forecast(params)
        else:
            raw_data = self.model.get_report_data(params)
            for r in raw_data:
                r["tipo_registro"] = "HISTORICO"
                r["es_pronostico"] = False
            kpis = self.model.calculate_summary_kpis(raw_data, params)
            daily_df = pd.DataFrame()

        results = {
            "kpis": kpis,
            "outputs": {},
            "daily_df": daily_df,
            "raw_data": raw_data
        }

        # Generar CSVs amigables con nombres de negocio y unidades explícitas en output/
        self._export_specialized_csvs(output_dir, raw_data, daily_df, params)

        # Renderizar Vistas seleccionadas
        html_path = os.path.join(output_dir, f"pui_report_{params.agente_objetivo}_unificado.html")
        csv_path = os.path.join(output_dir, f"pui_dataset_unificado.csv")

        for fmt in formats:
            fmt_lower = fmt.lower().strip()
            if fmt_lower in self.views:
                view = self.views[fmt_lower]
                out_path = html_path if fmt_lower == "html" else (csv_path if fmt_lower == "csv" else None)
                rendered_res = view.render(raw_data, kpis, params, out_path)
                results["outputs"][fmt_lower] = rendered_res

        print(f"[MVC Controller] Proceso completado exitosamente. Todos los archivos se guardaron en: '{output_dir}/'\n")
        return results

    def _export_specialized_csvs(self, output_dir: str, raw_data: List[Dict[str, Any]], daily_df: pd.DataFrame, params: PUIParameters):
        """Exporta múltiples archivos CSV amigables con encabezados claros de negocio, referencias de BD y unidades."""

        # 1. Dataset Unificado Principal (45+ columnas traducidas)
        path_unificado = os.path.join(output_dir, "pui_dataset_unificado.csv")
        if raw_data:
            mapped_rows = []
            for r in raw_data:
                mapped_row = {BUSINESS_COLUMN_MAP.get(k, k): v for k, v in r.items()}
                mapped_rows.append(mapped_row)

            with open(path_unificado, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(mapped_rows[0].keys()))
                writer.writeheader()
                writer.writerows(mapped_rows)
            print(f"  ✓ Exportado Dataset Unificado: {path_unificado}")

        # 2. CSV de Auditoría de Fórmulas CREG & Cobertura de Demanda
        path_auditoria = os.path.join(output_dir, "pui_auditoria_formulas.csv")
        auditoria_rows = []
        for r in raw_data:
            auditoria_rows.append({
                "Período (Mes)": r.get("mes"),
                "Tipo de Registro": r.get("tipo_registro"),
                "Código Agente": r.get("agente_code"),
                "Rol PUI": r.get("rol_pui"),
                "Código Mercado": r.get("mercado_code"),
                "Mercado Comercialización": r.get("mercado_name"),
                "Demanda Agente (VR - DemaComeReg) [kWh]": r.get("vr_agente_kwh"),
                "Cobertura Energía en Contratos [kWh]": r.get("energia_contratos_kwh"),
                "Exposición Energía en Bolsa Spot [kWh]": r.get("energia_bolsa_kwh"),
                "Porcentaje Cobertura Contratos [%]": r.get("pct_cobertura_contratos"),
                "Porcentaje Exposición Bolsa Spot [%]": r.get("pct_exposicion_bolsa"),
                "Estado Cobertura Demanda": r.get("estado_cobertura"),
                "Costo Unitario Prestación (CU - PrecPromCont) [COP/kWh]": r.get("precio_prom_contratos_cop_kwh"),
                "Demanda Mercado Actual (VR) [kWh]": r.get("vr_mercado_kwh"),
                "Demanda Mercado Rezago m-1 (VR m-1) [kWh]": r.get("vr_mercado_m1_kwh"),
                "Volumen Áreas Especiales m-1 (VPUI m-1) [kWh]": r.get("vpui_mercado_m1_kwh"),
                "Costo Unitario Rezago m-1 (CU m-1) [COP/kWh]": r.get("cu_m1_cop_kwh"),
                "Demanda Mercado Rezago m-2 (VR m-2) [kWh]": r.get("vr_mercado_m2_kwh"),
                "Volumen Áreas Especiales Actual (VPUI) [kWh]": r.get("vpui_actual_kwh"),
                "Cargo Transitorio Unitario (CRPUI) [COP/kWh]": r.get("crpui_unitario"),
                "Cargo Competitivo Fijo (CFPUI) [COP/kWh]": r.get("cfpui_unitario"),
                "Valor Total PUI Mercado [COP]": r.get("pui_mercado_total"),
                "Giro Obligatorio Total Mercado [COP]": r.get("giro_obligatorio_mercado"),
                "Recaudo Real Estimado Mercado [COP]": r.get("recaudo_real_mercado"),
                "Participación Agente CNIOR [%]": r.get("participacion_ettc_pct_cniors"),
                "Asignación Energía PUI Agente [kWh]": r.get("pui_energia_kwh"),
                "Valor Asignación PUI Agente [COP]": r.get("pui_dinero_cop"),
                "Egreso Giro Obligatorio al CIOR [COP]": r.get("egreso_giro_cior"),
                "Recaudo Real Efectivo Agente [COP]": r.get("recaudo_real_agente"),
                "Flujo Neto de Caja PUI [COP]": r.get("flujo_neto_caja_pui"),
                "Sobrecosto por Incobrabilidad [COP]": r.get("sobrecosto_pui"),
                "Pérdida por Incobrabilidad [%]": r.get("pct_perdida_incobrabilidad")
            })
        if auditoria_rows:
            with open(path_auditoria, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(auditoria_rows[0].keys()))
                writer.writeheader()
                writer.writerows(auditoria_rows)
            print(f"  ✓ Exportado CSV Auditoría de Fórmulas CREG: {path_auditoria}")

        # 3. CSV de Resumen Mensual Consolidado (High-Level)
        path_resumen_mensual = os.path.join(output_dir, "pui_resumen_mensual.csv")
        mes_summary = {}
        for r in raw_data:
            mes = str(r.get("mes"))
            if mes not in mes_summary:
                mes_summary[mes] = {
                    "Período (Mes)": mes,
                    "Tipo de Registro": r.get("tipo_registro"),
                    "Demanda Comercial Agente (VR - DemaComeReg) [kWh]": 0.0,
                    "Cobertura Energía en Contratos [kWh]": 0.0,
                    "Exposición Energía en Bolsa Spot [kWh]": 0.0,
                    "Porcentaje Cobertura Contratos [%]": r.get("pct_cobertura_contratos", 85.0),
                    "Porcentaje Exposición Bolsa Spot [%]": r.get("pct_exposicion_bolsa", 15.0),
                    "PUI Energía Total Agente [kWh]": 0.0,
                    "PUI Valor Total Agente [COP]": 0.0,
                    "Egreso Giro Total CIOR [COP]": 0.0,
                    "Recaudo Real Efectivo Total [COP]": 0.0,
                    "Flujo Neto de Caja Total [COP]": 0.0,
                    "Sobrecosto Incobrabilidad Total [COP]": 0.0
                }
            mes_summary[mes]["Demanda Comercial Agente (VR - DemaComeReg) [kWh]"] += float(r.get("vr_agente_kwh", 0))
            mes_summary[mes]["Cobertura Energía en Contratos [kWh]"] += float(r.get("energia_contratos_kwh", 0))
            mes_summary[mes]["Exposición Energía en Bolsa Spot [kWh]"] += float(r.get("energia_bolsa_kwh", 0))
            mes_summary[mes]["PUI Energía Total Agente [kWh]"] += float(r.get("pui_energia_kwh", 0))
            mes_summary[mes]["PUI Valor Total Agente [COP]"] += float(r.get("pui_dinero_cop", 0))
            mes_summary[mes]["Egreso Giro Total CIOR [COP]"] += float(r.get("egreso_giro_cior", 0))
            mes_summary[mes]["Recaudo Real Efectivo Total [COP]"] += float(r.get("recaudo_real_agente", 0))
            mes_summary[mes]["Flujo Neto de Caja Total [COP]"] += float(r.get("flujo_neto_caja_pui", 0))
            mes_summary[mes]["Sobrecosto Incobrabilidad Total [COP]"] += float(r.get("sobrecosto_pui", 0))

        if mes_summary:
            resumen_list = sorted(mes_summary.values(), key=lambda x: x["Período (Mes)"])
            with open(path_resumen_mensual, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(resumen_list[0].keys()))
                writer.writeheader()
                writer.writerows(resumen_list)
            print(f"  ✓ Exportado CSV Resumen Mensual Consolidado: {path_resumen_mensual}")

        # 4. CSV de Predicciones Diarias Granulares con TimesFM y Cobertura
        path_diario = os.path.join(output_dir, "pui_series_diarias_forecast.csv")
        if not daily_df.empty:
            df_mapped = daily_df.rename(columns={
                "fecha": "Fecha (Día)",
                "agente_code": "Código Agente",
                "mercado_code": "Código Mercado Comercialización",
                "mes": "Período (Mes)",
                "vr_agente_kwh": "Demanda Comercial Agente (VR - DemaComeReg) [kWh]",
                "energia_contratos_kwh": "Cobertura Energía en Contratos [kWh]",
                "energia_bolsa_kwh": "Exposición Energía en Bolsa Spot [kWh]",
                "pct_cobertura_contratos": "Porcentaje Cobertura Contratos [%]",
                "pct_exposicion_bolsa": "Porcentaje Exposición Bolsa Spot [%]",
                "estado_cobertura": "Estado Cobertura Demanda",
                "precio_prom_contratos_cop_kwh": "Costo Unitario (CU - PrecPromCont) [COP/kWh]",
                "vr_mercado_kwh": "Demanda Mercado Total (VR - DemaCome) [kWh]",
                "pui_energia_kwh": "Asignación Diaria PUI [kWh]",
                "pui_dinero_cop": "Valor Diarios PUI [COP]",
                "egreso_giro_cior": "Egreso Giro Diario al CIOR [COP]",
                "recaudo_real_agente": "Recaudo Real Diario Agente [COP]",
                "flujo_neto_caja_pui": "Flujo Neto Caja Diarios [COP]",
                "sobrecosto_pui": "Sobrecosto Diarios [COP]",
                "tipo_registro": "Tipo de Registro",
                "es_pronostico": "Es Pronóstico (Sí/No)"
            })
            df_mapped.to_csv(path_diario, index=False, encoding="utf-8")
            print(f"  ✓ Exportado CSV Predicciones Diarias TimesFM: {path_diario}")
