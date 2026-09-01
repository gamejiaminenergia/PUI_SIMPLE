"""
Módulo de Configuración para el Sistema MVC de Informes PUI.
"""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

@dataclass
class DatabaseSettings:
    """Configuración de conexión a PostgreSQL."""
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "postgres")
    user: str = os.getenv("DB_USER", "postgres")
    password: str = os.getenv("DB_PASSWORD", "postgres")

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class DefaultPUIParameters:
    """Parámetros predeterminados del modelo PUI."""
    rcpui: float = 0.03
    pct_areas_especiales: float = 0.10
    factor_recaudo_cnior: float = 0.92
    cfpui: float = 0.025
    esquema_competitivo: bool = False
    fecha_inicio: str = "2024-01-01"
    fecha_fin: str = "2026-08-27"
    agente_objetivo: str = "ETTC"

DB_SETTINGS = DatabaseSettings()
DEFAULT_PUI_PARAMS = DefaultPUIParameters()
