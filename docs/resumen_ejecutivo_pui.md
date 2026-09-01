# Resumen Ejecutivo PUI — Análisis Global del Mercado

**Fecha de generación:** 2026-09-01 04:40  
**Agentes analizados:** 62 comercializadores del MEM  
**Marco regulatorio:** Resoluciones CREG 101/2012 y CREG 121/2016  
**Motor de pronóstico:** Google TimesFM 3.0 (modo offline)  

> Este documento resume cómo el mecanismo **PUI (Pago por Uso de Interconexión)** afecta al conjunto de los **comercializadores independientes** del mercado eléctrico colombiano, tanto en el periodo histórico evaluado como en el horizonte de pronóstico.

### Clasificación de los Agentes Analizados

Los agentes incluidos en este estudio son **Comercializadores Independientes del MEM (Mercado Eléctrico Mayorista)**, también conocidos como **CNIORs** (Comercializadores No Integrados al Ofrecimiento de Recursos). Estos son agentes que:

- **No tienen generación propia** — compran toda su energía en el mercado mayorista.
- Son **responsables de girar el PUI** al CIOR (ENEL Colombia S.A. E.S.P.) proporcional a su participación en la demanda regulada.
- Asumen el **riesgo de incobrabilidad** del PUI: la diferencia entre lo que giran al CIOR y lo que efectivamente recaudan de sus usuarios finales.
- Son los **únicos agentes del MEM que generan sobrecosto por PUI**, ya que el CIOR (ENEL) recibe los giros sin asumir pérdida por incobrabilidad.

> **Nota:** Los agentes verticalmente integrados (generadores-comercializadores como EPM, ISAGEN, CEN/ISA) no son sujetos de este análisis porque no están expuestos al mismo mecanismo de sobrecosto por PUI.

## 0. Parámetros de Simulación (config/params.yaml)

> Los siguientes parámetros regulatorios y de modelo fueron utilizados para esta simulación:

| Parámetro | Valor |
|---|---|
| Prima Riesgo Cartera (rcpui) | $0.030 / kWh |
| % Áreas Especiales | 10.0% |
| Factor Recaudo CNIOR | 92% |
| Cargo Competitivo Fijo (cfpui) | $0.025 / kWh |
| Esquema Competitivo | No (Transitorio) |
| % Cobertura Contratos (fallback) | 85% |
| Derivar cobertura desde datos | Sí |

| Parámetro del Modelo | Valor |
|---|---|
| Motor de pronóstico | google/timesfm-3.0-pytorch |
| Backend | cuda |
| Contexto (días) | 512 |
| Horizonte pronóstico (días) | 185 |

| Período de Análisis | Valor |
|---|---|
| Fecha inicio entrenamiento | 2024-01-01 |
| Fecha fin entrenamiento | 2026-08-27 |
| Fecha inicio predicción | 2026-08-28 |
| Fecha fin predicción | 2027-02-28 |

## 1. Impacto Global del PUI (Agregado de Mercado)

| Indicador Global | Valor |
|---|---|
| Energía PUI totalizada (mercado) | 0 kWh |
| Valor total PUI mercado | $234,99 B |
| Giros obligatorios totales al CIOR | $115.257,91 B |
| Recaudo real efectivo total | $106.037,27 B |
| **Faltante de caja (gap recaudo)** | **$9.220,63 B** |
| Sobrecosto por incobrabilidad acumulado | $9.220,63 B |
| Flujo neto de caja PUI (agregado) | -$9.220,63 B |

**Lectura ejecutiva:**
- En el agregado, el mercado deja de recuperar **$9.220,63 B** del PUI facturado. Equivale al **8.00%** del total girado al operador (CIOR/CNIOR).
- El flujo neto de caja agregado es **negativo** (-$9.220,63 B): el sistema, en conjunto, está financiando el PUI con recursos propios.

## 2. Cobertura de Demanda — Contratos vs Bolsa Spot

| Fuente de energía | Valor | Participación |
|---|---|---|
| Cobertura por contratos bilaterales | 603.61 GWh | 87.54% |
| Exposición en bolsa spot | 85.95 GWh | 12.46% |
| **Demanda total agregada (cobertura)** | **689.56 GWh** | 100% |

**Lectura ejecutiva:**
- El mercado está **altamente cubierto por contratos bilaterales** (87.54%). La exposición agregada a la bolsa spot es baja, lo que reduce el riesgo de variabilidad de precios de compra de energía.

