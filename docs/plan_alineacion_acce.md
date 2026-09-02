# Plan de Alineación del Proyecto PUI con ACCE

**Cliente:** Asociación Colombiana de Comercializadores de Energía (ACCE)
**Propósito:** Alinear los entregables del estudio PUI (`docs/resumen_ejecutivo_pui.md` y contenidos de `output/`) con la visión del cliente: evidenciar el **impacto negativo del esquema transitorio del PUI** (Resolución CREG 101 121 de 2026, Artículos 11 y 12) sobre sus asociados, los **CNIOR** (Comercializadores No Integrados con el Operador de Red).

**Fecha del plan:** 2026-09-02
**Estado:** Ejecutado en su totalidad

---

## Contexto del cliente

- ACCE es la agremiación (desde 1999) de las **Comercializadoras Independientes** de energía en Colombia.
- Su visión: "fortalecer la competencia" en los mercados mayorista y minorista y lograr **"un esquema equitativo y de Competencia"**.
- Su rol: **análisis y soporte regulatorio a los miembros** e **interlocución directa con la CREG/gobierno** ("Protegemos y Representamos a nuestros Afiliados").
- Este estudio es un **instrumento de abogacía regulatoria**: evidencia técnica para la interlocución con la CREG.

## Fuentes de referencia

- `docs/acce.md` — análisis del cliente sobre la Resolución 101 121 de 2026 (Artículos 11 y 12).
- `docs/acce.csv` — listado oficial de Asociados ACCE (CODE=0 miembro / CODE=1 no miembro).
- `https://www.acce.com.co/` — misión, visión y contexto de la agremiación.
- `docs/resumen_ejecutivo_pui.md` — entregable principal (generado automáticamente).
- `output/<SIGLA>/` — reportes HTML y CSVs por agente.

## Desalineaciones detectadas (antes del plan)

| Aspecto | Proyecto antes | Visión ACCE |
|---|---|---|
| Marco regulatorio | CREG 101/2012 y 121/2016 | **Resolución 101 121 de 2026** (Art. 11 y 12) |
| Sigla PUI | "Pago por Uso de Interconexión" | **Prestador de Última Instancia** |
| CNIOR | "Comercializador Independiente No Interconectado al Ofrecimiento de Recursos" | **Comercializador No Integrado con el Operador de Red** |
| CIOR | "Comercializador de Último Recurso Obligado a Recibir" | **Comercializador Incumbente del Operador de Red** |
| Narrativa | Técnica/neutral | Demostrar **asimetría y trato discriminatorio** contra CNIOR (Art. 12: "pague lo facturado, no lo recaudado") |
| Escenarios | Solo transitorio | Comparativa transitorio vs mecanismo competitivo definitivo |
| Asociados | Agentes genéricos | **Identificar y marcar a los Asociados ACCE** |

---

## Fases ejecutadas

### Fase 1 — Marco regulatorio y glosario (terminología + nombre ACCE oficial)

Cambios de terminología en código, templates y documentación:

- **Nuevo módulo `config/acce.py`**: branding oficial de ACCE, Resolución 101 121 de 2026, definiciones PUI/CIOR/CNIOR y listado de 14 Asociados ACCE.
- `controllers/executive_summary.py` — marco regulatorio, intro, metodología y glosario.
- `templates/partials/` — `_head.html` (título), `_methodology.html` (marco), `_nav_tabs.html`, `_header.html` (badge), `_styles.html` (estilo badge), `_dashboard.html` (explicación pedagógica).
- `views/csv_view.py` y `controllers/report_controller.py` — mapa de columnas.
- `views/console_view.py` — bug pre-existente corregido (mercado con nombre `None` crasheaba la vista).
- `main.py`, `README.md`, `config/params.yaml` — descripciones y comentarios.

### Fase 2 — Narrativa del resumen ejecutivo alineada a la tesis ACCE

- Sección 6 "Esquema Equitativo vs Trato Asimétrico (Artículos 11 y 12)": caja garantizada del OR vs riesgo 100% en el CNIOR; "pague lo facturado, no lo recaudado"; ausencia de subsidio cruzado; discriminación indirecta.
- Reformulación de lecturas ejecutivas: el dato como evidencia de la afectación negativa.

### Fase 3 — Comparativa transitorio vs mecanismo competitivo definitivo

- Sección 7: sensibilidad del faltante de caja según el reconocimiento del riesgo de cartera (0.92 → 1.00).
- Resultado: el faltante agregado cae de **$9.193 B** (hoy, Art. 12) a $5.745 B / $3.447 B / **$0** según la remuneración del riesgo.
- Mensaje: el sobrecosto **no es un costo inherente del servicio** sino consecuencia del diseño transitorio.

### Fase 4 — Marca de Asociados ACCE

- Lista de asociados leída desde **`docs/acce.csv`** (fuente de verdad del cliente: CODE=0 = miembro ACCE independiente, CODE=1 = no miembro). Total: **19 asociados**.
- Ranking y anexo del resumen ejecutivo con **★**.
- Badge verde "★ Asociado ACCE" + panel en cada reporte HTML por agente.
- Columna "Asociado ACCE (Sí/No)" en los datasets CSV (50 columnas).
- **Nota de corrección:** la versión inicial asumía asociados desde la página web de ACCE; se corrigió al recibir `docs/acce.csv` (fuente autoritativa del cliente).

### Fase 5 — Higiene de datos

- Eliminada carpeta fantasma `output/ASCC~` (62 → 61 agentes).

### Fase 6 — Regeneración y validación

- Regenerados los 61 agentes con datos reales PostgreSQL (no mock), 61/61 sin errores.
- Resumen ejecutivo regenerado con las 12 secciones numeradas.

---

## Entregables resultantes

| Entregable | Ubicación |
|---|---|
| Resumen ejecutivo (último estable) | `docs/resumen_ejecutivo_pui.md` |
| Reportes HTML por agente | `output/<SIGLA>/pui_report_<SIGLA>_unificado.html` |
| Datasets CSV por agente (50 columnas) | `output/<SIGLA>/pui_dataset_unificado.csv` |
| Análisis del cliente | `docs/acce.md` |
| Módulo de branding ACCE | `config/acce.py` |

## Validación final

- `python3 main.py --todos` → **61/61 agentes procesados exitosamente**.
- `python3 main.py --solo-resumen` → resumen regenerado en segundos desde `kpis.json`.
- Verificado: badge ACCE en HTML (asociados vs no asociados), columna ACCE en CSV, secciones 0–12 del resumen.