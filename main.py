#!/usr/bin/env python3
"""
Punto de Entrada CLI del Sistema MVC de Informes PUI (Histórico y Pronóstico TimesFM).
Organiza todos los archivos de salida en la carpeta 'output/' y, si se indica
(--todos), genera los informes de TODOS los agentes configurados en params.yaml,
cada uno en su propia subcarpeta output/<SIGLA>/.
"""
import argparse
import os
import yaml


def main():
    parser = argparse.ArgumentParser(
        description="Sistema MVC de Generación de Informes PUI (Pago por Uso de Interconexión - Histórico & Pronóstico TimesFM)"
    )

    parser.add_argument("--config", type=str, default="config/params.yaml", help="Ruta al archivo YAML de configuración")
    parser.add_argument("--mode", type=str, default="both", choices=["historical", "forecast", "both"], help="Modo de informe: historical, forecast o both (default: both)")
    parser.add_argument("--agente", type=str, default=None, help="Código de UN agente objetivo (overrides config)")
    parser.add_argument("--todos", action="store_true", help="Genera informes para TODOS los agentes definidos en la lista 'agents' del YAML, cada uno en output/<SIGLA>/")
    parser.add_argument("--recaudo", type=float, default=None, help="Factor de recaudo CNIOR (overrides config)")
    parser.add_argument("--format", type=str, default="console,html,csv", help="Formatos separados por coma (console,html,csv)")
    parser.add_argument("--output_dir", type=str, default="output", help="Carpeta contenedora para los reportes y CSVs (default: output)")

    args = parser.parse_args()

    from models.pui_forecast_model import PUIForecastModel
    from controllers.report_controller import ReportController

    # Cargar la configuración YAML para conocer la lista de agentes
    with open(args.config, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}
    agents_list = raw_config.get("agents", [])

    if args.todos and not agents_list:
        print("ERROR: Se solicitó '--todos' pero no se encontró la lista 'agents' en la configuración.")
        raise SystemExit(1)

    # Determinar qué agentes procesar
    if args.todos:
        target_agents = agents_list
    elif args.agente:
        target_agents = [args.agente]
    else:
        target_agents = [raw_config.get("agent", "ETTC")]

    formats = [f.strip() for f in args.format.split(",")]

    print(f"Se procesarán {len(target_agents)} agente(s) en modo '{args.mode.upper()}':")
    for a in target_agents:
        print(f"  - {a}")

    errors = []
    for agente in target_agents:
        print(f"\n{'='*70}\n>>> Procesando agente: {agente}\n{'='*70}")
        try:
            # Instancia fresca por agente para aislar configuración
            forecast_model = PUIForecastModel(config_path=args.config)
            params = forecast_model.get_forecast_params()

            # Overrides
            params.agente_objetivo = agente
            if args.recaudo is not None:
                params.factor_recaudo_cnior = args.recaudo

            # Carpeta independiente por agente: output/<SIGLA>/
            agente_dir = os.path.join(args.output_dir, agente)
            os.makedirs(agente_dir, exist_ok=True)

            controller = ReportController(forecast_model=forecast_model)
            controller.generate_report(
                params,
                formats=formats,
                output_dir=agente_dir,
                mode=args.mode
            )
        except Exception as e:
            import traceback
            print(f"[ERROR] Falló el agente {agente}: {e}")
            traceback.print_exc()
            errors.append(agente)

    print(f"\n{'='*70}\nResumen de ejecución:")
    if errors:
        print(f"  Agentes con error ({len(errors)}): {', '.join(errors)}")
    else:
        print(f"  Todos los agentes ({len(target_agents)}) se procesaron exitosamente.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