## 3. Ranking de Agentes por Sobrecosto Acumulado (Todos los 62 Agentes)

| # | Código | Nombre | Rol PUI | Sobrecosto (COP) | Flujo Neto (COP) | Recaudo (COP) | Pérdida % |
|---|---|---|---|---|---|---|---|
| 1 | `BEIC` | BEAM ENERGY INNOVATION S.A.S. E.S.P. | CNIOR | **$600,44 B** | -$600,44 B | $6.905,07 B | 8.00% |
| 2 | `RTQC` | RUITOQUE S.A. E.S.P. | CNIOR | **$545,86 B** | -$545,86 B | $6.277,44 B | 8.00% |
| 3 | `SCEC` | SOL & CIELO ENERGIA S.A.S. E.S.P | CNIOR | **$545,85 B** | -$545,85 B | $6.277,31 B | 8.00% |
| 4 | `DLRC` | DICELER S.A. E.S.P. | CNIOR | **$545,85 B** | -$545,85 B | $6.277,27 B | 8.00% |
| 5 | `ESVC` | EMPRESA SIGLO XXI EICE ESP | CNIOR | **$545,81 B** | -$545,81 B | $6.276,83 B | 8.00% |
| 6 | `ASCC` | A.S.C. INGENIERIA S.A. E.S.P. | CNIOR | **$545,79 B** | -$545,79 B | $6.276,61 B | 8.00% |
| 7 | `ENBC` | ENERBIT S.A.S. E.S.P. | CNIOR | **$545,76 B** | -$545,76 B | $6.276,27 B | 8.00% |
| 8 | `QIEC` | QI ENERGY S.A.S. E.S.P. | CNIOR | **$545,68 B** | -$545,68 B | $6.275,28 B | 8.00% |
| 9 | `ETTC` | ENERTOTAL S.A. E.S.P. | CNIOR | **$545,68 B** | -$545,68 B | $6.275,26 B | 8.00% |
| 10 | `TPLC` | TERPEL ENERGÍA S.A.S. E.S.P. | CNIOR | **$545,67 B** | -$545,67 B | $6.275,15 B | 8.00% |
| 11 | `GNCC` | VATIA S.A. E.S.P. | CNIOR | **$545,64 B** | -$545,64 B | $6.274,87 B | 8.00% |
| 12 | `NEUC` | NEU ENERGY S.A.S E.S.P | CNIOR | **$545,64 B** | -$545,64 B | $6.274,84 B | 8.00% |
| 13 | `ITLC` | ITALCOL ENERGIA S.A. E.S.P. | CNIOR | **$539,63 B** | -$539,63 B | $6.205,70 B | 8.00% |
| 14 | `PEEC` | PROFESIONALES EN ENERGIA S.A. E.S.P. | CNIOR | **$535,68 B** | -$535,68 B | $6.160,33 B | 8.00% |
| 15 | `SMTC` | SMTC S.A. E.S.P. | CNIOR | **$32,14 B** | -$32,14 B | $369,56 B | 8.00% |
| 16 | `DUCC` | DUCC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,54 B | 8.00% |
| 17 | `ELIC` | ELIC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,54 B | 8.00% |
| 18 | `PRYC` | PRYC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,50 B | 8.00% |
| 19 | `DEPC` | DEPC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,48 B | 8.00% |
| 20 | `UNGC` | UNGC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,46 B | 8.00% |
| 21 | `EXIC` | EXIC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,45 B | 8.00% |
| 22 | `CBYC` | CBYC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,45 B | 8.00% |
| 23 | `EGTC` | EGTC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,44 B | 8.00% |
| 24 | `NESC` | NESC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,44 B | 8.00% |
| 25 | `COLC` | COLC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,43 B | 8.00% |
| 26 | `LESC` | LESC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,43 B | 8.00% |
| 27 | `PLSC` | PLSC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,42 B | 8.00% |
| 28 | `AMPC` | AMPC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,41 B | 8.00% |
| 29 | `RPEC` | RPEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,41 B | 8.00% |
| 30 | `DRUC` | DRUC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,41 B | 8.00% |
| 31 | `ERNC` | ERNC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,40 B | 8.00% |
| 32 | `MERC` | MERC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,38 B | 8.00% |
| 33 | `GAPC` | GAPC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,37 B | 8.00% |
| 34 | `GREC` | GREC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,36 B | 8.00% |
| 35 | `CBNC` | CBNC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,36 B | 8.00% |
| 36 | `LMEC` | LMEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,35 B | 8.00% |
| 37 | `ENVC` | ENVC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,35 B | 8.00% |
| 38 | `SPRC` | SPRC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,35 B | 8.00% |
| 39 | `IAEC` | IAEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,34 B | 8.00% |
| 40 | `EYCC` | EYCC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,34 B | 8.00% |
| 41 | `GNYC` | GNYC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,34 B | 8.00% |
| 42 | `FREC` | FREC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 43 | `NEXC` | NEXC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 44 | `SOEC` | SOEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 45 | `LTEC` | LTEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,32 B | 8.00% |
| 46 | `FERC` | FERC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,32 B | 8.00% |
| 47 | `CNRC` | CNRC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,32 B | 8.00% |
| 48 | `EFEC` | EFEC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,32 B | 8.00% |
| 49 | `ASCC~` | ASCC~ S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,31 B | 8.00% |
| 50 | `NRCC` | ENERCO S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,31 B | 8.00% |
| 51 | `CMXC` | CMXC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,31 B | 8.00% |
| 52 | `VESC` | VESC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,30 B | 8.00% |
| 53 | `GWOC` | GWOC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,29 B | 8.00% |
| 54 | `DMRC` | DMRC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,29 B | 8.00% |
| 55 | `JRDC` | JRDC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,27 B | 8.00% |
| 56 | `SEJC` | SEJC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,27 B | 8.00% |
| 57 | `CERC` | CERC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,23 B | 8.00% |
| 58 | `NMRC` | NMRC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,20 B | 8.00% |
| 59 | `SFEC` | SFEC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,18 B | 8.00% |
| 60 | `SOUC` | SOUC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,17 B | 8.00% |
| 61 | `EMMC` | EMMC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,15 B | 8.00% |
| 62 | `RTAC` | RTAC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,15 B | 8.00% |

