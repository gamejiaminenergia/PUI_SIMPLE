#!/usr/bin/env python3
"""
Punto de Entrada CLI del Sistema MVC de Informes PUI (Histórico y Pronóstico TimesFM).
Organiza todos los archivos de salida en la carpeta 'output/'.
"""
import argparse
import sys
from models.pui_parameters import PUIParameters
from models.pui_forecast_model import PUIForecastModel
from controllers.report_controller import ReportController

def main():
    parser = argparse.ArgumentParser(
        description="Sistema MVC de Generación de Informes PUI (Pago por Uso de Interconexión - Histórico & Pronóstico TimesFM)"
    )

    parser.add_argument("--config", type=str, default="config/params.yaml", help="Ruta al archivo YAML de configuración")
    parser.add_argument("--mode", type=str, default="both", choices=["historical", "forecast", "both"], help="Modo de informe: historical, forecast o both (default: both)")
    parser.add_argument("--agente", type=str, default=None, help="Código del agente objetivo (overrides config)")
    parser.add_argument("--recaudo", type=float, default=None, help="Factor de recaudo CNIOR (overrides config)")
    parser.add_argument("--format", type=str, default="console,html,csv", help="Formatos separados por coma (console,html,csv)")
    parser.add_argument("--output_dir", type=str, default="output", help="Carpeta contenedora para los reportes y CSVs (default: output)")

    args = parser.parse_args()

    # Cargar modelo de pronóstico con la configuración YAML
    forecast_model = PUIForecastModel(config_path=args.config)
    params = forecast_model.get_forecast_params()

    # Overrides opcionales desde CLI
    if args.agente:
        params.agente_objetivo = args.agente
    if args.recaudo is not None:
        params.factor_recaudo_cnior = args.recaudo

    formats = [f.strip() for f in args.format.split(",")]

    controller = ReportController(forecast_model=forecast_model)
    controller.generate_report(params, formats=formats, output_dir=args.output_dir, mode=args.mode)

if __name__ == "__main__":
    main()
