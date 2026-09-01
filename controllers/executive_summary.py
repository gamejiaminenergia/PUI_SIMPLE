"""
Generador de Resumen Ejecutivo (.md) para el cliente.

Cuando se procesan TODOS los agentes, agrega los KPIs globales y produce
un informe ejecutivo en `docs/resumen_ejecutivo_pui_<TIMESTAMP>.md` que
muestra cómo el mecanismo PUI afecta al mercado en su conjunto:
- Totales agregados de demanda, energía PUI, giros al CIOR, recaudo, sobrecosto
- Ranking de agentes por exposición financiera
- Distribución de cobertura de demanda (contratos vs bolsa)
- Distribución de pérdida por incobrabilidad
- Comparación histórico vs forecast
"""
import os
from datetime import datetime
from typing import List, Dict, Any

from config.logging_config import get_logger

logger = get_logger("controllers.executive_summary")


def _fmt_int(v):
    try:
        return f"{int(round(float(v))):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def _fmt_cop(v):
    """Formatea pesos colombianos: $1.234.567,89 (estilo CO)."""
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "$0"
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1e9:
        # Miles millones (B = 'billones' estilo CO)
        val = abs_n / 1e9
        entero = int(val)
        frac = val - entero
        entero_str = f"{entero:,}".replace(",", ".")
        return f"{sign}${entero_str},{int(round(frac*100)):02d} B"
    if abs_n >= 1e6:
        val = abs_n / 1e6
        entero = int(val)
        frac = val - entero
        entero_str = f"{entero:,}".replace(",", ".")
        return f"{sign}${entero_str},{int(round(frac*10)):01d} MM"
    if abs_n >= 1e3:
        val = abs_n / 1e3
        entero = int(val)
        frac = val - entero
        entero_str = f"{entero:,}".replace(",", ".")
        return f"{sign}${entero_str},{int(round(frac*10)):01d} K"
    return f"{sign}${abs_n:,.0f}".replace(",", ".") if n >= 0 else f"-${abs_n:,.0f}".replace(",", ".")