**Lectura ejecutiva:**
- El agente con mayor sobrecosto (`BEIC` — BEAM ENERGY INNOVATION S.A.S. E.S.P.) concentra **6.51%** del sobrecosto total del mercado.
- La totalidad de los 62 agentes concentra **100.00%** del sobrecosto total.

## 4. Distribución de Pérdida por Incobrabilidad

| Rango de pérdida | # Agentes | Agentes |
|---|---|---|
| <2% | 0 | — |
| 2-5% | 0 | — |
| 5-10% | 62 | `AMPC`, `ASCC`, `ASCC~`, `BEIC`, `CBNC`, `CBYC`, `CERC`, `CMXC`, `CNRC`, `COLC`, `DEPC`, `DLRC`, `DMRC`, `DRUC`, `DUCC`, `EFEC`, `EGTC`, `ELIC`, `EMMC`, `ENBC`, `ENVC`, `ERNC`, `ESVC`, `ETTC`, `EXIC`, `EYCC`, `FERC`, `FREC`, `GAPC`, `GNCC`, `GNYC`, `GREC`, `GWOC`, `IAEC`, `ITLC`, `JRDC`, `LESC`, `LMEC`, `LTEC`, `MERC`, `NESC`, `NEUC`, `NEXC`, `NMRC`, `NRCC`, `PEEC`, `PLSC`, `PRYC`, `QIEC`, `RPEC`, `RTAC`, `RTQC`, `SCEC`, `SEJC`, `SFEC`, `SMTC`, `SOEC`, `SOUC`, `SPRC`, `TPLC`, `UNGC`, `VESC` |
| >10% | 0 | — |

**Lectura ejecutiva:**
- **62 agentes** (100.0%) tienen pérdida media-alta (≥5%).
- **0 agentes** tienen pérdida moderada (2–5%).
- **0 agentes** tienen pérdida baja (<2%).

## 5. Cobertura Temporal del Análisis

| Tipo | # Agentes | % |
|---|---|---|
| Con histórico completo | 0 | 0.0% |
| Con forecast TimesFM | 62 | 100.0% |

**Lectura ejecutiva:**
- **Todos los agentes cuentan con pronóstico diario TimesFM** para el horizonte futuro, lo que permite proyectar la trayectoria del PUI y anticipar necesidades de caja.

## 6. Conclusiones Ejecutivas

1. **El PUI es financieramente deficitario en el agregado:** el mercado, en conjunto, deja de recuperar una porción significativa del PUI facturado por cuenta de la incobrabilidad de los usuarios finales.
2. **La cobertura por contratos es alta**, lo que reduce el riesgo de volatilidad de precios de compra para los comercializadores.
3. **El sobrecosto se concentra:** un número reducido de agentes concentra la mayor parte de la pérdida financiera por incobrabilidad. Esto sugiere que las acciones de gestión de cartera tienen alto impacto si se focalizan en esos agentes.
4. **El forecast permite anticipar el faltante**, lo que habilita planes de cobertura de caja y de gestión de recaudo proactivo.

