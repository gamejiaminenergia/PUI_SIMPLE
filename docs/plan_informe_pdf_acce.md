# Plan: Informe PDF del PUI para ACCE

## Objetivo

Generar un **PDF institucional** para el cliente **ACCE** (Asociación Colombiana de Comercializadores de Energía) sobre el análisis del **PUI** (Prestador de Última Instancia), alineado con la tesis del cliente (`docs/acce.md`), respaldado **por los datos y la lógica ya calculados** en `controllers/executive_summary.py`, `controllers/report_controller.py` y los artefactos de `output/<SIGLA>/`, con branding según `docs/acce_pdf_report_spec.json` y `docs/logo.png`.

## Stack (según solicitud del usuario)

- **Jinja2** → plantilla HTML
- **WeasyPrint** → render PDF (soporta `@page`, `counter(page/pages)`)
- **Plotly + kaleido** → exportar gráficas como **SVG** (no PNG)
- Datos: pandas/numpy (ya en venv)

> **Dependencias a instalar** (no están en el venv): `plotly>=5.20`, `kaleido>=0.2.1`, `WeasyPrint>=60.0`. Se agregarán a `requirements.txt`.

---

## CÓMO SE RESPALDA LA VISIÓN DEL CLIENTE CON EL CÓDIGO EXISTENTE

La tesis ACCE (asimetría/trato discriminatorio contra CNIOR; "pague lo facturado, no lo recaudado") **ya está calculada y auditada** en el proyecto. El PDF **no reinventa nada**: reutiliza los mismos campos computados y el mismo método de agregación que el resumen ejecutivo, de modo que los números del PDF **coinciden exactamente** con la simulación.

### 1. Agregación global (idéntica a `ExecutiveSummaryGenerator.generate()`)

`build_pdf.py` leerá los **61 `output/<SIGLA>/kpis.json`** y recalculará los totales con la **misma lógica** que `executive_summary.py:111-123`:
- `tot_egreso`, `tot_recaudo`, `tot_sobrecosto`, `tot_flujo`, `gap_recaudo`, `pct_incob_global`, `pct_cobertura_global`.
- → Respalda **"Faltante de caja $9.235,84B = 8% del giro"** (sección "Impacto global").

### 2. Ranking de agentes y asociados ★ (idéntico a `executive_summary.py:319-353` + `config/acce.py:es_asociado_acce`)

- Mismo ranking por `sobrecosto_total_cop` (top 10-20 en tabla) y marcado ★ de los **19 Asociados ACCE** desde `docs/acce.csv` (`config/acce.py`).
- → Respalda **"el sobrecosto se concentra; los CNIOR (asociados) son los más afectados"**.

### 3. Gráficas desde **datos reales generados** (no solo del markdown)

- **Trayectoria mensual histórica+forecast**: agregar `tendencia_mensual` de los 61 kpis → línea de sobrecosto/flujo. Refleja el despegue del faltante en el horizonte TimesFM.
- **Cobertura contratos vs bolsa**: agregar `total_energia_contratos_kwh` / `total_energia_bolsa_kwh` → donut (88.76% / 11.24%).
- **Ranking horizontal top 10** por sobrecosto.
- **Escenarios transitorio vs competitivo**: mismos 4 escenarios de `executive_summary.py:427-436` (92%→95%→97%→100% ⇒ faltante $9.235B→$5.772B→$3.463B→$0) → **línea/área de reducción del faltante**. Es el argumento central: *"el sobrecosto no es un costo inherente, es un diseño transitorio"*.
- **Distribución por rango de pérdida** (buckets `<2, 2-5, 5-10, >10%` de `executive_summary.py:134-144`).

### 4. Mapa coroplético de Colombia por departamento

- Datos: `top_mercados_sobrecosto` de cada kpis.json (mercados como BOGOTA-CUNDINAMARCA, ANTIOQUIA, VALLE, CARIBE…). Normalizar los 34 nombres a departamentos, agregar sobrecosto por departamento y colorear el choropleth.
- → Respalda visualmente **"dónde se concentra la incobrabilidad"** (zonas de riesgo de cartera / áreas especiales).

### 5. Trazabilidad de fórmulas (auditoría) → explicaciones del PDF

