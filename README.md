# Sistema MVC de Generación de Informes PUI (Prestador de Última Instancia & Pronóstico TimesFM)

Sistema modular en Python basado en la arquitectura **Modelo-Vista-Controlador (MVC)** para analizar, auditar y pronosticar el impacto del mecanismo **PUI (Prestador de Última Instancia)** bajo la **Resolución CREG 101 121 de 2026** (Artículos 11 y 12).

Estudio encargado por la **Asociación Colombiana de Comercializadores de Energía (ACCE)** para evidenciar el impacto negativo del esquema transitorio sobre sus asociados, los **Comercializadores No Integrados con el Operador de Red (CNIOR)**.

## 🎯 Características Principales

- **61 agentes preconfigurados** del mercado eléctrico colombiano (MEM)
- **Ejecución por defecto multi-agente**: genera informe de todos los agentes en una sola corrida
- **Arquitectura MVC** limpia con principios SOLID (templates divididos en parciales reutilizables)
- **Pronóstico TimesFM** (Google) a nivel diario → agregación mensual — **modo offline** (sin peticiones a HuggingFace tras la primera descarga)
- **Datos reales PostgreSQL** del SIN (XM) — conexión verificada con logs
- **Balance de Cobertura de Demanda**: Contratos bilaterales vs Exposición Bolsa Spot
- **Fórmulas regulatorias** renderizadas con MathJax (LaTeX) y alineadas por `=` para legibilidad
- **Gráficas interactivas Chart.js** con línea punteada separando histórico de forecast
- **Explicaciones en lenguaje natural** en cada gráfica para usuarios no expertos
- **Benchmark comparativo** de sobrecostos PUI por agente del config
- **Sistema de logs robusto** (`logs/`) con rotación diaria y archivo de errores
- **Salida organizada** en `output/<SIGLA>/` por agente
- **Marca de Asociados ACCE** en reportes, ranking y datasets

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

### Resumen Ejecutivo Global (`docs/`)

Cuando se procesan **2+ agentes** (con `--todos` o por defecto), el sistema genera automáticamente:

- `docs/resumen_ejecutivo_pui_<TIMESTAMP>.md` — informe markdown con timestamp
- `docs/resumen_ejecutivo_pui.md` — copia "último" estable

Contiene: impacto agregado del PUI, cobertura global de demanda (contratos vs bolsa), ranking completo de agentes por sobrecosto con marca de Asociados ACCE, distribución de pérdida por incobrabilidad, narrativa de asimetría regulatoria (Artículos 11 y 12), comparativa transitorio vs mecanismo competitivo, cobertura histórico/forecast, conclusiones ejecutivas y metodología. **Listo para compartir con el cliente (ACCE).**

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
python3 main.py --log-level DEBUG      # logs verbosos para depuración
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
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | `INFO` |

## 🗄️ Configuración de Base de Datos

El sistema lee credenciales de PostgreSQL desde el archivo `.env` (copia `.env.example`):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres        # BD del SIN/XM
DB_PASSWORD=postgres
```

El sistema **carga automáticamente** el `.env` y muestra en logs la cadena de conexión, filas obtenidas y, en caso de fallo, recae a datos mock con una advertencia explícita. Si ves el warning `Datos MOCK devueltos` en `logs/pui_errors.log`, **tu consulta no está usando datos reales**.

## 📋 Sistema de Logs (`logs/`)

Cada ejecución genera dos archivos con rotación automática:

```
logs/
├── pui_YYYYMMDD.log          # log completo (rotación 14 días)
└── pui_errors.log            # solo errores con traceback completo (30 días)
```

Formato: `TIMESTAMP | NIVEL | MÓDULO | MENSAJE`. Librerías ruidosas (`httpx`, `huggingface_hub`, `transformers`) se silencian automáticamente. La variable `HF_HUB_OFFLINE=1` se fuerza para evitar peticiones HTTP a HuggingFace en cada ejecución.

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

# Parámetros regulatorios PUI (Res. 101 121 de 2026)
pui_params:
  rcpui: 0.03                    # $/kWh - Prima riesgo cartera CIOR
  pct_areas_especiales: 0.10     # 10% VR en áreas especiales
  factor_recaudo_cnior: 0.92     # 92% recaudo efectivo
  cfpui: 0.025                   # $/kWh - Cargo competitivo fijo
  esquema_competitivo: false     # false = Transitorio (CRPUI)
  pct_cobertura_contratos: 0.85  # 85% contratos / 15% bolsa
```

## 📊 Dashboard Interactivo (HTML)

El informe HTML incluye **4 pestañas** con gráficas explicadas para usuarios no expertos:

| Pestaña | Contenido |
|---------|-----------|
| **📊 Dashboard Ejecutivo** | 5 KPIs en unidades legibles (MM COP, GWh), 6 series temporales + benchmark por agente |
| **🧠 Metodología & CREG** | Fórmulas paso a paso (Paso 0-5) renderizadas con MathJax, alineadas por `=` |
| **📐 Matriz Auditoría** | Tabla buscable con 360 registros y variables intermedias con unidades |
| **📋 Dataset Unificado** | 360 registros, 45+ columnas, filtros en tiempo real |

### Gráficas del Dashboard (con explicaciones integradas)