## 7. Anexo — Agentes Analizados (Listado Completo)

Los 62 siguientes comercializadores del MEM fueron incluidos en este análisis:

| #1 | #2 | #3 | #4 | #5 | #6 |
|---|---|---|---|---|---|
| `AMPC` | `ASCC` | `ASCC~` | `BEIC` | `CBNC` | `CBYC` |
| `CERC` | `CMXC` | `CNRC` | `COLC` | `DEPC` | `DLRC` |
| `DMRC` | `DRUC` | `DUCC` | `EFEC` | `EGTC` | `ELIC` |
| `EMMC` | `ENBC` | `ENVC` | `ERNC` | `ESVC` | `ETTC` |
| `EXIC` | `EYCC` | `FERC` | `FREC` | `GAPC` | `GNCC` |
| `GNYC` | `GREC` | `GWOC` | `IAEC` | `ITLC` | `JRDC` |
| `LESC` | `LMEC` | `LTEC` | `MERC` | `NESC` | `NEUC` |
| `NEXC` | `NMRC` | `NRCC` | `PEEC` | `PLSC` | `PRYC` |
| `QIEC` | `RPEC` | `RTAC` | `RTQC` | `SCEC` | `SEJC` |
| `SFEC` | `SMTC` | `SOEC` | `SOUC` | `SPRC` | `TPLC` |
| `UNGC` | `VESC` | — | — | — | — |

## 8. Ecuaciones y Modelo de Cálculo

> Modelo regulatorio descrito en las resoluciones **CREG 101/2012** (Esquema Transitorio) y **CREG 121/2016** (Esquema Competitivo). A continuación se presentan las ecuaciones en orden lógico de cálculo, de la demanda hasta el sobrecosto final.

### Paso 0 — Cobertura de Demanda (Contratos vs Bolsa Spot)

Toda demanda comercial regulada del agente se divide en dos fuentes de compra de energía:

```
VR_agente = Energía_Contratos + Energía_Bolsa_Spot   [kWh]

% Cobertura_Contratos = (Energía_Contratos / VR_agente) × 100
% Exposición_Bolsa    = (Energía_Bolsa_Spot / VR_agente) × 100
```

> **Interpretación:** A mayor % de cobertura por contratos, menor exposición a la volatilidad del precio spot (PMEM). El 85% es el fallback cuando la BD no expone la variable `CompContEnerReg`.

### Paso 1 — Demanda Comercial Agente y Mercado

Variables extraídas de la BD del SIN (tabla `fact_hourly_*`):

```
VR_agente  = Σ DemaComeReg   [kWh]   ← Demanda Comercial Regulada por agente
VR_mercado = Σ DemaCome      [kWh]   ← Demanda Comercial total del mercado
```

> **Dato de BD:** `DemaComeReg` (demanda del agente) y `DemaCome` (demanda del mercado). Ambas en kilovatios-hora [kWh].

### Paso 2 — Costo Unitario de la Prestación (CU)

Precio promedio de los contratos bilaterales del agente:

```
CU_m-1 = PrecPromCont_m-1   [COP/kWh]
```

> **Dato de BD:** `PrecPromCont` (Costo Unitario promedio ponderado). Se utiliza con rezago de 1 mes (m-1) según la metodología CREG.

### Paso 3 — Volumen de Áreas Especiales (VPUI)

Energía que se encuentra en las zonas geográficas donde aplica el PUI, calculada con rezago de 1 mes:

```
VPUI_m-1 = VR_mercado_m-1 × %_áreas_especiales   [kWh]

Ejemplo: VPUI = VR_mercado × 10%
```

> **Parámetro:** `%_áreas_especiales = 10%` (configurable en params.yaml). Representa el porcentaje de la demanda del mercado que está en zonas especiales.

### Paso 4 — Tarifas de Incobrabilidad (CRPUI / CFPUI)

**Esquema Transitorio** (CREG 101/2012) — aplica un cargo por riesgo de cartera:

```
CRPUI_unitario_m = (rcpui × VPUI_m-1) / (VR_m-1 × CU_m-1)   [COP/kWh]

Donde:
  rcpui  = Prima de riesgo de cartera (por defecto: $0.030 COP/kWh)
  VPUI   = Volumen de áreas especiales (Paso 3)
  VR_m-1 = Demanda del mercado rezago m-1
  CU_m-1 = Costo unitario rezago m-1
```

