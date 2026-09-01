"""
Modelo de Datos PUI (Histórico / Core).
Procesa registros y ejecuta cálculos de KPIs para el informe.
"""
import logging
from typing import List, Dict, Any
from models.pui_parameters import PUIParameters

logger = logging.getLogger(__name__)

class PUIModel:
    """Modelo responsable de la extracción y agregación de datos históricos de PUI."""

    def __init__(self, db_connection=None):
        self.db = db_connection

    def get_report_data(self, params: PUIParameters) -> List[Dict[str, Any]]:
        """
        Obtiene los datos del reporte. Si la conexión a BD está activa consulta PostgreSQL,
        de lo contrario utiliza el generador sintético (Mock Data).
        """
        if self.db and hasattr(self.db, "execute_query"):
            try:
                # Consulta SQL Real contra la BD de 9.2M de registros
                query = "SELECT * FROM public.fact_hourly_agente LIMIT 100;"
                return self.db.execute_query(query)
            except Exception as e:
                logger.warning(f"Error consultando BD PostgreSQL ({e}). Se usará el motor sintético.")
        
        # Generación de datos sintéticos según example.sql y CREG 101/2012
        from database.mock_data import generate_mock_pui_data
        return generate_mock_pui_data(params)

    def calculate_summary_kpis(self, data: List[Dict[str, Any]], params: Any = None) -> Dict[str, Any]:
        """
        Calcula indicadores clave de rendimiento (KPIs) y resúmenes ejecutivos
        tanto a nivel global como por mercado y por mes.
        """
        if not data:
            return {}

        first = data[0]
        agente_code = first.get("agente_code", "N/A")
        agente_name = first.get("agente_name", "Agente Desconocido")
        rol_pui = first.get("rol_pui", "N/A")
        cior_name = first.get("cior_name", "")

        total_pui_kwh = sum(float(r.get("pui_energia_kwh", 0)) for r in data)
        total_pui_cop = sum(float(r.get("pui_dinero_cop", 0)) for r in data)
        total_egreso_giro_kwh = sum(float(r.get("egreso_giro_cior", 0)) for r in data)
        total_recaudo_kwh = sum(float(r.get("recaudo_real_agente", 0)) for r in data)
        flujo_neto_caja_total_kwh = sum(float(r.get("flujo_neto_caja_pui", 0)) for r in data)
        sobrecosto_total_kwh = sum(float(r.get("sobrecosto_pui", 0)) for r in data)

        # Convertir a valores monetarios aproximados en COP según precio de contratos (CU)
        total_egreso_giro_cop = sum(float(r.get("egreso_giro_cior", 0)) * float(r.get("precio_prom_contratos_cop_kwh", 0)) for r in data)
        total_recaudo_cop = sum(float(r.get("recaudo_real_agente", 0)) * float(r.get("precio_prom_contratos_cop_kwh", 0)) for r in data)
        flujo_neto_caja_total_cop = sum(float(r.get("flujo_neto_caja_pui", 0)) * float(r.get("precio_prom_contratos_cop_kwh", 0)) for r in data)
        sobrecosto_total_cop = sum(float(r.get("sobrecosto_pui", 0)) * float(r.get("precio_prom_contratos_cop_kwh", 0)) for r in data)

        pct_perdida_promedio = (sobrecosto_total_kwh / total_egreso_giro_kwh * 100.0) if total_egreso_giro_kwh > 0 else 0.0

        mercados_set = set(r.get("mercado_code") for r in data)
        meses_set = set(r.get("mes") for r in data)

        # Agrupamiento por Mercado para ver los de mayor sobrecosto
        mercado_map: Dict[str, Dict[str, Any]] = {}
        for r in data:
            m_code = r.get("mercado_code", "")
            m_name = r.get("mercado_name", m_code)
            if m_code not in mercado_map:
                mercado_map[m_code] = {"code": m_code, "name": m_name, "egreso": 0.0, "sobrecosto": 0.0, "flujo": 0.0}
            cu = float(r.get("precio_prom_contratos_cop_kwh", 0))
            mercado_map[m_code]["egreso"] += float(r.get("egreso_giro_cior", 0)) * cu
            mercado_map[m_code]["sobrecosto"] += float(r.get("sobrecosto_pui", 0)) * cu
            mercado_map[m_code]["flujo"] += float(r.get("flujo_neto_caja_pui", 0)) * cu

        sorted_mercados = sorted(mercado_map.values(), key=lambda x: x["sobrecosto"], reverse=True)

        # Agrupamiento enriquecido por Mes para gráficos de Series de Tiempo (Chart.js)
        mes_map: Dict[str, Dict[str, Any]] = {}
        for r in data:
            mes = str(r.get("mes", ""))
            if mes not in mes_map:
                mes_map[mes] = {
                    "mes": mes,
                    "vr_agente_kwh": 0.0,
                    "energia_contratos_kwh": 0.0,
                    "energia_bolsa_kwh": 0.0,
                    "pct_cobertura_contratos": float(r.get("pct_cobertura_contratos", 85.0)),
                    "pct_exposicion_bolsa": float(r.get("pct_exposicion_bolsa", 15.0)),
                    "cu_cop_kwh": 0.0,
                    "crpui_unitario": 0.0,
                    "cfpui_unitario": 0.0,
                    "pui_energia_kwh": 0.0,
                    "pui_cop": 0.0,
                    "egreso_cop": 0.0,
                    "recaudo_cop": 0.0,
                    "flujo_cop": 0.0,
                    "sobrecosto_cop": 0.0,
                    "es_pronostico": bool(r.get("es_pronostico", False)),
                    "_count": 0
                }
            cu = float(r.get("precio_prom_contratos_cop_kwh", 0))
            mes_map[mes]["vr_agente_kwh"] += float(r.get("vr_agente_kwh", 0))
            mes_map[mes]["energia_contratos_kwh"] += float(r.get("energia_contratos_kwh", 0))
            mes_map[mes]["energia_bolsa_kwh"] += float(r.get("energia_bolsa_kwh", 0))
            mes_map[mes]["cu_cop_kwh"] += cu
            mes_map[mes]["crpui_unitario"] += float(r.get("crpui_unitario", 0))
            mes_map[mes]["cfpui_unitario"] += float(r.get("cfpui_unitario", 0))
            mes_map[mes]["pui_energia_kwh"] += float(r.get("pui_energia_kwh", 0))
            mes_map[mes]["pui_cop"] += float(r.get("pui_dinero_cop", 0))
            mes_map[mes]["egreso_cop"] += float(r.get("egreso_giro_cior", 0)) * cu
            mes_map[mes]["recaudo_cop"] += float(r.get("recaudo_real_agente", 0)) * cu
            mes_map[mes]["flujo_cop"] += float(r.get("flujo_neto_caja_pui", 0)) * cu
            mes_map[mes]["sobrecosto_cop"] += float(r.get("sobrecosto_pui", 0)) * cu
            if bool(r.get("es_pronostico", False)):
                mes_map[mes]["es_pronostico"] = True
            mes_map[mes]["_count"] += 1

        # Promediar precios unitarios por mes
        for m_key, m_val in mes_map.items():
            cnt = max(1, m_val["_count"])
            m_val["cu_cop_kwh"] = round(m_val["cu_cop_kwh"] / cnt, 4)
            m_val["crpui_unitario"] = round(m_val["crpui_unitario"] / cnt, 7)
            m_val["cfpui_unitario"] = round(m_val["cfpui_unitario"] / cnt, 4)

        sorted_tendencia = sorted(mes_map.values(), key=lambda x: x["mes"])

        # ---- Benchmark por Agente (Config) para Gráfica Comparativa ----
        # Calcula el sobrecosto/PUI acumulado de cada agente del config para que
        # el agente del informe pueda compararse contra los demás.
        benchmark_agentes = getattr(params, "agentes_benchmark", None)
        top_agentes_sobrecosto = []
        if benchmark_agentes:
            import dataclasses
            from database import mock_data as mock_mod
            for ag_code in benchmark_agentes:
                try:
                    # Copia superficial de params, solo cambiando el agente objetivo
                    if dataclasses.is_dataclass(params):
                        ag_params = dataclasses.replace(params, agente_objetivo=ag_code)
                    else:
                        ag_params = params
                        ag_params.agente_objetivo = ag_code

                    ag_rows = mock_mod.generate_mock_pui_data(ag_params)
                    if not ag_rows:
                        continue

                    sobrecosto_cop_ag = 0.0
                    pui_cop_ag = 0.0
                    for r in ag_rows:
                        cu_v = float(r.get("precio_prom_contratos_cop_kwh", 0))
                        sobrecosto_cop_ag += float(r.get("sobrecosto_pui", 0)) * cu_v
                        pui_cop_ag += float(r.get("pui_dinero_cop", 0))

                    top_agentes_sobrecosto.append({
                        "code": ag_code,
                        "name": ag_rows[0].get("agente_name", ag_code),
                        "sobrecosto": round(sobrecosto_cop_ag, 2),
                        "pui_cop": round(pui_cop_ag, 2),
                        "es_actual": (ag_code == agente_code)
                    })
                except Exception as e:
                    logger.warning(f"No se pudo calcular benchmark para agente {ag_code}: {e}")

            # Ordenar desc por sobrecosto; el agente actual se resalta
            top_agentes_sobrecosto.sort(key=lambda x: x["sobrecosto"], reverse=True)

        return {
            "total_registros": len(data),
            "agente_code": agente_code,
            "agente_name": agente_name,
            "rol_pui": rol_pui,
            "cior_name": cior_name,
            "total_pui_kwh": total_pui_kwh,
            "total_pui_cop": total_pui_cop,
            "total_egreso_giro_cop": total_egreso_giro_cop,
            "total_recaudo_cop": total_recaudo_cop,
            "flujo_neto_caja_total_cop": flujo_neto_caja_total_cop,
            "sobrecosto_total_cop": sobrecosto_total_cop,
            "pct_perdida_promedio": pct_perdida_promedio,
            "mercados_analizados": len(mercados_set),
            "meses_analizados": len(meses_set),
            "top_mercados_sobrecosto": sorted_mercados,
            "tendencia_mensual": sorted_tendencia,
            "top_agentes_sobrecosto": top_agentes_sobrecosto
        }