- Reutilizar el **flujo de cálculo Paso 0→9** documentado en `executive_summary.py:493-670` (VR, VPUI, CRPUI, giro CIOR, recaudo 92%, sobrecosto = egreso×8%) para los bloques de **explicación / tips / warnings** del informe, en lenguaje regulatorio ACCE.
- Los `pui_auditoria_formulas.csv` por agente permiten, si se quiere, citar un ejemplo numérico real de auditoría.

---

## Estructura de archivos a crear

```
scripts/
  build_pdf.py            # Carga 61 kpis.json → recalcula agregados (misma lógica que resumen) → renderiza PDF
  make_charts.py          # Plotly→SVG (paleta ACCE): trayectoria, donut, ranking, escenarios, distribución
  make_map.py             # Choropleth Colombia por departamento → SVG
templates/
  report_pui_acce.html.jinja2
static/
  css/report_acce.css
  fonts/inter.ttf
  img/logo.png
  geo/colombia_departamentos.geojson   # descargar (internet OK)
assets_svg/                            # SVGs generados
docs/plan_informe_pdf_acce.md          # ESTE plan
```

## Secciones del PDF (alineadas a resumen + tesis ACCE + datos calculados)

1. **Portada** — logo ACCE, título, cliente, fecha, línea naranja (`@page :first` sin header/footer).
2. **Resumen ejecutivo** — tarjetas KPI: Faltante $9.235B, 8% incobrabilidad, cobertura 88.76%, 61 agentes, 19 asociados ★.
3. **Contexto regulatorio** (`acce.md`): Art. 11 y 12, asimetrías CNIOR (caja garantizada OR vs riesgo 100% CNIOR).
4. **Impacto global del mercado** — tabla agregada + barras giros/recaudo/sobrecosto.
5. **Cobertura de demanda** — tabla + donut contratos/bolsa.
6. **Ranking por sobrecosto** — tabla top ~20 con ★ + barra horizontal top 10.
7. **Mapa de Colombia** — choropleth por departamento.
8. **Trayectoria temporal** — línea mensual (histórico + forecast TimesFM).
9. **Transitorio vs competitivo** — tabla de escenarios + gráfica de reducción del faltante (mensaje clave ACCE).
10. **Distribución de pérdida por incobrabilidad** — barras por rango.
11. **Conclusiones / recomendaciones** — checklist de posición ACCE ante CREG.
12. **Anexos** — metodología (Paso 0-9), glosario, listado de 61 agentes con ★.

## Componentes reutilizables (`acce_pdf_report_spec.json`)

`kpi_card` (borde superior naranja), `data_table` (header #1F2A33, filas alt #FBEFE4), `callout_box` (fondo #F4F4F2, borde izq 3pt naranja) para **tips/explicaciones**, `section_divider` naranja. **Contenido**: tablas, KPIs, tips, warnings, explicaciones, gráficas SVG, mapa.

## Paleta (verificar del logo con PIL en ejecución)

Naranja `#E8720C` · Grafito `#1F2A33` · Gris claro `#F4F4F2` · Alt fila `#FBEFE4` · Verde `#2E7D32` · Rojo `#C62828`.

## Notas técnicas WeasyPrint

`@page` Letter, márgenes 25/20/18/18mm; `@page :first` sin header/footer; running header (logo izq + título/fecha der); footer "Página X de Y"; `orphans/widows:3`; `break-inside:avoid` por fila; `Inter` .ttf con `@font-face`.

## Pasos de ejecución

1. Crear estructura de carpetas.
2. Instalar deps y agregarlas a `requirements.txt`.
3. `make_charts.py` + `make_map.py` (SVG).
4. `build_pdf.py` (cargar kpis.json → agregar con lógica del resumen → Jinja2 → WeasyPrint).
5. Plantilla + CSS + logo + fuentes.
6. **Validación**: portada vs internas, corte de tabla larga, numeración, y **verificación de que los agregados del PDF coinciden con `resumen_ejecutivo_pui.md`** ($9.235,84B, 8%, 88.76%).
7. Extraer hex reales del logo y confirmar.

## Entregable

`pdf/informe_pui_acce.pdf` (carpeta dedicada `pdf/` en la raíz del proyecto, aislada de `docs/`), con números **idénticos a la simulación** que ya validó el cliente.

---

**Estado:** Pendiente de aprobación de ejecución.
