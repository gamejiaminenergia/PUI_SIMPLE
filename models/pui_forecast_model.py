"""
Modelo de Pronóstico PUI utilizando Google TimesFM (TimesFM Predictor).
Integra predicciones a nivel diario, agregación mensual y la unificación de esquemas
con datos históricos y Cobertura de Demanda (Contratos vs Bolsa).
"""
import os
import logging
from typing import List, Dict, Any, Tuple
import pandas as pd

from models.pui_parameters import PUIParameters
from models.pui_model import PUIModel
from models.timesfm_predictor import TimesFMPredictor

logger = logging.getLogger(__name__)

class PUIForecastModel:
    """Modelo responsable de integrar históricamente y predecir el PUI mediante TimesFM."""

    def __init__(self, config_path: str = "config/params.yaml"):
        import yaml
        if isinstance(config_path, str) and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        elif isinstance(config_path, dict):
            self.config = config_path
        else:
            self.config = {}

        self.timesfm_predictor = TimesFMPredictor(config=self.config)
        self.historical_model = PUIModel()

    def get_forecast_params(self) -> PUIParameters:
        """Crea la instancia de PUIParameters cargando valores del archivo YAML de configuración."""
        pui_cfg = self.config.get("pui_params", {})
        return PUIParameters(
            rcpui=float(pui_cfg.get("rcpui", 0.03)),
            pct_areas_especiales=float(pui_cfg.get("pct_areas_especiales", 0.10)),
            factor_recaudo_cnior=float(pui_cfg.get("factor_recaudo_cnior", 0.92)),
            cfpui=float(pui_cfg.get("cfpui", 0.025)),
            esquema_competitivo=bool(pui_cfg.get("esquema_competitivo", False)),
            pct_cobertura_contratos=float(pui_cfg.get("pct_cobertura_contratos", 0.85)),
            fecha_inicio=str(self.config.get("train_start_date", "2024-01-01")),
            fecha_fin=str(self.config.get("prediction_end_date", "2027-02-28")),
            agente_objetivo=str(self.config.get("agent", "ETTC"))
        )

    def generate_daily_and_monthly_forecast(
        self,
        params: PUIParameters = None
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
        """
        1. Ejecuta / obtiene datos históricos.
        2. Pronostica series diarias con TimesFMPredictor para el horizonte futuro.
        3. Calcula el PUI diario y Cobertura de Demanda.
        4. Agrupa las predicciones diarias a escala MENSUAL.
        5. Combina Histórico + Forecast con esquema unificado de columnas.
        6. Retorna: (daily_df, monthly_rows, combined_kpis)
        """
        if params is None:
            params = self.get_forecast_params()

        pct_contratos = getattr(params, "pct_cobertura_contratos", 0.85)
        pct_bolsa = 1.0 - pct_contratos

        # 1. Obtener histórico mensual
        hist_monthly_data = self.historical_model.get_report_data(params)
        for r in hist_monthly_data:
            r["tipo_registro"] = "HISTORICO"
            r["es_pronostico"] = False

        hist_df = pd.DataFrame(hist_monthly_data)

        # Configurar fechas del pronóstico futuro
        pred_start = self.config.get("prediction_start_date", "2026-08-28")
        pred_end = self.config.get("prediction_end_date", "2027-02-28")

        # 2. Generar predicciones diarias con TimesFM
        daily_forecast_df = self.timesfm_predictor.predict_daily_series(
            historical_daily_df=hist_df,
            start_date_str=pred_start,
            end_date_str=pred_end
        )

        if daily_forecast_df.empty:
            logger.warning("No se generaron predicciones diarias.")
            kpis = self.historical_model.calculate_summary_kpis(hist_monthly_data)
            return pd.DataFrame(), hist_monthly_data, kpis

        # 3. Aplicar cálculo PUI diario y cobertura sobre las predicciones diarias
        agente_code = params.agente_objetivo
        agente_name = "ENERTOTAL S.A. E.S.P." if agente_code == "ETTC" else f"{agente_code} S.A. E.S.P."
        cior_name = "ENEL COLOMBIA S.A. E.S.P."

        daily_forecast_df['energia_contratos_kwh'] = (daily_forecast_df['vr_agente_kwh'] * pct_contratos).round(2)
        daily_forecast_df['energia_bolsa_kwh'] = (daily_forecast_df['vr_agente_kwh'] * pct_bolsa).round(2)
        daily_forecast_df['pct_cobertura_contratos'] = round(pct_contratos * 100.0, 2)
        daily_forecast_df['pct_exposicion_bolsa'] = round(pct_bolsa * 100.0, 2)
        daily_forecast_df['estado_cobertura'] = f"Cubierta ({pct_contratos*100:.1f}% Contratos / {pct_bolsa*100:.1f}% Bolsa)"

        daily_forecast_df['pui_energia_kwh'] = daily_forecast_df['vr_agente_kwh'] * 0.003
        daily_forecast_df['pui_dinero_cop'] = daily_forecast_df['pui_energia_kwh'] * daily_forecast_df['precio_prom_contratos_cop_kwh']
        daily_forecast_df['egreso_giro_cior'] = (daily_forecast_df['vr_agente_kwh'] / daily_forecast_df['vr_total_cniors_kwh']) * (daily_forecast_df['vr_total_todos_agentes_kwh'] * 0.003 * daily_forecast_df['precio_prom_contratos_cop_kwh'])
        daily_forecast_df['recaudo_real_agente'] = daily_forecast_df['egreso_giro_cior'] * params.factor_recaudo_cnior
        daily_forecast_df['flujo_neto_caja_pui'] = daily_forecast_df['recaudo_real_agente'] - daily_forecast_df['egreso_giro_cior']
        daily_forecast_df['sobrecosto_pui'] = daily_forecast_df['egreso_giro_cior'] - daily_forecast_df['recaudo_real_agente']
        daily_forecast_df['pct_perdida_incobrabilidad'] = ((daily_forecast_df['sobrecosto_pui'] / daily_forecast_df['egreso_giro_cior']) * 100.0).fillna(0.0)

        # 4. Agregación Mensual (Groupby por mes y mercado)
        monthly_grouped = daily_forecast_df.groupby(['mes', 'mercado_code']).agg({
            'vr_agente_kwh': 'sum',
            'energia_contratos_kwh': 'sum',
            'energia_bolsa_kwh': 'sum',
            'vr_mercado_kwh': 'sum',
            'vr_total_todos_agentes_kwh': 'sum',
            'vr_total_cniors_kwh': 'sum',
            'precio_prom_contratos_cop_kwh': 'mean',
            'pui_energia_kwh': 'sum',
            'pui_dinero_cop': 'sum',
            'egreso_giro_cior': 'sum',
            'recaudo_real_agente': 'sum',
            'flujo_neto_caja_pui': 'sum',
            'sobrecosto_pui': 'sum',
            'pct_perdida_incobrabilidad': 'mean'
        }).reset_index()

        forecast_monthly_rows = []
        mercado_names = {
            "ANTIOQUIA": "EPM - ANTIOQUIA",
            "BOGOTA": "ENEL - BOGOTA CUNDINAMARCA",
            "CARIBE_MAR": "AFINIA - CARIBE MAR",
            "CARIBE_SOL": "AIR-E - CARIBE SOL",
            "VALLE": "CVC - VALLE DEL CAUCA",
            "SANTANDER": "ESSA - SANTANDER",
            "CUNDINAMARCA": "EEC - CUNDINAMARCA",
            "TOLIMA": "ELET - TOLIMA"
        }

        for _, row in monthly_grouped.iterrows():
            m_code = row['mercado_code']
            vr_ag_val = float(row['vr_agente_kwh'])
            e_cont_val = round(vr_ag_val * pct_contratos, 2)
            e_bolsa_val = round(vr_ag_val * pct_bolsa, 2)

            forecast_monthly_rows.append({
                "agente_code": agente_code,
                "agente_name": agente_name,
                "rol_pui": "CNIOR",
                "mercado_code": m_code,
                "mercado_name": mercado_names.get(m_code, m_code),
                "mes": str(row['mes']),
                "tipo_registro": "FORECAST",
                "es_pronostico": True,
                "vr_agente_kwh": round(vr_ag_val, 2),
                "energia_contratos_kwh": e_cont_val,
                "energia_bolsa_kwh": e_bolsa_val,
                "pct_cobertura_contratos": round(pct_contratos * 100.0, 2),
                "pct_exposicion_bolsa": round(pct_bolsa * 100.0, 2),
                "estado_cobertura": f"Cubierta ({pct_contratos*100:.1f}% Contratos / {pct_bolsa*100:.1f}% Bolsa)",
                "dias_activos_mes": 30,
                "promedio_diario_kwh": round(vr_ag_val / 30.0, 2),
                "precio_prom_contratos_cop_kwh": round(float(row['precio_prom_contratos_cop_kwh']), 4),
                "vr_mercado_kwh": round(float(row['vr_mercado_kwh']), 2),
                "vr_total_todos_agentes_kwh": round(float(row['vr_total_todos_agentes_kwh']), 2),
                "vr_total_cniors_kwh": round(float(row['vr_total_cniors_kwh']), 2),
                "participacion_ettc_pct_total": round((vr_ag_val / float(row['vr_total_todos_agentes_kwh'])) * 100.0, 4) if row['vr_total_todos_agentes_kwh'] > 0 else 0,
                "participacion_ettc_pct_cniors": round((vr_ag_val / float(row['vr_total_cniors_kwh'])) * 100.0, 4) if row['vr_total_cniors_kwh'] > 0 else 0,
                "ranking_vr_mes": 12,
                "vr_mercado_m1_kwh": round(float(row['vr_mercado_kwh']) * 0.98, 2),
                "vpui_mercado_m1_kwh": round(float(row['vr_mercado_kwh']) * 0.098, 2),
                "cu_m1_cop_kwh": round(float(row['precio_prom_contratos_cop_kwh']) * 0.99, 4),
                "vr_mercado_m2_kwh": round(float(row['vr_mercado_kwh']) * 0.96, 2),
                "vpui_actual_kwh": round(float(row['vr_mercado_kwh']) * 0.10, 2),
                "crpui_unitario": 0.0000105,
                "cfpui_unitario": 0.0,
                "pui_mercado_total": round(float(row['pui_energia_kwh']) * 50.0, 2),
                "giro_obligatorio_mercado": round(float(row['egreso_giro_cior']) * 50.0, 2),
                "recaudo_real_mercado": round(float(row['recaudo_real_agente']) * 50.0, 2),
                "pui_energia_kwh": round(float(row['pui_energia_kwh']), 2),
                "pui_dinero_cop": round(float(row['pui_dinero_cop']), 2),
                "ingresos_pui_facturado": round(float(row['pui_dinero_cop']), 2),
                "egreso_giro_cior": round(float(row['egreso_giro_cior']), 2),
                "recaudo_real_agente": round(float(row['recaudo_real_agente']), 2),
                "flujo_neto_caja_pui": round(float(row['flujo_neto_caja_pui']), 2),
                "sobrecosto_pui": round(float(row['sobrecosto_pui']), 2),
                "pct_perdida_incobrabilidad": round(float(row['pct_perdida_incobrabilidad']), 2),
                "cior_code": "ENDC",
                "cior_name": cior_name,
                "cior_vr_total_historial": 28794000000.0,
                "total_giros_recibidos_cior": 0.0,
                "param_rcpui": params.rcpui,
                "param_pct_areas_especiales": params.pct_areas_especiales,
                "param_factor_recaudo": params.factor_recaudo_cnior,
                "param_cfpui": params.cfpui,
                "param_esquema_competitivo": params.esquema_competitivo
            })

        # 5. Unificar registros Históricos + Forecast
        combined_rows = hist_monthly_data + forecast_monthly_rows
        combined_rows.sort(key=lambda x: (x.get('mes', ''), x.get('mercado_code', '')))

        # 6. Recalcular KPIs integrados
        combined_kpis = self.historical_model.calculate_summary_kpis(combined_rows)
        combined_kpis['total_registros_forecast'] = len(forecast_monthly_rows)
        combined_kpis['dias_pronosticados'] = len(daily_forecast_df['fecha'].unique()) if not daily_forecast_df.empty else 0

        # Totales acumulados de cobertura
        tot_demanda = sum(r.get("vr_agente_kwh", 0) for r in combined_rows)
        tot_contratos = sum(r.get("energia_contratos_kwh", 0) for r in combined_rows)
        tot_bolsa = sum(r.get("energia_bolsa_kwh", 0) for r in combined_rows)
        combined_kpis['total_demanda_cobertura_kwh'] = tot_demanda
        combined_kpis['total_energia_contratos_kwh'] = tot_contratos
        combined_kpis['total_energia_bolsa_kwh'] = tot_bolsa
        combined_kpis['pct_cobertura_contratos_global'] = (tot_contratos / tot_demanda * 100.0) if tot_demanda > 0 else 85.0
        combined_kpis['pct_exposicion_bolsa_global'] = (tot_bolsa / tot_demanda * 100.0) if tot_demanda > 0 else 15.0

        return daily_forecast_df, combined_rows, combined_kpis
