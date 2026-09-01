"""
Modelo de Parámetros de Simulación PUI y Cobertura de Demanda.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class PUIParameters:
    """Parámetros de configuración del modelo PUI."""
    rcpui: float = 0.03                  # $/kWh - Prima riesgo de cartera CIOR
    pct_areas_especiales: float = 0.10   # 10% VR en áreas especiales
    factor_recaudo_cnior: float = 0.92   # 92% recaudo efectivo CNIOR
    cfpui: float = 0.025                 # $/kWh - Costo competitivo fijo
    esquema_competitivo: bool = False    # FALSE = CRPUI transitorio, TRUE = CFPUI competitivo
    pct_cobertura_contratos: float = 0.85 # 85% Cobertura de demanda por contratos (15% Exposición Bolsa Spot)
    fecha_inicio: str = "2024-01-01"     # Inicio rango
    fecha_fin: str = "2026-08-27"        # Fin rango
    agente_objetivo: str = "ETTC"        # Código del agente objetivo
    agentes_benchmark: list = None       # Lista de agentes (config) para comparativa PUI

    def validate(self) -> None:
        """Valida que los rangos de parámetros sean matemáticamente correctos."""
        if not (0.0 <= self.factor_recaudo_cnior <= 1.0):
            raise ValueError(f"factor_recaudo_cnior debe estar entre 0.0 y 1.0. Valor actual: {self.factor_recaudo_cnior}")
        if not (0.0 <= self.pct_areas_especiales <= 1.0):
            raise ValueError(f"pct_areas_especiales debe estar entre 0.0 y 1.0. Valor actual: {self.pct_areas_especiales}")
        if not (0.0 <= self.pct_cobertura_contratos <= 1.0):
            raise ValueError(f"pct_cobertura_contratos debe estar entre 0.0 y 1.0. Valor actual: {self.pct_cobertura_contratos}")
        if self.rcpui < 0:
            raise ValueError("rcpui no puede ser negativo.")
        if self.cfpui < 0:
            raise ValueError("cfpui no puede ser negativo.")
