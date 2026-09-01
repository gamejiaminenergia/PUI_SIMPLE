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
        # Conectar el modelo histórico con el gestor de BD para usar la query real
        try:
            from database.connection import DatabaseConnectionManager
            self.historical_model = PUIModel(db_connection=DatabaseConnectionManager())
        except Exception:
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
            derive_cobertura_desde_datos=bool(pui_cfg.get("derive_cobertura_desde_datos", True)),
            fecha_inicio=str(self.config.get("train_start_date", "2024-01-01")),
            fecha_fin=str(self.config.get("prediction_end_date", "2027-02-28")),
            agente_objetivo=str(self.config.get("agent", "ETTC")),
            agentes_benchmark=list(self.config.get("agents", []))
        )

    def _pronosticar_cobertura(
        self,
        hist_monthly_data: List[Dict[str, Any]],
        pred_start: str,
        pred_end: str
    ) -> Dict[str, float]:
        """
        Construye la serie histórica mensual REAL de pct_cobertura_contratos y la pronostica
        con TimesFM 3.0 (máximo histórico disponible). Retorna {mes: %cobertura} por mes futuro.

        Si no hay histórico (derive_cobertura_desde_datos=False o sin datos), usa el
        parámetro de reserva pct_cobertura_contratos como fallback.
        """
        from datetime import datetime

        # Obtener los meses del horizonte a pronosticar
        meses_futuros = []
        dt = datetime.strptime(pred_start[:10], "%Y-%m-%d")
        fin = datetime.strptime(pred_end[:10], "%Y-%m-%d")
        while dt <= fin:
            key = dt.strftime("%Y-%m-01")
            if key not in meses_futuros:
                meses_futuros.append(key)
            if dt.month == 12:
                dt = dt.replace(year=dt.year + 1, month=1)
            else:
                dt = dt.replace(month=dt.month + 1)
        horizon = len(meses_futuros)

        # Serie histórica real de cobertura por mes (agregada del histórico)
        hist_por_mes = {}
        for r in hist_monthly_data:
            pct = r.get("pct_cobertura_contratos")
            if pct is None:
                continue
            mes = r.get("mes")
            if not mes:
                continue
            try:
                v = float(pct)
            except (TypeError, ValueError):
                continue
            # Si es fracción (0-1) convertir a %; si ya es % (posible >1) mantener
            hist_por_mes[str(mes)[:10]] = v * 100.0 if v <= 1.5 else v

        derive = getattr(self, "config", {}).get("pui_params", {}).get("derive_cobertura_desde_datos", True)
        if derive and hist_por_mes:
            # Ordenar serie por mes (2015-01 -> último)
            serie = pd.Series(dict(sorted(hist_por_mes.items())))
            pcts = list(serie.values)
            logger.info(f"Entrenando pronóstico de cobertura con {len(pcts)} meses históricos "
                        f"(rango {serie.index[0]} -> {serie.index[-1]}).")
            forecast = self.timesfm_predictor.predict_coverage_series(pcts, horizon)
        else:
            fallback_pct = self._pct_fallback()
            logger.info(f"Sin histórico de cobertura real; usando fallback {fallback_pct}%.")
            forecast = [fallback_pct] * horizon

        return {m: round(f, 2) for m, f in zip(meses_futuros, forecast)}

    def _pct_fallback(self) -> float:
        """% de cobertura de reserva (de params.yaml) cuando no hay histórico que derive la cobertura."""
        default = self.config.get("pui_params", {}).get("pct_cobertura_contratos", 0.85)
        try:
            v = float(default)
            return v * 100.0 if v <= 1.5 else v
        except (TypeError, ValueError):
            return 85.0

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

        # 1. Obtener histórico mensual
        hist_monthly_data = self.historical_model.get_report_data(params)
        for r in hist_monthly_data:
            r["tipo_registro"] = "HISTORICO"
            r["es_pronostico"] = False

        hist_df = pd.DataFrame(hist_monthly_data)

        # Configurar fechas del pronóstico futuro
        pred_start = self.config.get("prediction_start_date", "2026-08-28")
        pred_end = self.config.get("prediction_end_date", "2027-02-28")

        # 2a. Pronosticar COBERTURA de contratos (% por mes futuro) con TimesFM 3.0
        #     usando el máximo histórico mensual real disponible (NO el 0.85 fijo).
        pct_por_mes = self._pronosticar_cobertura(hist_monthly_data, pred_start, pred_end)

        # 2. Generar predicciones diarias con TimesFM
        daily_forecast_df = self.timesfm_predictor.predict_daily_series(
            historical_daily_df=hist_df,
            start_date_str=pred_start,
            end_date_str=pred_end
        )

        if daily_forecast_df.empty:
            logger.warning("No se generaron predicciones diarias.")
            kpis = self.historical_model.calculate_summary_kpis(hist_monthly_data, params)
            return pd.DataFrame(), hist_monthly_data, kpis

        # 3. Aplicar cálculo PUI diario y cobertura sobre las predicciones diarias
        agente_code = params.agente_objetivo
        agente_name = "ENERTOTAL S.A. E.S.P." if agente_code == "ETTC" else f"{agente_code} S.A. E.S.P."
        cior_name = "ENEL COLOMBIA S.A. E.S.P."

        # Cobertura mensual diferenciada por mes (pronóstico TimesFM), no un 0.85 único
        daily_forecast_df['pct_cobertura_contratos'] = daily_forecast_df['mes'].map(pct_por_mes).fillna(
            params.pct_cobertura_contratos * 100.0)
        daily_forecast_df['pct_exposicion_bolsa'] = (100.0 - daily_forecast_df['pct_cobertura_contratos']).round(2)
        daily_forecast_df['pct_cobertura_contratos'] = daily_forecast_df['pct_cobertura_contratos'].round(2)
        daily_forecast_df['energia_contratos_kwh'] = (
            daily_forecast_df['vr_agente_kwh'] * daily_forecast_df['pct_cobertura_contratos'] / 100.0).round(2)
        daily_forecast_df['energia_bolsa_kwh'] = (
            daily_forecast_df['vr_agente_kwh'] * daily_forecast_df['pct_exposicion_bolsa'] / 100.0).round(2)
        daily_forecast_df['estado_cobertura'] = (
            "Cubierta (" + daily_forecast_df['pct_cobertura_contratos'].round(1).astype(str)
            + "% Contratos / " + daily_forecast_df['pct_exposicion_bolsa'].round(1).astype(str) + "% Bolsa)")
        daily_forecast_df['modo_cobertura'] = "pronostico"

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
            # % cobertura pronosticado para ESTE mes (no un 0.85 global)
            mes_s = str(row['mes'])
            this_pct = pct_por_mes.get(mes_s, params.pct_cobertura_contratos * 100.0)
            this_bolsa = 100.0 - this_pct
            e_cont_val = round(vr_ag_val * this_pct / 100.0, 2)
            e_bolsa_val = round(vr_ag_val * this_bolsa / 100.0, 2)

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
                "pct_cobertura_contratos": round(this_pct, 2),
                "pct_exposicion_bolsa": round(this_bolsa, 2),
                "modo_cobertura": "pronostico",
                "estado_cobertura": f"Cubierta ({this_pct:.1f}% Contratos / {this_bolsa:.1f}% Bolsa)",
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

        # 5. Unificar registros Históricos + Forecast (normalizar 'mes' a str para orden estable)
        combined_rows = hist_monthly_data + forecast_monthly_rows
        def _sort_key(x):
            mes = x.get('mes', '')
            return (str(mes) if mes is not None else '', x.get('mercado_code', ''))
        combined_rows.sort(key=_sort_key)

        # 6. Recalcular KPIs integrados
        combined_kpis = self.historical_model.calculate_summary_kpis(combined_rows, params)
        combined_kpis['total_registros_forecast'] = len(forecast_monthly_rows)
        combined_kpis['dias_pronosticados'] = len(daily_forecast_df['fecha'].unique()) if not daily_forecast_df.empty else 0

        # Totales acumulados de cobertura (Decimal -> float para evitar TypeError en sums)
        def _to_float(v):
            try:
                return float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                return 0.0
        tot_demanda = sum(_to_float(r.get("vr_agente_kwh", 0)) for r in combined_rows)
        tot_contratos = sum(_to_float(r.get("energia_contratos_kwh", 0)) for r in combined_rows)
        tot_bolsa = sum(_to_float(r.get("energia_bolsa_kwh", 0)) for r in combined_rows)
        combined_kpis['total_demanda_cobertura_kwh'] = tot_demanda
        combined_kpis['total_energia_contratos_kwh'] = tot_contratos
        combined_kpis['total_energia_bolsa_kwh'] = tot_bolsa
        combined_kpis['pct_cobertura_contratos_global'] = (tot_contratos / tot_demanda * 100.0) if tot_demanda > 0 else 85.0
        combined_kpis['pct_exposicion_bolsa_global'] = (tot_bolsa / tot_demanda * 100.0) if tot_demanda > 0 else 15.0

        return daily_forecast_df, combined_rows, combined_kpis
