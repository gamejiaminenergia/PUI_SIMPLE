# Sistema MVC de Generación de Informes PUI (Pago por Uso de Interconexión & Pronóstico TimesFM)

Sistema modular en Python basado en la arquitectura **Modelo-Vista-Controlador (MVC)** para analizar, auditar y pronosticar la consulta regulatoria del Pago por Uso de Interconexión (PUI) bajo resoluciones CREG 101/2012 y 121/2016.

---

## 📁 Carpeta Organizada de Salidas (`output/`)

Todos los resultados, análisis de auditoría de fórmulas y reportes ejecutivos se organizan automáticamente en la carpeta `output/`:

1. **`output/pui_report_ETTC_unificado.html`**:
   - Informe HTML interactivo para clientes exigentes con pestañas para:
     - 📊 Dashboard Ejecutivo & KPIs Financieros.
     - 🧠 Guía Metodológica y Fórmulas CREG Paso a Paso (CREG 101/2012 y CREG 121/2016).
     - 📐 Matriz de Auditoría de Fórmulas y Variables Intermedias ($VR_{m-1}, VPUI_{m-1}, CU_{m-1}, CRPUI, PUI_{mercado}, Giro_{CIOR}, Sobrecosto$).
     - 📋 Dataset Unificado Completo (360 registros con buscador en tiempo real).
2. **`output/pui_dataset_unificado.csv`**:
   - Dataset maestro con las 45 columnas unificadas (`HISTORICO` vs `FORECAST`).
3. **`output/pui_auditoria_formulas.csv`**:
   - Desglose granular de variables intermedias para auditorías contables/regulatorias en Excel.
4. **`output/pui_resumen_mensual.csv`**:
   - Consolidado mensual ejecutivo.
5. **`output/pui_series_diarias_forecast.csv`**:
   - Serie temporal diaria pronosticada mediante el modelo de inteligencia artificial **Google TimesFM** antes de su agregación mensual.

---

## 🚀 Uso Rápido (CLI)

```bash
# Generar informe completo y auditable en la carpeta output/
python3 main.py --mode both --format console,html,csv
```
