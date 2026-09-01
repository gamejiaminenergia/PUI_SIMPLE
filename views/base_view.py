"""
Interfaz Base para Vistas del Sistema MVC PUI.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.pui_parameters import PUIParameters

class BaseReportView(ABC):
    """Clase base abstracta para generadores de informes."""

    @abstractmethod
    def render(self, data: List[Dict[str, Any]], kpis: Dict[str, Any], params: PUIParameters, output_path: str = None) -> str:
        """
        Renderiza o guarda el informe generado.
        Retorna la representación en string o ruta del archivo generado.
        """
        pass
