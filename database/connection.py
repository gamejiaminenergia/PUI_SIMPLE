"""
Gestor de Conexión a Base de Datos PostgreSQL con Fallback a Generador Sintético.
"""
import os
import logging
from typing import List, Dict, Any
from config.settings import DB_SETTINGS
from database.mock_data import generate_mock_pui_data
from config.logging_config import get_logger

logger = get_logger("database.connection")


class DatabaseConnectionManager:
    """Administra la conexión a PostgreSQL y la ejecución de la consulta PUI."""

    def __init__(self, settings=DB_SETTINGS):
        self.settings = settings
        logger.info("DB host=%s port=%s db=%s user=%s",
                    settings.host, settings.port, settings.database, settings.user)

    def execute_pui_query(self, sql_query: str, params: Any) -> List[Dict[str, Any]]:
        """
        Intenta ejecutar la consulta parametrizada en la base de datos PostgreSQL.
        Si la conexión falla o las tablas no existen, recurre al modo mock sintético.
        """
        # Formatear la consulta con los parámetros del modelo
        formatted_sql = sql_query.format(
            rcpui=params.rcpui,
            pct_areas_especiales=params.pct_areas_especiales,
            factor_recaudo_cnior=params.factor_recaudo_cnior,
            cfpui=params.cfpui,
            esquema_competitivo="TRUE" if params.esquema_competitivo else "FALSE",
            fecha_inicio=params.fecha_inicio,
            fecha_fin=params.fecha_fin,
            agente_objetivo=params.agente_objetivo
        )

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            logger.info("Conectando a PostgreSQL %s:%s/%s ...",
                        self.settings.host, self.settings.port, self.settings.database)
            conn = psycopg2.connect(
                host=self.settings.host,
                port=self.settings.port,
                dbname=self.settings.database,
                user=self.settings.user,
                password=self.settings.password,
                connect_timeout=3
            )
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(formatted_sql)
                records = cur.fetchall()
                conn.close()
                if records:
                    logger.info("PostgreSQL OK: %d filas obtenidas", len(records))
                    return [dict(r) for r in records]
                logger.warning("PostgreSQL OK pero la consulta no devolvió filas.")
        except Exception as e:
            logger.error("Fallo PostgreSQL: %s", e, exc_info=True)
            logger.warning("Usando motor sintético (mock_data).")

        # Fallback a datos mock sintéticos
        mock = generate_mock_pui_data(params)
        logger.warning("Datos MOCK devueltos: %d filas", len(mock))
        return mock