**Esquema Competitivo** (CREG 121/2016) — cargo fijo:

```
CFPUI = $0.025 COP/kWh   (fijo, no depende de variables del mercado)
```

> **Nota:** En este estudio se usa el **Esquema Transitorio** por defecto. El parámetro `esquema_competitivo = false` en params.yaml controla cuál aplica.

### Paso 5 — PUI Asignado al Agente

El PUI total asignado al agente (en energía y en dinero):

```
PUI_energia_kwh = VR_agente × %_áreas_especiales   [kWh]
PUI_dinero_cop  = PUI_energia_kwh × CRPUI_unitario  [COP]
```

> **Resultado:** Es el monto total que el agente debe facturar a sus usuarios como parte del mecanismo PUI.

### Paso 6 — Egreso por Giro Obligatorio al CIOR

Obligación regulada del agente CNIOR de girar el PUI al CIOR (ENEL Colombia), proporcional a su participación en la demanda total de CNIORs:

```
Egreso_Giro_CIOR = Giro_mercado × (VR_CNIOR / VR_CNIORs)   [COP]

Donde:
  Giro_mercado = Total de giros PUI de todo el mercado
  VR_CNIOR     = Demanda del agente CNIOR específico
  VR_CNIORs    = Demanda total de TODOS los CNIORs
```

> **Interpretación:** Cada agente CNIOR gira al CIOR según su proporción de participación en el mercado regulado.

### Paso 7 — Recaudo Efectivo

Monto que el agente logra efectivamente cobrar a sus usuarios finales:

```
Recaudo_Efectivo = Egreso_Giro_CIOR × Factor_Recaudo   [COP]

Donde:
  Factor_Recaudo = 92% (por defecto, configurable en params.yaml)
```

> **Interpretación:** El 8% restante (100% - 92%) representa la **incobrabilidad** — el monto que los usuarios finales no pagan.

### Paso 8 — Sobrecosto por Incobrabilidad (Pérdida Final)

La pérdida financiera neta del agente por el mecanismo PUI:

```
Sobrecosto_Incobrabilidad = Egreso_Giro_CIOR - Recaudo_Efectivo   [COP]

Equivalente a:
Sobrecosto = Egreso_Giro_CIOR × (1 - Factor_Recaudo)   [COP]
```

> **Interpretación:** Es el dinero que el agente debe pagar al CIOR pero no logra recaudar. Lo financia con recursos propios, lo que impacta directamente su flujo de caja.

### Paso 9 — Flujo Neto de Caja

Balance final del efectivo del agente por concepto PUI:

```
Flujo_Neto_Caja = Recaudo_Efectivo - Egreso_Giro_CIOR   [COP]

Si Flujo_Neto < 0 → El agente está financiando la diferencia
Si Flujo_Neto ≥ 0 → El agente cubre su obligación sin pérdida
```

> **Nota:** En este estudio, el flujo neto es **negativo** para todos los agentes porque el factor de recaudo (92%) genera un 8% de pérdida inevitable.

### Resumen del Flujo de Cálculo

```
┌─────────────────────────────────────────────────────────────────────┐
│  BD SIN/XM                                                         │
│  ├── DemaComeReg (VR_agente)                                       │
│  ├── DemaCome (VR_mercado)                                         │
│  ├── PrecPromCont (CU)                                              │
│  └── %_áreas_especiales (parámetro)                                │
└──────────────────────┬──────────────────────────────────────────────┘
                       ▼
  Paso 3: VPUI = VR_mercado × 10%                                    │
                       ▼
  Paso 4: CRPUI = (rcpui × VPUI) / (VR × CU)                        │
                       ▼
  Paso 5: PUI = VR_agente × CRPUI                                    │
                       ▼
  Paso 6: Egreso_Giro = Giro_mercado × (VR_CNIOR / VR_CNIORs)        │
                       ▼
  Paso 7: Recaudo = Egreso × 92%                                     │
                       ▼
  Paso 8: Sobrecosto = Egreso - Recaudo                              │
                       ▼
  Paso 9: Flujo_Neto = Recaudo - Egreso  (= -Sobrecosto)             │
```

## 9. Metodología y Fuentes de Datos

