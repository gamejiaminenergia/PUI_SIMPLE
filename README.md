# Sistema MVC de Generación de Informes PUI (Pago por Uso de Interconexión & Pronóstico TimesFM)

Sistema modular en Python basado en la arquitectura **Modelo-Vista-Controlador (MVC)** para analizar, auditar y pronosticar la consulta regulatoria del Pago por Uso de Interconexión (PUI) bajo resoluciones **CREG 101/2012** y **CREG 121/2016**.

## 🎯 Características Principales

- **61 agentes preconfigurados** del mercado eléctrico colombiano (MEM)
- **Ejecución por defecto multi-agente**: genera informe de todos los agentes en una sola corrida
- **Arquitectura MVC** limpia con principios SOLID (templates divididos en parciales reutilizables)
- **Pronóstico TimesFM** (Google) a nivel diario → agregación mensual
- **Balance de Cobertura de Demanda**: Contratos bilaterales vs Exposición Bolsa Spot
- **Fórmulas regulatorias** renderizadas con MathJax (LaTeX) y alineadas por `=` para legibilidad
- **Gráficas interactivas Chart.js** con línea punteada separando histórico de forecast
- **Explicaciones en lenguaje natural** en cada gráfica para usuarios no expertos
- **Benchmark comparativo** de sobrecostos PUI por agente del config
- **Salida organizada** en `output/<SIGLA>/` por agente

## 📁 Estructura de Salidas (`output/<SIGLA>/`)

Cada agente genera su propia carpeta independiente:

```
output/
├── AMPC/
│   ├── pui_report_AMPC_unificado.html
│   ├── pui_dataset_unificado.csv
│   ├── pui_auditoria_formulas.csv
│   ├── pui_resumen_mensual.csv
│   └── pui_series_diarias_forecast.csv
├── ASCC/
├── ... (61 carpetas, una por agente)
└── VESC/
```

**Archivos por agente:**

| Archivo | Descripción |
|---------|-------------|
| `pui_report_<SIGLA>_unificado.html` | Informe HTML interactivo con 4 pestañas |
| `pui_dataset_unificado.csv` | Dataset maestro (45+ columnas, HISTÓRICO + FORECAST) |
| `pui_auditoria_formulas.csv` | Desglose granular de variables intermedias (CREG 101/121) |
| `pui_resumen_mensual.csv` | Consolidado mensual ejecutivo |
| `pui_series_diarias_forecast.csv` | Serie diaria pronosticada (TimesFM) |

## 🚀 Uso Rápido (CLI)

```bash
# Genera TODOS los 61 agentes (comportamiento por defecto)
python3 main.py

# Genera solo un agente específico
python3 main.py --agente ASCC

# Equivalente al comportamiento por defecto
python3 main.py --todos

# Opciones adicionales
python3 main.py --format html,csv     # solo HTML y CSV (sin console)
python3 main.py --mode historical      # solo histórico
python3 main.py --mode forecast        # solo pronóstico
python3 main.py --recaudo 0.95         # override factor recaudo
python3 main.py --config mi_config.yaml # configuración personalizada
```

### Opciones CLI

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--agente <COD>` | Un solo agente (override config) | Todos |
| `--todos` | Todos los agentes del config | ✓ (default) |
| `--mode` | `historical`, `forecast`, `both` | `both` |
| `--format` | `console,html,csv` (separado por comas) | `console,html,csv` |
| `--recaudo` | Factor recaudo CNIOR (0.0-1.0) | 0.92 |
| `--output_dir` | Carpeta contenedora | `output` |
| `--config` | Archivo YAML de configuración | `config/params.yaml` |

## ⚙️ Configuración (`config/params.yaml`)

```yaml
# Agentes del estudio (61 agentes del MEM)
agents:
  - ASCC
  - CBNC
  - DEPC
  # ... 58 más

# Fechas
train_start_date: "2024-01-01"
train_end_date: "2026-08-27"
prediction_start_date: "2026-08-28"
prediction_end_date: "2027-02-28"

# Modelo TimesFM
model:
  name: "google/timesfm-1.0-200m"
  backend: "cpu"
  context_len: 512
  horizon_len: 185

# Parámetros regulatorios PUI (CREG 101/2012)
pui_params:
  rcpui: 0.03                    # $/kWh - Prima riesgo cartera CIOR
  pct_areas_especiales: 0.10     # 10% VR en áreas especiales
  factor_recaudo_cnior: 0.92     # 92% recaudo efectivo
  cfpui: 0.025                   # $/kWh - Cargo competitivo fijo
  esquema_competitivo: false     # false = Transitorio (CRPUI)
  pct_cobertura_contratos: 0.85  # 85% contratos / 15% bolsa