1. **Cobertura de Demanda** - Contratos (verde) vs Bolsa (amarillo) vs VR (línea azul). Más verde = más protección.
2. **Precios CU y Cargos PUI** - CU (verde) = costo compra energía; CRPUI/CFPUI (líneas derechas) = "seguro" regulado en COP/MM kWh.
3. **Asignación PUI vs Giros/Recaudo** - Barras = asignación; Rojo = obligación girar; Verde = recaudo real.
4. **Sobrecosto y Flujo Neto** - Rojo = pérdida no recuperada; Azul = flujo neto (recaudado - girado).
5. **Cobertura y Demanda** - Resumen ejecutivo contratos vs bolsa vs demanda total.
6. **Rendimiento Financiero** - CU m-1 (verde), Sobrecosto (rojo punteado), Recaudo Real (morado punteado).
7. **Benchmark por Agente** - Barra morada = tu agente; Azules = pares. Compara riesgo vs mercado.

> **Todas las gráficas incluyen**: título técnico, subtítulo, línea punteada "Inicio Forecast" y **explicación en lenguaje natural** (bloque azul) para usuarios no expertos.

## 🏗️ Arquitectura del Proyecto

```
PUI_SIMPLE/
├── main.py                    # Punto de entrada CLI (multi-agente por defecto)
├── .env                       # Credenciales PostgreSQL (auto-cargado)
├── config/
│   ├── params.yaml            # Configuración central (61 agentes + params)
│   ├── settings.py            # Dataclasses + load_dotenv()
│   └── logging_config.py      # Logging centralizado (logs/ con rotación)
├── models/
│   ├── pui_parameters.py      # Dataclass PUIParameters
│   ├── pui_model.py           # Modelo histórico + KPIs + benchmark
│   ├── pui_forecast_model.py  # Modelo TimesFM + agregación mensual
│   └── timesfm_predictor.py   # Wrapper TimesFM (modo offline) + fallback
├── views/
│   ├── base_view.py           # Clase base abstracta
│   ├── html_view.py           # Vista HTML + manejo de Decimal/date
│   ├── csv_view.py            # Exportación CSV con headers de negocio
│   └── console_view.py        # Vista terminal
├── controllers/
│   └── report_controller.py   # Orquestador MVC + exportación CSV especializada
├── database/
│   ├── connection.py          # PostgreSQL + fallback mock (con logs explícitos)
│   └── mock_data.py           # Generador sintético con demanda diferenciada por agente
├── logs/                      # Generados automáticamente
│   ├── pui_YYYYMMDD.log       # Log completo (rotación 14 días)
│   └── pui_errors.log         # Solo errores con traceback (30 días)
└── templates/
    ├── report_template.html   # Layout orquestador (includes parciales)
    └── partials/
        ├── _head.html         # Meta, fonts, CDNs (Chart.js, MathJax)
        ├── _styles.html       # CSS completo (dark glassmorphism)
        ├── _header.html       # Header + badges
        ├── _nav_tabs.html     # Navegación 4 pestañas
        ├── _dashboard.html    # KPIs + 6 gráficas con explicaciones pedagógicas
        ├── _methodology.html  # 6 pasos CREG con fórmulas alineadas
        ├── _audit_matrix.html # Tabla auditoría completa
        ├── _dataset.html      # Tabla dataset unificado
        ├── _footer.html       # Footer
        ├── _scripts_nav.html  # Navegación tabs + filtros
        ├── _scripts_data.html # Datos Chart.js + fmtCompact + plugin forecast
        ├── _scripts_charts_series.html  # Charts series temporales
        ├── _scripts_charts_benchmark.html # Chart benchmark
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
python-dotenv>=1.0.0
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

- **TimesFM offline**: el sistema fuerza `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` y `HF_DATASETS_OFFLINE=1`. El modelo se descarga **una sola vez** en `~/.cache/huggingface/hub/` y las siguientes ejecuciones no hacen HTTP. Funciona sin internet.
- **TimesFM opcional**: si `timesfm` no está instalado, usa predictor estadístico con estacionalidad y tendencia
- **PostgreSQL opcional**: si no hay BD accesible, usa `mock_data.py` con demanda diferenciada por agente (hash determinístico del código). **El log advertirá explícitamente** cuando se use fallback mock.
- **Manejo de tipos Decimal/date**: psycopg2 devuelve `Decimal` y `date`; el view HTML y CSV normalizan automáticamente para evitar errores en Jinja2 (`r.mes[:7]`, multiplicaciones, etc.)
- **CRPUI/CFPUI micro**: la fórmula regulatoria produce ratios ~1e-5 COP/kWh. El chart `chartPricesAndTariffs` los escala ×10⁶ y los muestra como `COP/MM kWh` con tooltip que revela el valor real.
- **MathJax CDN**: renderiza fórmulas LaTeX en la pestaña Metodología (`tex-mml-chtml.js`)
- **Chart.js CDN**: gráficas interactivas con plugin custom para línea "Inicio Forecast"
- **Unidades KPI**: MM COP (millones), GWh (gigavatios-hora) para conciencia situacional
- **Fórmulas alineadas**: entorno `aligned` de LaTeX divide por `=` en renglones separados

## 🐛 Depuración Rápida

```bash
# Ver solo errores de las últimas ejecuciones
tail -f logs/pui_errors.log

# Confirmar que se están usando datos reales (no mock)
grep "PostgreSQL OK" logs/pui_*.log
# Debe mostrar: "PostgreSQL OK: 928 filas obtenidas"
# Si ves "Datos MOCK devueltos", la conexión falló.

# Logs verbosos para depurar un agente específico
python3 main.py --agente ETTC --log-level DEBUG --format html
```

## 🤝 Créditos

- **Google TimesFM** - Modelo de pronóstico de series temporales
- **Chart.js** - Gráficas interactivas
- **MathJax** - Renderizado de fórmulas LaTeX
- **Resolución CREG 101 121 de 2026** - Marco regulatorio colombiano PUI (Artículos 11 y 12)

---

**Generado con arquitectura MVC, principios SOLID y templates modulares para mantenibilidad a largo plazo.**