- **Datos fuente:** PostgreSQL (BD del SIN/XM), tabla `fact_hourly_*` y dimensiones `dim_*`. Conexión verificada por logs en `logs/pui_YYYYMMDD.log`.
- **Pronóstico:** Google TimesFM 3.0 (modo offline, sin peticiones HTTP tras descarga inicial).
- **Parámetros regulatorios:** CREG 101/2012 y CREG 121/2016.
- **Modelo:** Arquitectura MVC en Python, principios SOLID, logger centralizado con rotación diaria en `logs/`.

## 10. Glosario de Términos

> Definiciones para facilitar la comprensión del documento a auditores, gerentes financieros y áreas comerciales.

| Término | Sigla | Definición |
|---|---|---|
| **PUI** | PUI | Pago por Uso de Interconexión. Cargo que los comercializadores deben pagar por el uso de la red de transmisión nacional. Se calcula sobre la demanda comercial de cada agente en áreas especiales.
| **CIOR** | CIOR | Comercializador de Último Recurso Obligado a Recibir. Es el agente designado para recibir los giros del PUI de parte de los CNIORs. En este estudio, es ENEL Colombia S.A. E.S.P.
| **CNIOR** | CNIOR | Comercializador Independiente No Interconectado al Ofrecimiento de Recursos. Son los comercializadores puros del MEM (sin generación propia) que participan en este estudio. Compran toda su energía en el mercado mayorista y son responsables de girar el PUI al CIOR. Asumen el riesgo de incobrabilidad sobre los giros.
| **Sobrecosto** | — | Diferencia entre el monto total que el agente debe girar al CIOR y el monto que efectivamente logra recaudar de sus usuarios. Representa la pérdida financiera por incobrabilidad.
| **Flujo Neto de Caja** | — | Resultado de restar los egresos por giros al CIOR menos el recaudo efectivo. Si es negativo, el agente está financiando la diferencia.
| **Recaudo Efectivo** | — | Porcentaje del PUI que el agente realmente logra cobrar a sus usuarios finales.Depende del factor de recaudo configurado (por defecto 92%).
| **Incobrabilidad** | — | Porcentaje del monto facturado que no se logra cobrar. Es la principal causa del sobrecosto en el mecanismo PUI.
| **Cobertura de Demanda** | — | Porcentaje de la demanda de energía del agente que está cubierta por contratos bilaterales de compra vs. lo que se compra en bolsa spot. A mayor cobertura por contratos, menor exposición a la volatilidad del mercado.
| **Bolsa Spot** | — | Mercado de compra-venta de energía a precio diario (PMEM). Es el precio de referencia del mercado eléctrico colombiano.
| **Contratos Bilaterales** | — | Acuerdos privados de compra de energía a precio fijo o indexado, que protegen al comercializador de la volatilidad del precio spot.
| **Áreas Especiales** | — | Zonas geográficas del país donde el PUI se aplica sobre un porcentaje de la demanda (por defecto 10%). Están definidas por la CREG.
| **rcpui** | rcpui | Prima de riesgo de cartera. Es un cargo adicional (en COP/kWh) que compensa el riesgo de no cobro del PUI. Por defecto: $0.030/kWh.
| **cfpui** | cfpui | Cargo fijo competitivo. Componente del PUI que representa el costo competitivo de la interconexión. Por defecto: $0.025/kWh.
| **Esquema Competitivo vs Transitorio** | — | El esquema transitorio aplica un cargo fijo (cfpui) mientras que el competitivo calcula el cargo según la metodología CREG 121/2016. Por defecto: Transitorio.
| **TimesFM** | — | Google TimesFM 3.0. Modelo de inteligencia artificial de pronóstico de series temporales utilizado para proyectar la demanda y cobertura de energía a futuro.
| **MEM** | MEM | Mercado Eléctrico Mayorista. El mercado mayorista de comercialización de energía eléctrica en Colombia, regulado por la CREG.
| **CREG** | CREG | Comisión de Regulación de Energía y Gas. Ente regulador del sector eléctrico y gasífero en Colombia.
| **SIN** | SIN | Sistema Interconectado Nacional. La red eléctrica nacional de Colombia, administrada por el operador XM.
| **PMEM** | PMEM | Precio Marginal de Energía en el Mercado. El precio de referencia diario de la energía en el MEM.
| **Forecast / Pronóstico** | — | Predicción de valores futuros basada en modelos estadísticos o de inteligencia artificial. En este estudio se usa para proyectar la demanda y cobertura a futuro.

---

_Documento generado automáticamente. Carpetas individuales por agente en `output/<SIGLA>/`._
