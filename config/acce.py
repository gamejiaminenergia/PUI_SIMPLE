"""
Contexto y branding del cliente ACCE.

ACCE (Asociación Colombiana de Comercializadores de Energía) contrató este
estudio para evidenciar el impacto negativo del esquema transitorio del PUI
(Prestador de Última Instancia) sobre sus asociados: los Comercializadores No
Integrados con el Operador de Red (CNIOR).

Marco regulatorio de referencia: Resolución CREG 101 121 de 2026 (Artículos 11 y 12).

La lista de Asociados ACCE se lee desde docs/acce.csv (fuente de verdad
proporcionada por el cliente): CODE=0 -> miembro ACCE (comercializador
independiente), CODE=1 -> NO miembro ACCE.
"""
import os
import csv
from typing import Dict

ACCE_FULL_NAME = "Asociación Colombiana de Comercializadores de Energía (ACCE)"
ACCE_SHORT = "ACCE"

RESOLUCION_PUI = "Resolución CREG 101 121 de 2026"
RESOLUCION_FECHA = "30 de julio de 2026"
RESOLUCION_PUBLICACION = "10 de agosto de 2026"

PUI_SIGLA_FULL = "Prestador de Última Instancia (PUI)"
CIOR_FULL = "Comercializador Incumbente del Operador de Red (CIOR)"
CNIOR_FULL = "Comercializador No Integrado con el Operador de Red (CNIOR)"

# Esquema regulatorio: Artículo 11 (traslado de valor tarifado ex-ante) y
# Artículo 12 (obligatoriedad de giro "pague lo facturado, no lo recaudado").
ARTICULO_11 = "Artículo 11 — Traslado del valor del PUI a los usuarios regulados antes del mecanismo competitivo"
ARTICULO_12 = "Artículo 12 — Recaudo y liquidación del costo asumido por el PUI (pague lo facturado, no lo recaudado)"

# Ruta a la fuente de verdad de asociados ACCE.
_ACCE_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "acce.csv")


def _cargar_asociados() -> Dict[str, str]:
    """Carga los Asociados ACCE desde docs/acce.csv (CODE=0 => miembro)."""
    asociados: Dict[str, str] = {}
    if not os.path.isfile(_ACCE_CSV):
        return asociados
    with open(_ACCE_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sigla = (row.get("SIGLA") or "").strip()
            code = (row.get("CODE") or "").strip()
            if not sigla or code != "0":
                continue
            asociados[sigla] = sigla
    return asociados


# Códigos de agentes que son Asociados ACCE (fuente: docs/acce.csv).
# Clave: código en config/params.yaml -> valor de marcado (el código mismo).
ASOCIADOS_ACCE: Dict[str, str] = _cargar_asociados()


def es_asociado_acce(codigo: str) -> bool:
    """Retorna True si el código de agente corresponde a un Asociado ACCE."""
    return codigo in ASOCIADOS_ACCE


def nombre_asociado(codigo: str) -> str:
    """Etiqueta del asociado ACCE (el propio código), o cadena vacía si no es asociado."""
    return ASOCIADOS_ACCE.get(codigo, "")