"""
Tests de verificación del Plan de Cobertura de Contratos (sección 6 del PLAN).
Validan que el sistema ya NO use el 0.85 fijo y use datos reales/pronosticados.
"""
import unittest

from models.pui_forecast_model import PUIForecastModel
from models.pui_parameters import PUIParameters


class TestCoberturaPlan(unittest.TestCase):
    """Tests basados en los objetivos del PLAN_cobertura_contratos.md"""

    def setUp(self):
        self.forecast_model = PUIForecastModel("config/params.yaml")
        self.params = self.forecast_model.get_forecast_params()

    def test_f1_cobertura_historica_no_es_85_fijo(self):
        """F1: La cobertura histórica varía por mes (no es 85% estacionario)."""
        hist = self.forecast_model.historical_model.get_report_data(self.params)
        pcts = set()
        for r in hist:
            pct = r.get("pct_cobertura_contratos")
            if pct is not None:
                pcts.add(round(float(pct), 2))
        # Debe haber al menos 3 valores distintos (mock realista genera variación)
        self.assertGreaterEqual(
            len(pcts), 3,
            f"La cobertura histórica debe variar por mes. Valores únicos: {sorted(pcts)}"
        )
        # El viejo comportamiento: TODOS los meses = 85.0 (un solo valor)
        # Ahora debe haber más de un valor (no estacionario)
        self.assertNotEqual(
            len(pcts), 1, "Cobertura no debe ser estacionaria (un solo valor)"
        )
        # Y ese único valor no debe ser 85.0 (el hardcodeado)
        if len(pcts) == 1:
            self.assertNotEqual(list(pcts)[0], 85.0)

    def test_f2_cobertura_varia_por_agente(self):
        """F2: En modo --todos, la cobertura varía por agente (no todos 85%)."""
        agentes = ["ETTC", "ENDC", "NRCC", "EPMC"]
        pcts_por_agente = {}
        for ag in agentes:
            self.params.agente_objetivo = ag
            hist = self.forecast_model.historical_model.get_report_data(self.params)
            # Promedio de cobertura del agente en su histórico
            avg_pct = sum(
                float(r.get("pct_cobertura_contratos", 0))
                for r in hist if r.get("pct_cobertura_contratos") is not None
            ) / len(hist)
            pcts_por_agente[ag] = round(avg_pct, 2)
        
        # Deben ser distintos entre sí (mock usa hash determinístico por agente)
        self.assertEqual(
            len(set(pcts_por_agente.values())), len(pcts_por_agente),
            f"Cobertura debe variar por agente: {pcts_por_agente}"
        )

    def test_f3_forecast_proviene_de_timesfm(self):
        """F3: El forecast de cobertura viene de TimesFM (no del parámetro fix)."""
        hist = self.forecast_model.historical_model.get_report_data(self.params)
        pred_start = "2026-08-28"
        pred_end = "2027-02-28"
        
        pct_por_mes = self.forecast_model._pronosticar_cobertura(hist, pred_start, pred_end)
        
        # Debe haber al menos 2 valores distintos (TimesFM pronostica tendencia)
        self.assertGreaterEqual(
            len(set(pct_por_mes.values())), 2,
            f"Forecast de cobertura debe variar por mes: {pct_por_mes}"
        )
        # Verificar que NO usa el fallback 85% (que sería plano)
        fallback_85 = all(abs(v - 85.0) < 0.01 for v in pct_por_mes.values())
        self.assertFalse(
            fallback_85,
            "El forecast no debe ser 85.0% plano (eso es el parámetro de reserva)"
        )

    def test_f4_mock_varia_mes_a_mes(self):
        """F4: En modo mock, pct_cobertura_contratos varía mes a mes (no constante)."""
        p = PUIParameters(fecha_inicio="2024-01-01", fecha_fin="2025-12-31", agente_objetivo="ETTC")
        from database.mock_data import generate_mock_pui_data
        rows = generate_mock_pui_data(p)
        
        # Agrupar por mes y ver que la cobertura cambia
        pcts_mensuales = {}
        for r in rows:
            mes = r.get("mes")
            pct = r.get("pct_cobertura_contratos")
            if mes and pct is not None:
                if mes not in pcts_mensuales:
                    pcts_mensuales[mes] = round(float(pct), 2)
        
        self.assertGreaterEqual(
            len(set(pcts_mensuales.values())), 5,
            f"Mock debe generar cobertura variable por mes: {pcts_mensuales}"
        )
        # Verificar acotado [55, 100] (rango realista del plan)
        for v in pcts_mensuales.values():
            self.assertTrue(55 <= v <= 100, f"Cobertura {v}% fuera de rango [55,100]")

    def test_derive_flag_activo(self):
        """El flag derive_cobertura_desde_datos está activo por defecto."""
        self.assertTrue(
            getattr(self.params, "derive_cobertura_desde_datos", True),
            "derive_cobertura_desde_datos debe ser True"
        )

    def test_fallback_param_disponible(self):
        """El parámetro de reserva pct_cobertura_contratos existe y es válido."""
        fallback = getattr(self.params, "pct_cobertura_contratos", None)
        self.assertIsNotNone(fallback)
        self.assertGreater(fallback, 0.0)
        self.assertLessEqual(fallback, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)