```

## 📊 Dashboard Interactivo (HTML)

El informe HTML incluye **5 pestañas** con gráficas explicadas para usuarios no expertos:

| Pestaña | Contenido |
|---------|-----------|
| **📊 Dashboard Ejecutivo** | 5 KPIs en unidades legibles (MM COP, GWh), 4 series temporales + benchmark por agente |
| **🧠 Metodología & CREG** | Fórmulas paso a paso (Paso 0-5) renderizadas con MathJax, alineadas por `=` |
| **📐 Matriz Auditoría** | Tabla buscable con 360 registros y variables intermedias con unidades |
| **📋 Dataset Unificado** | 360 registros, 45+ columnas, filtros en tiempo real |

### Gráficas del Dashboard (con explicaciones integradas)

1. **Cobertura de Demanda** - Contratos (verde) vs Bolsa (amarillo). Más verde = más protección.
2. **Precios CU y Cargos PUI** - CU = costo compra energía; cargos PUI = "seguro" regulado.
3. **Asignación PUI vs Giros/Recaudo** - Barras = asignación; Rojo = obligación girar; Verde = recaudo real.
4. **Sobrecosto y Flujo Neto** - Rojo = pérdida no recuperada; Azul = flujo neto (recaudado - girado).
5. **Benchmark por Agente** - Barra morada = tu agente; Azules = pares. Compara riesgo vs mercado.

> **Todas las gráficas incluyen**: título técnico, subtítulo, línea punteada "Inicio Forecast" y **explicación en lenguaje natural** (bloque azul) para usuarios no expertos.

## 🏗️ Arquitectura del Proyecto

```
PUI_SIMPLE/
├── main.py                    # Punto de entrada CLI (multi-agente por defecto)
├── config/
│   ├── params.yaml            # Configuración central (61 agentes + params)
│   └── settings.py            # Dataclasses de configuración
├── models/
│   ├── pui_parameters.py      # Dataclass PUIParameters
│   ├── pui_model.py           # Modelo histórico + KPIs + benchmark
│   ├── pui_forecast_model.py  # Modelo TimesFM + agregación mensual
│   └── timesfm_predictor.py   # Wrapper Google TimesFM + fallback estadístico
├── views/
│   ├── base_view.py           # Clase base abstracta
│   ├── html_view.py           # Vista HTML (Jinja2 + FileSystemLoader)
│   ├── csv_view.py            # Exportación CSV con headers de negocio
│   └── console_view.py        # Vista terminal
├── controllers/
│   └── report_controller.py   # Orquestador MVC + exportación CSV especializada
├── database/
│   ├── connection.py          # PostgreSQL + fallback mock
│   └── mock_data.py           # Generador sintético con demanda diferenciada por agente
└── templates/
    ├── report_template.html   # Layout orquestador (includes parciales)
    └── partials/
        ├── _head.html         # Meta, fonts, CDNs (Chart.js, MathJax)
        ├── _styles.html       # CSS completo (dark glassmorphism)
        ├── _header.html       # Header + badges
        ├── _nav_tabs.html     # Navegación 4 pestañas
        ├── _dashboard.html    # KPIs + 5 gráficas con explicaciones
        ├── _methodology.html  # 6 pasos CREG con fórmulas alineadas
        ├── _audit_matrix.html # Tabla auditoría completa
        ├── _dataset.html      # Tabla dataset unificado
        ├── _footer.html       # Footer
        ├── _scripts_nav.html  # Navegación tabs + filtros
        ├── _scripts_data.html # Datos Chart.js + fmtCompact + plugin forecast
        ├── _scripts_charts_series.html  # Charts 1-2 (series temporales)
        ├── _scripts_charts_benchmark.html # Charts 3-5
        └── _scripts_formulas.html  # Auto-ajuste MathJax + aligned
```

## 📦 Requisitos

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```txt
pandas>=2.0.0
numpy>=1.24.0
PyYAML>=6.0
Jinja2>=3.1.0
psycopg2-binary>=2.9.0
# timesfm>=0.1.0  # opcional (fallback estadístico si no está)
```

## 🔧 Desarrollo

```bash
# Verificar sintaxis Python
python3 -m py_compile main.py models/*.py views/*.py controllers/*.py database/*.py

# Test rápido un agente
python3 main.py --agente ASCC --format html

# Regenerar todos
python3 main.py --todos
```

## 📝 Notas Técnicas

- **TimesFM opcional**: si `timesfm` no está instalado, usa predictor estadístico con estacionalidad y tendencia
- **PostgreSQL opcional**: si no hay BD accesible, usa `mock_data.py` con demanda diferenciada por agente (hash determinístico del código)
- **MathJax CDN**: renderiza fórmulas LaTeX en la pestaña Metodología (`tex-mml-chtml.js`)
- **Chart.js CDN**: gráficas interactivas con plugin custom para línea "Inicio Forecast"
- **Unidades KPI**: MM COP (millones), GWh (gigavatios-hora) para conciencia situacional
- **Fórmulas alineadas**: entorno `aligned` de LaTeX divide por `=` en renglones separados

## 🤝 Créditos

- **Google TimesFM** - Modelo de pronóstico de series temporales
- **Chart.js** - Gráficas interactivas
- **MathJax** - Renderizado de fórmulas LaTeX
- **CREG 101/2012 & 121/2016** - Marco regulatorio colombiano PUI

---

**Generado con arquitectura MVC, principios SOLID y templates modulares para mantenibilidad a largo plazo.**