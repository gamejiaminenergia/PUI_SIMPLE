#!/usr/bin/env python3
"""
Punto de Entrada CLI del Sistema MVC de Informes PUI (Histórico y Pronóstico TimesFM).
Organiza todos los archivos de salida en la carpeta 'output/' y, si se indica
(--todos), genera los informes de TODOS los agentes configurados en params.yaml,
cada uno en su propia subcarpeta output/<SIGLA>/.
"""
import argparse
import json
import os
import sys
import yaml

from config.logging_config import setup_logging, get_logger

log = get_logger("main")


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
    parser.add_argument("--solo-resumen", action="store_true", help="Solo regenera el resumen ejecutivo .md cargando KPIs desde output/ (rápido, sin re-procesar agentes)")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Nivel de logging (default: INFO)")

    args = parser.parse_args()
    setup_logging(level=args.log_level)
    log.info("CLI iniciado | args=%s", vars(args))

    # ---------- Modo rápido: solo regenerar resumen ejecutivo ----------
    if args.solo_resumen:
        log.info("Modo --solo-resumen: cargando KPIs desde %s/ ...", args.output_dir)
        with open(args.config, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f) or {}
        from controllers.executive_summary import ExecutiveSummaryGenerator, collect_kpis
        agent_results = []
        if not os.path.isdir(args.output_dir):
            log.error("Carpeta de salida no encontrada: %s", args.output_dir)
            raise SystemExit(1)
        for entry in sorted(os.listdir(args.output_dir)):
            kpis_path = os.path.join(args.output_dir, entry, "kpis.json")
            if os.path.isfile(kpis_path):
                with open(kpis_path, "r", encoding="utf-8") as kf:
                    kpis = json.load(kf)
                agent_results.append({"agente": entry, "kpis": kpis, "output_dir": os.path.join(args.output_dir, entry)})
        if not agent_results:
            log.error("No se encontraron archivos kpis.json en subcarpetas de %s", args.output_dir)
            raise SystemExit(1)
        log.info("KPIs cargados para %d agentes. Generando resumen ejecutivo...", len(agent_results))
        md_path = ExecutiveSummaryGenerator(docs_dir="docs").generate(collect_kpis(agent_results), sim_params=raw_config)
        log.info("Resumen ejecutivo regenerado: %s", md_path)
        raise SystemExit(0)

    from models.pui_forecast_model import PUIForecastModel
    from controllers.report_controller import ReportController

    # Cargar la configuración YAML para conocer la lista de agentes
    with open(args.config, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f) or {}
    agents_list = raw_config.get("agents", [])

    if args.todos and not agents_list:
        log.error("Se solicitó --todos pero no se encontró la lista 'agents' en la configuración.")
        raise SystemExit(1)

    # Determinar qué agentes procesar
    # Por defecto (sin --agente ni --todos) se procesan TODOS los agentes de la lista.
    if args.agente:
        target_agents = [args.agente]
    elif agents_list:
        target_agents = agents_list
    else:
        target_agents = [raw_config.get("agent", "ETTC")]

    formats = [f.strip() for f in args.format.split(",")]
    log.info("Agentes objetivo=%s | mode=%s | formatos=%s", target_agents, args.mode, formats)

    agent_results = []
    errors = []
    for agente in target_agents:
        log.info("=" * 60)
        log.info("Procesando agente: %s", agente)
        log.info("=" * 60)
        try:
            # Instancia fresca por agente para aislar configuración
            forecast_model = PUIForecastModel(config_path=args.config)
            params = forecast_model.get_forecast_params()
            log.debug("Parámetros cargados: %s", params)

            # Overrides
            params.agente_objetivo = agente
            if args.recaudo is not None:
                log.info("Override factor_recaudo_cnior: %s -> %s", params.factor_recaudo_cnior, args.recaudo)
                params.factor_recaudo_cnior = args.recaudo

            # Carpeta independiente por agente: output/<SIGLA>/
            agente_dir = os.path.join(args.output_dir, agente)
            os.makedirs(agente_dir, exist_ok=True)
            log.info("Carpeta de salida: %s", agente_dir)

            controller = ReportController(forecast_model=forecast_model)
            result = controller.generate_report(
                params,
                formats=formats,
                output_dir=agente_dir,
                mode=args.mode
            )
            agent_results.append({
                "agente": agente,
                "kpis": result.get("kpis", {}),
                "output_dir": agente_dir,
            })
            # Guardar KPIs a JSON para regeneración rápida del resumen ejecutivo
            kpis_path = os.path.join(agente_dir, "kpis.json")
            with open(kpis_path, "w", encoding="utf-8") as kf:
                json.dump(result.get("kpis", {}), kf, ensure_ascii=False, indent=2)
            log.info("Agente %s completado OK | KPIs guardados en %s", agente, kpis_path)
        except Exception as e:
            import traceback
            log.error("Falló el agente %s: %s", agente, e, exc_info=True)
            errors.append(agente)

    # Resumen ejecutivo agregado si se procesaron varios agentes y no falló todo
    if len(agent_results) >= 2:
        try:
            from controllers.executive_summary import ExecutiveSummaryGenerator, collect_kpis
            md_path = ExecutiveSummaryGenerator(docs_dir="docs").generate(collect_kpis(agent_results), sim_params=raw_config)
            log.info("Resumen ejecutivo global: %s", md_path)
        except Exception as e:
            log.error("No se pudo generar el resumen ejecutivo: %s", e, exc_info=True)

    log.info("=" * 60)
    log.info("Resumen de ejecución")
    if errors:
        log.error("Agentes con error (%d): %s", len(errors), ", ".join(errors))
        sys.exit(1)
    else:
        log.info("Todos los agentes (%d) procesados exitosamente.", len(target_agents))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