def _fmt_kwh(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return "0 kWh"
    if abs(n) >= 1e9:
        return f"{n/1e9:,.2f} GWh".replace(",", ".")
    if abs(n) >= 1e6:
        return f"{n/1e6:,.2f} MWh".replace(",", ".")
    return f"{n:,.0f} kWh".replace(",", ".")


def _safe(d, k, default=0.0):
    if not d:
        return default
    v = d.get(k, default)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _percent(part, total):
    if not total or total <= 0:
        return 0.0
    return (part / total) * 100.0


class ExecutiveSummaryGenerator:
    """Genera un .md ejecutivo agregando los KPIs de todos los agentes."""

    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = docs_dir
        os.makedirs(self.docs_dir, exist_ok=True)

    def generate(self, agent_reports: List[Dict[str, Any]], sim_params: Dict[str, Any] = None) -> str:
        """
        Args:
            agent_reports: lista de dicts con keys 'agente', 'kpis', 'output_dir'.
            sim_params: dict con los parámetros de simulación del YAML (opcional).
        Returns:
            Ruta al archivo .md generado.
        """
        logger.info("Generando resumen ejecutivo con %d agentes", len(agent_reports))
        if not agent_reports:
            raise ValueError("agent_reports vacío")

        # ---------- Agregaciones globales ----------
        n = len(agent_reports)
        tot_demanda = sum(_safe(r["kpis"], "total_pui_kwh", 0) for r in agent_reports)
        tot_pui_kwh = sum(_safe(r["kpis"], "total_pui_kwh_energia", 0) for r in agent_reports)
        tot_pui_cop = sum(_safe(r["kpis"], "total_pui_cop", 0) for r in agent_reports)
        tot_egreso = sum(_safe(r["kpis"], "total_egreso_giro_cop", 0) for r in agent_reports)
        tot_recaudo = sum(_safe(r["kpis"], "total_recaudo_cop", 0) for r in agent_reports)
        tot_sobrecosto = sum(_safe(r["kpis"], "sobrecosto_total_cop", 0) for r in agent_reports)
        tot_flujo = sum(_safe(r["kpis"], "flujo_neto_caja_total_cop", 0) for r in agent_reports)
        tot_contratos = sum(_safe(r["kpis"], "total_energia_contratos_kwh", 0) for r in agent_reports)
        tot_bolsa = sum(_safe(r["kpis"], "total_energia_bolsa_kwh", 0) for r in agent_reports)

        pct_cobertura_global = _percent(tot_contratos, tot_contratos + tot_bolsa)
        gap_recaudo = tot_egreso - tot_recaudo  # faltante global
        pct_incob_global = _percent(tot_sobrecosto, tot_egreso) if tot_egreso > 0 else 0.0

        # ---------- Ranking por sobrecosto absoluto (TODOS los agentes) ----------
        ranking = sorted(
            agent_reports,
            key=lambda r: _safe(r["kpis"], "sobrecosto_total_cop", 0),
            reverse=True,
        )
        top_n = len(ranking)  # Sin truncar: TODOS los agentes aparecen

        # ---------- Distribución por niveles de pérdida ----------
        buckets = {"<2%": [], "2-5%": [], "5-10%": [], ">10%": []}
        for r in agent_reports:
            pct = _safe(r["kpis"], "pct_perdida_promedio", 0)
            if pct < 2:
                buckets["<2%"].append(r["agente"])
            elif pct < 5:
                buckets["2-5%"].append(r["agente"])
            elif pct < 10:
                buckets["5-10%"].append(r["agente"])
            else:
                buckets[">10%"].append(r["agente"])

        # Lista COMPLETA de TODOS los agentes (ordenada alfabéticamente) para el anexo
        all_agents_alpha = sorted([r["agente"] for r in agent_reports])

        # ---------- Conteo histórico vs forecast ----------
        n_hist = 0
        n_fcst = 0
        for r in agent_reports:
            tr = _safe(r["kpis"], "total_registros_forecast", 0)
            if tr > 0:
                n_fcst += 1
            else:
                n_hist += 1

        # ---------- Render ----------
        md = self._render_md(
            n=n,
            tot_demanda=tot_demanda,
            tot_pui_kwh=tot_pui_kwh,
            tot_pui_cop=tot_pui_cop,
            tot_egreso=tot_egreso,
            tot_recaudo=tot_recaudo,
            tot_sobrecosto=tot_sobrecosto,
            tot_flujo=tot_flujo,
            tot_contratos=tot_contratos,
            tot_bolsa=tot_bolsa,
            pct_cobertura_global=pct_cobertura_global,
            gap_recaudo=gap_recaudo,
            pct_incob_global=pct_incob_global,
            ranking=ranking,
            top_n=top_n,
            buckets=buckets,
            n_hist=n_hist,
            n_fcst=n_fcst,
            all_agents_alpha=all_agents_alpha,
            sim_params=sim_params or {},
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(self.docs_dir, f"resumen_ejecutivo_pui_{ts}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)

        # También un puntero "último" estable
        latest = os.path.join(self.docs_dir, "resumen_ejecutivo_pui.md")
        with open(latest, "w", encoding="utf-8") as f:
            f.write(md)

        logger.info("Resumen ejecutivo escrito en %s", out_path)
        return out_path

    def _render_md(self, *, n, tot_demanda, tot_pui_kwh, tot_pui_cop,
                   tot_egreso, tot_recaudo, tot_sobrecosto, tot_flujo,
                   tot_contratos, tot_bolsa, pct_cobertura_global,
                   gap_recaudo, pct_incob_global, ranking, top_n,
                   buckets, n_hist, n_fcst, all_agents_alpha, sim_params) -> str:
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        out = []
        out.append("# Resumen Ejecutivo PUI — Análisis Global del Mercado")
        out.append("")
        out.append(f"**Fecha de generación:** {fecha}  ")
        out.append(f"**Agentes analizados:** {n} comercializadores del MEM  ")
        out.append(f"**Marco regulatorio:** Resoluciones CREG 101/2012 y CREG 121/2016  ")
        out.append(f"**Motor de pronóstico:** Google TimesFM 3.0 (modo offline)  ")
        out.append("")
        out.append("> Este documento resume cómo el mecanismo **PUI (Pago por Uso de Interconexión)** "
                   "afecta al conjunto de los **comercializadores independientes** del mercado eléctrico colombiano, "
                   "tanto en el periodo histórico evaluado como en el horizonte de pronóstico.")
        out.append("")
        out.append("### Clasificación de los Agentes Analizados")
        out.append("")
        out.append("Los agentes incluidos en este estudio son **Comercializadores Independientes del MEM "
                   "(Mercado Eléctrico Mayorista)**, también conocidos como **CNIORs** "
                   "(Comercializadores No Integrados al Ofrecimiento de Recursos). "
                   "Estos son agentes que:")
        out.append("")
        out.append("- **No tienen generación propia** — compran toda su energía en el mercado mayorista.")
        out.append("- Son **responsables de girar el PUI** al CIOR (ENEL Colombia S.A. E.S.P.) "
                   "proporcional a su participación en la demanda regulada.")
        out.append("- Asumen el **riesgo de incobrabilidad** del PUI: la diferencia entre lo que "
                   "giran al CIOR y lo que efectivamente recaudan de sus usuarios finales.")
        out.append("- Son los **únicos agentes del MEM que generan sobrecosto por PUI**, ya que "
                   "el CIOR (ENEL) recibe los giros sin asumir pérdida por incobrabilidad.")
        out.append("")
        out.append("> **Nota:** Los agentes verticalmente integrados (generadores-comercializadores como "
                   "EPM, ISAGEN, CEN/ISA) no son sujetos de este análisis porque no están expuestos "
                   "al mismo mecanismo de sobrecosto por PUI.")
        out.append("")

        # ---------- 0. Parámetros de Simulación ----------
        if sim_params:
            out.append("## 0. Parámetros de Simulación (config/params.yaml)")
            out.append("")
            out.append("> Los siguientes parámetros regulatorios y de modelo fueron utilizados para esta simulación:")
            out.append("")
            out.append("| Parámetro | Valor |")
            out.append("|---|---|")
            pui = sim_params.get("pui_params", {})
            out.append(f"| Prima Riesgo Cartera (rcpui) | ${pui.get('rcpui', 0):.3f} / kWh |")
            out.append(f"| % Áreas Especiales | {pui.get('pct_areas_especiales', 0) * 100:.1f}% |")
            out.append(f"| Factor Recaudo CNIOR | {pui.get('factor_recaudo_cnior', 0) * 100:.0f}% |")
            out.append(f"| Cargo Competitivo Fijo (cfpui) | ${pui.get('cfpui', 0):.3f} / kWh |")
            esq = pui.get('esquema_competitivo', False)
            out.append(f"| Esquema Competitivo | {'Sí (Competitivo)' if esq else 'No (Transitorio)'} |")
            out.append(f"| % Cobertura Contratos (fallback) | {pui.get('pct_cobertura_contratos', 0) * 100:.0f}% |")
            out.append(f"| Derivar cobertura desde datos | {'Sí' if pui.get('derive_cobertura_desde_datos', False) else 'No'} |")
            out.append("")
            modelo = sim_params.get("model", {})
            out.append("| Parámetro del Modelo | Valor |")
            out.append("|---|---|")
            out.append(f"| Motor de pronóstico | {modelo.get('name', 'N/A')} |")
            out.append(f"| Backend | {modelo.get('backend', 'N/A')} |")
            out.append(f"| Contexto (días) | {modelo.get('context_len', 'N/A')} |")
            out.append(f"| Horizonte pronóstico (días) | {modelo.get('horizon_len', 'N/A')} |")
            out.append("")
            out.append("| Período de Análisis | Valor |")
            out.append("|---|---|")
            out.append(f"| Fecha inicio entrenamiento | {sim_params.get('train_start_date', 'N/A')} |")
            out.append(f"| Fecha fin entrenamiento | {sim_params.get('train_end_date', 'N/A')} |")
            out.append(f"| Fecha inicio predicción | {sim_params.get('prediction_start_date', 'N/A')} |")
            out.append(f"| Fecha fin predicción | {sim_params.get('prediction_end_date', 'N/A')} |")
            out.append("")

        # ---------- 1. Impacto Global Agregado ----------
        out.append("## 1. Impacto Global del PUI (Agregado de Mercado)")
        out.append("")
        out.append("| Indicador Global | Valor |")
        out.append("|---|---|")
        out.append(f"| Energía PUI totalizada (mercado) | {_fmt_kwh(tot_pui_kwh)} |")
        out.append(f"| Valor total PUI mercado | {_fmt_cop(tot_pui_cop)} |")
        out.append(f"| Giros obligatorios totales al CIOR | {_fmt_cop(tot_egreso)} |")
        out.append(f"| Recaudo real efectivo total | {_fmt_cop(tot_recaudo)} |")
        out.append(f"| **Faltante de caja (gap recaudo)** | **{_fmt_cop(gap_recaudo)}** |")
        out.append(f"| Sobrecosto por incobrabilidad acumulado | {_fmt_cop(tot_sobrecosto)} |")
        out.append(f"| Flujo neto de caja PUI (agregado) | {_fmt_cop(tot_flujo)} |")
        out.append("")
        out.append("**Lectura ejecutiva:**")
        if gap_recaudo > 0:
            out.append(f"- En el agregado, el mercado deja de recuperar "
                       f"**{_fmt_cop(gap_recaudo)}** del PUI facturado. "
                       f"Equivale al **{pct_incob_global:.2f}%** del total girado al operador (CIOR/CNIOR).")
        else:
            out.append("- El recaudo efectivo supera los giros obligatorios en el agregado.")
        if tot_flujo < 0:
            out.append(f"- El flujo neto de caja agregado es **negativo** ({_fmt_cop(tot_flujo)}): "
                       "el sistema, en conjunto, está financiando el PUI con recursos propios.")
        else:
            out.append("- El flujo neto agregado es positivo.")
        out.append("")

        # ---------- 2. Cobertura de Demanda Global ----------
        out.append("## 2. Cobertura de Demanda — Contratos vs Bolsa Spot")
        out.append("")
        out.append("| Fuente de energía | Valor | Participación |")
        out.append("|---|---|---|")
        out.append(f"| Cobertura por contratos bilaterales | {_fmt_kwh(tot_contratos)} | {pct_cobertura_global:.2f}% |")
        out.append(f"| Exposición en bolsa spot | {_fmt_kwh(tot_bolsa)} | {100 - pct_cobertura_global:.2f}% |")
        out.append(f"| **Demanda total agregada (cobertura)** | **{_fmt_kwh(tot_contratos + tot_bolsa)}** | 100% |")
        out.append("")
        out.append("**Lectura ejecutiva:**")
        if pct_cobertura_global >= 80:
            out.append(f"- El mercado está **altamente cubierto por contratos bilaterales** "
                       f"({pct_cobertura_global:.2f}%). La exposición agregada a la bolsa spot es baja, "
                       "lo que reduce el riesgo de variabilidad de precios de compra de energía.")
        elif pct_cobertura_global >= 50:
            out.append(f"- Cobertura de contratos moderada ({pct_cobertura_global:.2f}%). "
                       f"La exposición a bolsa ({100 - pct_cobertura_global:.2f}%) es relevante.")
        else:
            out.append(f"- **Baja cobertura por contratos** ({pct_cobertura_global:.2f}%). "
                       "El mercado está mayoritariamente expuesto a la bolsa spot.")
        out.append("")

        # ---------- 3. Ranking de Exposición Financiera ----------
        out.append(f"## 3. Ranking de Agentes por Sobrecosto Acumulado (Todos los {top_n} Agentes)")
        out.append("")
        out.append("| # | Código | Nombre | Rol PUI | Sobrecosto (COP) | Flujo Neto (COP) | Recaudo (COP) | Pérdida % |")
        out.append("|---|---|---|---|---|---|---|---|")
        for i, r in enumerate(ranking[:top_n], start=1):
            k = r["kpis"]
            nombre = k.get("agente_name", "")
            rol = k.get("rol_pui", "")
            sc = _safe(k, "sobrecosto_total_cop", 0)
            fl = _safe(k, "flujo_neto_caja_total_cop", 0)
            re = _safe(k, "total_recaudo_cop", 0)
            pct = _safe(k, "pct_perdida_promedio", 0)
            out.append(f"| {i} | `{r['agente']}` | {nombre} | {rol} | "
                       f"**{_fmt_cop(sc)}** | {_fmt_cop(fl)} | {_fmt_cop(re)} | {pct:.2f}% |")
        out.append("")
        out.append("**Lectura ejecutiva:**")
        if ranking:
            top1 = ranking[0]
            top1_sc = _safe(top1["kpis"], "sobrecosto_total_cop", 0)
            top1_share = _percent(top1_sc, tot_sobrecosto) if tot_sobrecosto > 0 else 0
            out.append(f"- El agente con mayor sobrecosto (`{top1['agente']}` — "
                       f"{top1['kpis'].get('agente_name', '')}) concentra "
                       f"**{top1_share:.2f}%** del sobrecosto total del mercado.")
            out.append(f"- La totalidad de los {top_n} agentes concentra "
                       f"**{_percent(sum(_safe(r['kpis'], 'sobrecosto_total_cop', 0) for r in ranking[:top_n]), tot_sobrecosto):.2f}%** "
                       f"del sobrecosto total.")
        out.append("")

        # ---------- 4. Distribución de Pérdida por Incobrabilidad ----------
        out.append("## 4. Distribución de Pérdida por Incobrabilidad")
        out.append("")
        out.append("| Rango de pérdida | # Agentes | Agentes |")
        out.append("|---|---|---|")
        for label in ["<2%", "2-5%", "5-10%", ">10%"]:
            agentes = buckets[label]
            agentes_str = ", ".join(f"`{a}`" for a in agentes)
            out.append(f"| {label} | {len(agentes)} | {agentes_str or '—'} |")
        out.append("")
        out.append("**Lectura ejecutiva:**")
        alta = len(buckets[">10%"]) + len(buckets["5-10%"])
        media = len(buckets["2-5%"])
        baja = len(buckets["<2%"])
        out.append(f"- **{alta} agentes** ({_percent(alta, n):.1f}%) tienen pérdida media-alta (≥5%).")
        out.append(f"- **{media} agentes** tienen pérdida moderada (2–5%).")
        out.append(f"- **{baja} agentes** tienen pérdida baja (<2%).")
        out.append("")

        # ---------- 5. Histórico vs Forecast ----------
        out.append("## 5. Cobertura Temporal del Análisis")
        out.append("")
        out.append("| Tipo | # Agentes | % |")
        out.append("|---|---|---|")
        out.append(f"| Con histórico completo | {n_hist} | {_percent(n_hist, n):.1f}% |")
        out.append(f"| Con forecast TimesFM | {n_fcst} | {_percent(n_fcst, n):.1f}% |")
        out.append("")
        out.append("**Lectura ejecutiva:**")
        if n_fcst == n:
            out.append("- **Todos los agentes cuentan con pronóstico diario TimesFM** "
                       "para el horizonte futuro, lo que permite proyectar la trayectoria del PUI "
                       "y anticipar necesidades de caja.")
        else:
            out.append(f"- {n_fcst} de {n} agentes ({_percent(n_fcst, n):.1f}%) tienen "
                       "proyección de forecast con TimesFM. El resto se evalúa sólo con histórico.")
        out.append("")

        # ---------- 6. Conclusiones ----------
        out.append("## 6. Conclusiones Ejecutivas")
        out.append("")
        out.append("1. **El PUI es financieramente deficitario en el agregado:** el mercado, "
                   "en conjunto, deja de recuperar una porción significativa del PUI facturado "
                   "por cuenta de la incobrabilidad de los usuarios finales.")
        out.append("2. **La cobertura por contratos es alta**, lo que reduce el riesgo de "
                   "volatilidad de precios de compra para los comercializadores.")
        out.append("3. **El sobrecosto se concentra:** un número reducido de agentes "
                   "concentra la mayor parte de la pérdida financiera por incobrabilidad. "
                   "Esto sugiere que las acciones de gestión de cartera tienen alto impacto "
                   "si se focalizan en esos agentes.")
        out.append("4. **El forecast permite anticipar el faltante**, lo que habilita "
                   "planes de cobertura de caja y de gestión de recaudo proactivo.")
        out.append("")

        # ---------- 7. Anexo: Listado completo de agentes analizados ----------
        out.append("## 7. Anexo — Agentes Analizados (Listado Completo)")
        out.append("")
        out.append(f"Los {n} siguientes comercializadores del MEM fueron incluidos en este análisis:")
        out.append("")
        # Listado en columnas para que sea escaneable
        agents_per_row = 6
        rows = [all_agents_alpha[i:i + agents_per_row] for i in range(0, len(all_agents_alpha), agents_per_row)]
        # Cabecera de tabla
        header = "| " + " | ".join([f"#{i+1}" for i in range(agents_per_row)]) + " |"
        sep = "|" + "|".join(["---"] * agents_per_row) + "|"
        out.append(header)
        out.append(sep)
        for row in rows:
            padded = row + [""] * (agents_per_row - len(row))
            out.append("| " + " | ".join(f"`{a}`" if a else "—" for a in padded) + " |")
        out.append("")

        # ---------- 8. Ecuaciones y Modelo de Cálculo ----------
        out.append("## 8. Ecuaciones y Modelo de Cálculo")
        out.append("")
        out.append("> Modelo regulatorio descrito en las resoluciones **CREG 101/2012** (Esquema Transitorio) "
                   "y **CREG 121/2016** (Esquema Competitivo). A continuación se presentan las ecuaciones "
                   "en orden lógico de cálculo, de la demanda hasta el sobrecosto final.")
        out.append("")

        out.append("### Paso 0 — Cobertura de Demanda (Contratos vs Bolsa Spot)")
        out.append("")
        out.append("Toda demanda comercial regulada del agente se divide en dos fuentes de compra de energía:")
        out.append("")
        out.append("```")
        out.append("VR_agente = Energía_Contratos + Energía_Bolsa_Spot   [kWh]")
        out.append("")
        out.append("% Cobertura_Contratos = (Energía_Contratos / VR_agente) × 100")
        out.append("% Exposición_Bolsa    = (Energía_Bolsa_Spot / VR_agente) × 100")
        out.append("```")
        out.append("")
        out.append("> **Interpretación:** A mayor % de cobertura por contratos, menor exposición "
                   "a la volatilidad del precio spot (PMEM). El 85% es el fallback cuando la BD "
                   "no expone la variable `CompContEnerReg`.")
        out.append("")

        out.append("### Paso 1 — Demanda Comercial Agente y Mercado")
        out.append("")
        out.append("Variables extraídas de la BD del SIN (tabla `fact_hourly_*`):")
        out.append("")
        out.append("```")
        out.append("VR_agente  = Σ DemaComeReg   [kWh]   ← Demanda Comercial Regulada por agente")
        out.append("VR_mercado = Σ DemaCome      [kWh]   ← Demanda Comercial total del mercado")
        out.append("```")
        out.append("")
        out.append("> **Dato de BD:** `DemaComeReg` (demanda del agente) y `DemaCome` (demanda del mercado). "
                   "Ambas en kilovatios-hora [kWh].")
        out.append("")

        out.append("### Paso 2 — Costo Unitario de la Prestación (CU)")
        out.append("")
        out.append("Precio promedio de los contratos bilaterales del agente:")
        out.append("")
        out.append("```")
        out.append("CU_m-1 = PrecPromCont_m-1   [COP/kWh]")
        out.append("```")
        out.append("")
        out.append("> **Dato de BD:** `PrecPromCont` (Costo Unitario promedio ponderado). "
                   "Se utiliza con rezago de 1 mes (m-1) según la metodología CREG.")
        out.append("")

        out.append("### Paso 3 — Volumen de Áreas Especiales (VPUI)")
        out.append("")
        out.append("Energía que se encuentra en las zonas geográficas donde aplica el PUI, "
                   "calculada con rezago de 1 mes:")
        out.append("")
        out.append("```")
        out.append("VPUI_m-1 = VR_mercado_m-1 × %_áreas_especiales   [kWh]")
        out.append("")
        out.append("Ejemplo: VPUI = VR_mercado × 10%")
        out.append("```")
        out.append("")
        out.append("> **Parámetro:** `%_áreas_especiales = 10%` (configurable en params.yaml). "
                   "Representa el porcentaje de la demanda del mercado que está en zonas especiales.")
        out.append("")

        out.append("### Paso 4 — Tarifas de Incobrabilidad (CRPUI / CFPUI)")
        out.append("")
        out.append("**Esquema Transitorio** (CREG 101/2012) — aplica un cargo por riesgo de cartera:")
        out.append("")
        out.append("```")
        out.append("CRPUI_unitario_m = (rcpui × VPUI_m-1) / (VR_m-1 × CU_m-1)   [COP/kWh]")
        out.append("")
        out.append("Donde:")
        out.append("  rcpui  = Prima de riesgo de cartera (por defecto: $0.030 COP/kWh)")
        out.append("  VPUI   = Volumen de áreas especiales (Paso 3)")
        out.append("  VR_m-1 = Demanda del mercado rezago m-1")
        out.append("  CU_m-1 = Costo unitario rezago m-1")
        out.append("```")
        out.append("")
        out.append("**Esquema Competitivo** (CREG 121/2016) — cargo fijo:")
        out.append("")
        out.append("```")
        out.append("CFPUI = $0.025 COP/kWh   (fijo, no depende de variables del mercado)")
        out.append("```")
        out.append("")
        out.append("> **Nota:** En este estudio se usa el **Esquema Transitorio** por defecto. "
                   "El parámetro `esquema_competitivo = false` en params.yaml controla cuál aplica.")
        out.append("")

        out.append("### Paso 5 — PUI Asignado al Agente")
        out.append("")
        out.append("El PUI total asignado al agente (en energía y en dinero):")
        out.append("")
        out.append("```")
        out.append("PUI_energia_kwh = VR_agente × %_áreas_especiales   [kWh]")
        out.append("PUI_dinero_cop  = PUI_energia_kwh × CRPUI_unitario  [COP]")
        out.append("```")
        out.append("")
        out.append("> **Resultado:** Es el monto total que el agente debe facturar a sus usuarios "
                   "como parte del mecanismo PUI.")
        out.append("")

        out.append("### Paso 6 — Egreso por Giro Obligatorio al CIOR")
        out.append("")
        out.append("Obligación regulada del agente CNIOR de girar el PUI al CIOR (ENEL Colombia), "
                   "proporcional a su participación en la demanda total de CNIORs:")
        out.append("")
        out.append("```")
        out.append("Egreso_Giro_CIOR = Giro_mercado × (VR_CNIOR / VR_CNIORs)   [COP]")
        out.append("")
        out.append("Donde:")
        out.append("  Giro_mercado = Total de giros PUI de todo el mercado")
        out.append("  VR_CNIOR     = Demanda del agente CNIOR específico")
        out.append("  VR_CNIORs    = Demanda total de TODOS los CNIORs")
        out.append("```")
        out.append("")
        out.append("> **Interpretación:** Cada agente CNIOR gira al CIOR según su proporción "
                   "de participación en el mercado regulado.")
        out.append("")

        out.append("### Paso 7 — Recaudo Efectivo")
        out.append("")
        out.append("Monto que el agente logra efectivamente cobrar a sus usuarios finales:")
        out.append("")
        out.append("```")
        out.append("Recaudo_Efectivo = Egreso_Giro_CIOR × Factor_Recaudo   [COP]")
        out.append("")
        out.append("Donde:")
        out.append("  Factor_Recaudo = 92% (por defecto, configurable en params.yaml)")
        out.append("```")
        out.append("")
        out.append("> **Interpretación:** El 8% restante (100% - 92%) representa la "
                   "**incobrabilidad** — el monto que los usuarios finales no pagan.")
        out.append("")

        out.append("### Paso 8 — Sobrecosto por Incobrabilidad (Pérdida Final)")
        out.append("")
        out.append("La pérdida financiera neta del agente por el mecanismo PUI:")
        out.append("")
        out.append("```")
        out.append("Sobrecosto_Incobrabilidad = Egreso_Giro_CIOR - Recaudo_Efectivo   [COP]")
        out.append("")
        out.append("Equivalente a:")
        out.append("Sobrecosto = Egreso_Giro_CIOR × (1 - Factor_Recaudo)   [COP]")
        out.append("```")
        out.append("")
        out.append("> **Interpretación:** Es el dinero que el agente debe pagar al CIOR pero "
                   "no logra recaudar. Lo financia con recursos propios, lo que impacta "
                   "directamente su flujo de caja.")
        out.append("")

        out.append("### Paso 9 — Flujo Neto de Caja")
        out.append("")
        out.append("Balance final del efectivo del agente por concepto PUI:")
        out.append("")
        out.append("```")
        out.append("Flujo_Neto_Caja = Recaudo_Efectivo - Egreso_Giro_CIOR   [COP]")
        out.append("")
        out.append("Si Flujo_Neto < 0 → El agente está financiando la diferencia")
        out.append("Si Flujo_Neto ≥ 0 → El agente cubre su obligación sin pérdida")
        out.append("```")
        out.append("")
        out.append("> **Nota:** En este estudio, el flujo neto es **negativo** para todos los agentes "
                   "porque el factor de recaudo (92%) genera un 8% de pérdida inevitable.")
        out.append("")

        out.append("### Resumen del Flujo de Cálculo")
        out.append("")
        out.append("```")
        out.append("┌─────────────────────────────────────────────────────────────────────┐")
        out.append("│  BD SIN/XM                                                         │")
        out.append("│  ├── DemaComeReg (VR_agente)                                       │")
        out.append("│  ├── DemaCome (VR_mercado)                                         │")
        out.append("│  ├── PrecPromCont (CU)                                              │")
        out.append("│  └── %_áreas_especiales (parámetro)                                │")
        out.append("└──────────────────────┬──────────────────────────────────────────────┘")
        out.append("                       ▼")
        out.append("  Paso 3: VPUI = VR_mercado × 10%                                    │")
        out.append("                       ▼")
        out.append("  Paso 4: CRPUI = (rcpui × VPUI) / (VR × CU)                        │")
        out.append("                       ▼")
        out.append("  Paso 5: PUI = VR_agente × CRPUI                                    │")
        out.append("                       ▼")
        out.append("  Paso 6: Egreso_Giro = Giro_mercado × (VR_CNIOR / VR_CNIORs)        │")
        out.append("                       ▼")
        out.append("  Paso 7: Recaudo = Egreso × 92%                                     │")
        out.append("                       ▼")
        out.append("  Paso 8: Sobrecosto = Egreso - Recaudo                              │")
        out.append("                       ▼")
        out.append("  Paso 9: Flujo_Neto = Recaudo - Egreso  (= -Sobrecosto)             │")
        out.append("```")
        out.append("")

        # ---------- 9. Metodología ----------
        out.append("## 9. Metodología y Fuentes de Datos")
        out.append("")
        out.append("- **Datos fuente:** PostgreSQL (BD del SIN/XM), tabla `fact_hourly_*` y "
                   "dimensiones `dim_*`. Conexión verificada por logs en `logs/pui_YYYYMMDD.log`.")
        out.append("- **Pronóstico:** Google TimesFM 3.0 (modo offline, sin peticiones HTTP tras descarga inicial).")
        out.append("- **Parámetros regulatorios:** CREG 101/2012 y CREG 121/2016.")
        out.append("- **Modelo:** Arquitectura MVC en Python, principios SOLID, "
                   "logger centralizado con rotación diaria en `logs/`.")
        out.append("")

        # ---------- 10. Glosario de Términos ----------
        out.append("## 10. Glosario de Términos")
        out.append("")
        out.append("> Definiciones para facilitar la comprensión del documento a auditores, "
                   "gerentes financieros y áreas comerciales.")
        out.append("")
        out.append("| Término | Sigla | Definición |")
        out.append("|---|---|---|")
        out.append("| **PUI** | PUI | Pago por Uso de Interconexión. Cargo que los comercializadores "
                   "deben pagar por el uso de la red de transmisión nacional. Se calcula sobre "
                   "la demanda comercial de cada agente en áreas especiales.")
        out.append("| **CIOR** | CIOR | Comercializador de Último Recurso Obligado a Recibir. "
                   "Es el agente designado para recibir los giros del PUI de parte de los CNIORs. "
                   "En este estudio, es ENEL Colombia S.A. E.S.P.")
        out.append("| **CNIOR** | CNIOR | Comercializador Independiente No Interconectado al Ofrecimiento de Recursos. "
                   "Son los comercializadores puros del MEM (sin generación propia) que participan en "
                   "este estudio. Compran toda su energía en el mercado mayorista y son responsables "
                   "de girar el PUI al CIOR. Asumen el riesgo de incobrabilidad sobre los giros.")
        out.append("| **Sobrecosto** | — | Diferencia entre el monto total que el agente debe girar al CIOR "
                   "y el monto que efectivamente logra recaudar de sus usuarios. "
                   "Representa la pérdida financiera por incobrabilidad.")
        out.append("| **Flujo Neto de Caja** | — | Resultado de restar los egresos por giros al CIOR menos "
                   "el recaudo efectivo. Si es negativo, el agente está financiando la diferencia.")
        out.append("| **Recaudo Efectivo** | — | Porcentaje del PUI que el agente realmente logra cobrar "
                   "a sus usuarios finales.Depende del factor de recaudo configurado (por defecto 92%).")
        out.append("| **Incobrabilidad** | — | Porcentaje del monto facturado que no se logra cobrar. "
                   "Es la principal causa del sobrecosto en el mecanismo PUI.")
        out.append("| **Cobertura de Demanda** | — | Porcentaje de la demanda de energía del agente que está "
                   "cubierta por contratos bilaterales de compra vs. lo que se compra en bolsa spot. "
                   "A mayor cobertura por contratos, menor exposición a la volatilidad del mercado.")
        out.append("| **Bolsa Spot** | — | Mercado de compra-venta de energía a precio diario (PMEM). "
                   "Es el precio de referencia del mercado eléctrico colombiano.")
        out.append("| **Contratos Bilaterales** | — | Acuerdos privados de compra de energía a precio fijo "
                   "o indexado, que protegen al comercializador de la volatilidad del precio spot.")
        out.append("| **Áreas Especiales** | — | Zonas geográficas del país donde el PUI se aplica sobre "
                   "un porcentaje de la demanda (por defecto 10%). Están definidas por la CREG.")
        out.append("| **rcpui** | rcpui | Prima de riesgo de cartera. Es un cargo adicional (en COP/kWh) "
                   "que compensa el riesgo de no cobro del PUI. Por defecto: $0.030/kWh.")
        out.append("| **cfpui** | cfpui | Cargo fijo competitivo. Componente del PUI que representa "
                   "el costo competitivo de la interconexión. Por defecto: $0.025/kWh.")
        out.append("| **Esquema Competitivo vs Transitorio** | — | El esquema transitorio aplica "
                   "un cargo fijo (cfpui) mientras que el competitivo calcula el cargo según "
                   "la metodología CREG 121/2016. Por defecto: Transitorio.")
        out.append("| **TimesFM** | — | Google TimesFM 3.0. Modelo de inteligencia artificial "
                   "de pronóstico de series temporales utilizado para proyectar la demanda "
                   "y cobertura de energía a futuro.")
        out.append("| **MEM** | MEM | Mercado Eléctrico Mayorista. El mercado mayorista de "
                   "comercialización de energía eléctrica en Colombia, regulado por la CREG.")
        out.append("| **CREG** | CREG | Comisión de Regulación de Energía y Gas. "
                   "Ente regulador del sector eléctrico y gasífero en Colombia.")
        out.append("| **SIN** | SIN | Sistema Interconectado Nacional. La red eléctrica "
                   "nacional de Colombia, administrada por el operador XM.")
        out.append("| **PMEM** | PMEM | Precio Marginal de Energía en el Mercado. "
                   "El precio de referencia diario de la energía en el MEM.")
        out.append("| **Forecast / Pronóstico** | — | Predicción de valores futuros "
                   "basada en modelos estadísticos o de inteligencia artificial. "
                   "En este estudio se usa para proyectar la demanda y cobertura a futuro.")
        out.append("")
        out.append("---")
        out.append("")
        out.append(f"_Documento generado automáticamente. Carpetas individuales por agente en `output/<SIGLA>/`._")
        out.append("")
        return "\n".join(out)


def collect_kpis(agent_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte la salida de ReportController en el formato que espera ExecutiveSummaryGenerator."""
    out = []
    for r in agent_results:
        out.append({
            "agente": r.get("agente", "?"),
            "kpis": r.get("kpis", {}) or {},
            "output_dir": r.get("output_dir", ""),
        })
    return out