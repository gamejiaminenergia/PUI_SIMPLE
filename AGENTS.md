# AGENTS.md

## Comandos

- Todo se ejecuta con el venv: `.venv/bin/python ...` (contiene plotly, kaleido, WeasyPrint, pandas, PyTorch/TimesFM).
- `python3 main.py` — regenera los 61 agentes (PostgreSQL con fallback mock; revisa `logs/` para confirmar "PostgreSQL OK").
- `python3 main.py --solo-resumen` — regenera SOLO `docs/resumen_ejecutivo_pui.md` desde los `output/<SIGLA>/kpis.json` (rápido, no reprocesa agentes).
- `.venv/bin/python scripts/build_pdf.py` — regenera el informe PDF (`pdf/informe/informe_pui_acce.pdf`). `--no-assets` reutiliza los SVGs ya generados.
- `.venv/bin/python scripts/build_anexo_pdfs.py` — genera los 61 PDFs de presentación por agente (solo Dashboard Ejecutivo, formato 16:9 apaisado, máx. 2 páginas) en `pdf/anexo/informe_pui_<SIGLA>.pdf`. Usa `templates/report_presentacion_template.html` con branding ACCE (azul `#013A6F`, naranja `#ED8A22`, logo + Inter). Renderiza con Chrome headless (requiere Chart.js). `--agente SIGLA` para uno solo; `--keep-html` conserva el HTML temporal.
- Sintaxis: `python3 -m py_compile main.py models/*.py views/*.py controllers/*.py database/*.py scripts/*.py`

## Fuentes de verdad

- `docs/acce.csv` (leído por `config/acce.py`) = lista oficial de Asociados ACCE (**CODE=0 → miembro**). Son **19** de los 61 agentes.
- `output/<SIGLA>/kpis.json` = fuente de los agregados. `controllers/executive_summary.py` y `scripts/data_loader.py` agregan con **la misma lógica** → PDF y resumen ejecutivo deben coincidir exactamente.
- Formateadores compartidos `_fmt_cop`/`_fmt_kwh` viven en `controllers/executive_summary.py`. Cambiarlos afecta resumen y PDF a la vez.

## Reglas del cliente (no negociables)

- **Montos**: siempre COP completos (`$9.235.836.755.646 COP`). PROHIBIDO usar B/MM/K/"mil millones"/"billones" en valores de datos. Los ejes de gráfica sí pueden decir "Billones de COP" como unidad.
- **Ranking**: debe incluir TODOS los 61 agentes (sin "Top N"). Los agentes deben verse reflejados. En plotly, el eje Y adelgaza ticks automáticamente → forzar `tickmode="array"` + `tickvals`/`ticktext` para mostrar todas las etiquetas.
- Narrativa: demostrar asimetría regulatoria contra los CNIOR (Art. 11 y 12 de la Res. CREG 101 121 de 2026).

## Quirks de Plotly/kaleido

- `fig.write_image(path, format="svg")` (sin `engine=` en plotly 7).
- `paper_bgcolor` NO acepta `'transparent'` → usar `rgba(0,0,0,0)`.
- `fig.add_vline(annotation_text=...)` CRASHEA en ejes de categoría → usar `add_vline` sin texto + `fig.add_annotation(...)` aparte.
- Las gráficas quedan como vectores en el PDF (no aparecen en `pdfimages`); solo el logo es raster.

## Quirks de WeasyPrint

- Los gradientes `@page` son poco fiables → usar `position: fixed` para la línea divisoria (se repite en todas las páginas).
- El `width` en `@top-left { content: url(...) }` se ignora: el logo del encabezado se renderiza al 75% del tamaño natural → pre-redimensionar (`static/img/logo_header.png`).
- Flexbox es poco fiable → usar `inline-block` + `box-sizing: border-box` para grillas (ej. KPIs 3×2).
- Numeración: `counter(page) " de " counter(pages)`; header con `string(chapter, first)`.
- Validar desbordes: el contenido no debe pasar `x > 561pt` (margen derecho 18mm en Letter).

## Verificación del PDF

- `pdfinfo pdf/informe/informe_pui_acce.pdf` → páginas/tamaño.
- `pdftotext -layout` → extraer texto; confirmar que los agregados coinciden con `docs/resumen_ejecutivo_pui.md` (gap $9.235.836.755.646 COP, incobrabilidad 8%, cobertura 88,76%, etc.).
- Chequear que no haya "B"/"mil millones"/"billones" en valores y ningún "Top 10".