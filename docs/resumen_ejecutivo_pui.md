# Resumen Ejecutivo PUI — Análisis Global del Mercado

**Fecha de generación:** 2026-09-02 01:34  
**Agentes analizados:** 61 comercializadores del MEM  
**Marco regulatorio:** Resolución CREG 101 121 de 2026 (Artículos 11 y 12)  
**Motor de pronóstico:** Google TimesFM 3.0 (modo offline)  

> Estudio encargado por la **Asociación Colombiana de Comercializadores de Energía (ACCE)** para evidenciar cómo el mecanismo **PUI (Prestador de Última Instancia)** afecta a sus asociados —los **comercializadores independientes** del mercado eléctrico colombiano— tanto en el periodo histórico evaluado como en el horizonte de pronóstico.

### Clasificación de los Agentes Analizados

Los agentes incluidos en este estudio son **Comercializadores Independientes del MEM (Mercado Eléctrico Mayorista)**, también conocidos como **CNIORs** (Comercializadores No Integrados con el Operador de Red). Estos son agentes que:

- **No tienen generación propia** — compran toda su energía en el mercado mayorista.
- Son **responsables de girar el PUI** al CIOR (Comercializador Incumbente del Operador de Red, ENEL Colombia S.A. E.S.P.) proporcional a su participación en la demanda regulada.
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
| Valor total PUI mercado | $235,54 B |
| Giros obligatorios totales al CIOR | $115.447,96 B |
| Recaudo real efectivo total | $106.212,12 B |
| **Faltante de caja (gap recaudo)** | **$9.235,84 B** |
| Sobrecosto por incobrabilidad acumulado | $9.235,84 B |
| Flujo neto de caja PUI (agregado) | -$9.235,84 B |

**Lectura ejecutiva:**
- En el agregado, el mercado deja de recuperar **$9.235,84 B** del PUI facturado. Equivale al **8.00%** del total girado al operador (CIOR/CNIOR).
- El flujo neto de caja agregado es **negativo** (-$9.235,84 B): el sistema, en conjunto, está financiando el PUI con recursos propios.

## 2. Cobertura de Demanda — Contratos vs Bolsa Spot

| Fuente de energía | Valor | Participación |
|---|---|---|
| Cobertura por contratos bilaterales | 610.16 GWh | 88.76% |
| Exposición en bolsa spot | 77.27 GWh | 11.24% |
| **Demanda total agregada (cobertura)** | **687.43 GWh** | 100% |

**Lectura ejecutiva:**
- El mercado está **altamente cubierto por contratos bilaterales** (88.76%). La exposición agregada a la bolsa spot es baja, lo que reduce el riesgo de variabilidad de precios de compra de energía.

## 3. Ranking de Agentes por Sobrecosto Acumulado (Todos los 61 Agentes)

| # | Código | Nombre | Rol PUI | Sobrecosto (COP) | Flujo Neto (COP) | Recaudo (COP) | Pérdida % |
|---|---|---|---|---|---|---|---|
| 1 | `BEIC` | BEAM ENERGY INNOVATION S.A.S. E.S.P. | CNIOR | **$607,51 B** | -$607,51 B | $6.986,40 B | 8.00% |
| 2 | `ASCC ★` | A.S.C. INGENIERIA S.A. E.S.P. | CNIOR | **$549,61 B** | -$549,61 B | $6.320,52 B | 8.00% |
| 3 | `GNCC ★` | VATIA S.A. E.S.P. | CNIOR | **$549,55 B** | -$549,55 B | $6.319,80 B | 8.00% |
| 4 | `SCEC ★` | SOL & CIELO ENERGIA S.A.S. E.S.P | CNIOR | **$549,54 B** | -$549,54 B | $6.319,70 B | 8.00% |
| 5 | `ETTC ★` | ENERTOTAL S.A. E.S.P. | CNIOR | **$549,54 B** | -$549,54 B | $6.319,68 B | 8.00% |
| 6 | `DLRC ★` | DICELER S.A. E.S.P. | CNIOR | **$549,51 B** | -$549,51 B | $6.319,34 B | 8.00% |
| 7 | `ENBC` | ENERBIT S.A.S. E.S.P. | CNIOR | **$549,44 B** | -$549,44 B | $6.318,56 B | 8.00% |
| 8 | `QIEC ★` | QI ENERGY S.A.S. E.S.P. | CNIOR | **$549,37 B** | -$549,37 B | $6.317,81 B | 8.00% |
| 9 | `RTQC ★` | RUITOQUE S.A. E.S.P. | CNIOR | **$549,35 B** | -$549,35 B | $6.317,53 B | 8.00% |
| 10 | `NEUC ★` | NEU ENERGY S.A.S E.S.P | CNIOR | **$549,34 B** | -$549,34 B | $6.317,43 B | 8.00% |
| 11 | `ESVC` | EMPRESA SIGLO XXI EICE ESP | CNIOR | **$549,34 B** | -$549,34 B | $6.317,36 B | 8.00% |
| 12 | `TPLC` | TERPEL ENERGÍA S.A.S. E.S.P. | CNIOR | **$549,16 B** | -$549,16 B | $6.315,33 B | 8.00% |
| 13 | `ITLC ★` | ITALCOL ENERGIA S.A. E.S.P. | CNIOR | **$539,29 B** | -$539,29 B | $6.201,80 B | 8.00% |
| 14 | `PEEC` | PROFESIONALES EN ENERGIA S.A. E.S.P. | CNIOR | **$535,70 B** | -$535,70 B | $6.160,54 B | 8.00% |
| 15 | `GNYC` | GNYC S.A. E.S.P. | CNIOR | **$32,14 B** | -$32,14 B | $369,60 B | 8.00% |
| 16 | `ERNC` | ERNC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,54 B | 8.00% |
| 17 | `DUCC` | DUCC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,53 B | 8.00% |
| 18 | `GWOC` | GWOC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,51 B | 8.00% |
| 19 | `COLC` | COLC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,50 B | 8.00% |
| 20 | `VESC` | VESC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,46 B | 8.00% |
| 21 | `EXIC ★` | EXIC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,44 B | 8.00% |
| 22 | `SOUC` | SOUC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,44 B | 8.00% |
| 23 | `EGTC ★` | EGTC S.A. E.S.P. | CNIOR | **$32,13 B** | -$32,13 B | $369,44 B | 8.00% |
| 24 | `NESC` | NESC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,43 B | 8.00% |
| 25 | `ENVC` | ENVC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,43 B | 8.00% |
| 26 | `RTAC` | RTAC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,42 B | 8.00% |
| 27 | `GAPC` | GAPC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,42 B | 8.00% |
| 28 | `EYCC ★` | EYCC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,40 B | 8.00% |
| 29 | `AMPC` | AMPC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,40 B | 8.00% |
| 30 | `CNRC` | CNRC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,39 B | 8.00% |
| 31 | `CMXC` | CMXC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,39 B | 8.00% |
| 32 | `DMRC` | DMRC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,39 B | 8.00% |
| 33 | `CBYC` | CBYC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,38 B | 8.00% |
| 34 | `PRYC` | PRYC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,38 B | 8.00% |
| 35 | `EFEC` | EFEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,37 B | 8.00% |
| 36 | `IAEC` | IAEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,37 B | 8.00% |
| 37 | `UNGC` | UNGC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,37 B | 8.00% |
| 38 | `NMRC` | NMRC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,37 B | 8.00% |
| 39 | `PLSC` | PLSC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,36 B | 8.00% |
| 40 | `DRUC` | DRUC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,36 B | 8.00% |
| 41 | `MERC ★` | MERC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,35 B | 8.00% |
| 42 | `LTEC` | LTEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,35 B | 8.00% |
| 43 | `CERC` | CERC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,34 B | 8.00% |
| 44 | `EMMC` | EMMC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,34 B | 8.00% |
| 45 | `LESC` | LESC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 46 | `FREC` | FREC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 47 | `LMEC` | LMEC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,33 B | 8.00% |
| 48 | `ELIC` | ELIC S.A. E.S.P. | CNIOR | **$32,12 B** | -$32,12 B | $369,32 B | 8.00% |
| 49 | `NRCC ★` | ENERCO S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,32 B | 8.00% |
| 50 | `NEXC` | NEXC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,32 B | 8.00% |
| 51 | `SOEC` | SOEC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,31 B | 8.00% |
| 52 | `CBNC ★` | CBNC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,31 B | 8.00% |
| 53 | `SPRC` | SPRC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,30 B | 8.00% |
| 54 | `FERC ★` | FERC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,30 B | 8.00% |
| 55 | `SMTC` | SMTC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,29 B | 8.00% |
| 56 | `RPEC` | RPEC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,27 B | 8.00% |
| 57 | `SFEC ★` | SFEC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,26 B | 8.00% |
| 58 | `SEJC` | SEJC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,25 B | 8.00% |
| 59 | `JRDC ★` | JRDC S.A. E.S.P. | CNIOR | **$32,11 B** | -$32,11 B | $369,24 B | 8.00% |
| 60 | `GREC` | GREC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,20 B | 8.00% |
| 61 | `DEPC ★` | DEPC S.A. E.S.P. | CNIOR | **$32,10 B** | -$32,10 B | $369,15 B | 8.00% |

> **Nota:** el símbolo **★** identifica a los **Asociados ACCE** dentro del ranking. En este listado hay **19** asociados ACCE.

**Lectura ejecutiva:**
- El agente con mayor sobrecosto (`BEIC` — BEAM ENERGY INNOVATION S.A.S. E.S.P.) concentra **6.58%** del sobrecosto total del mercado.
- La totalidad de los 61 agentes concentra **100.00%** del sobrecosto total.

## 4. Distribución de Pérdida por Incobrabilidad

| Rango de pérdida | # Agentes | Agentes |
|---|---|---|
| <2% | 0 | — |
| 2-5% | 0 | — |
| 5-10% | 61 | `ASCC`, `CBNC`, `DEPC`, `DLRC`, `NRCC`, `EGTC`, `EYCC`, `ETTC`, `EXIC`, `FERC`, `ITLC`, `JRDC`, `MERC`, `NEUC`, `QIEC`, `RTQC`, `SFEC`, `SCEC`, `GNCC`, `AMPC`, `BEIC`, `CBYC`, `CERC`, `CMXC`, `CNRC`, `COLC`, `DMRC`, `DRUC`, `DUCC`, `EFEC`, `EMMC`, `ESVC`, `ENBC`, `ELIC`, `NMRC`, `ENVC`, `ERNC`, `SPRC`, `FREC`, `GAPC`, `GWOC`, `GNYC`, `GREC`, `IAEC`, `LTEC`, `LMEC`, `LESC`, `NEXC`, `NESC`, `PLSC`, `PRYC`, `PEEC`, `RPEC`, `SMTC`, `SEJC`, `SOUC`, `SOEC`, `RTAC`, `TPLC`, `UNGC`, `VESC` |
| >10% | 0 | — |

**Lectura ejecutiva:**
- **61 agentes** (100.0%) tienen pérdida media-alta (≥5%).
- **0 agentes** tienen pérdida moderada (2–5%).
- **0 agentes** tienen pérdida baja (<2%).

## 5. Cobertura Temporal del Análisis

| Tipo | # Agentes | % |
|---|---|---|
| Con histórico completo | 0 | 0.0% |
| Con forecast TimesFM | 61 | 100.0% |

**Lectura ejecutiva:**
- **Todos los agentes cuentan con pronóstico diario TimesFM** para el horizonte futuro, lo que permite proyectar la trayectoria del PUI y anticipar necesidades de caja.

## 6. Esquema Equitativo vs Trato Asimétrico (Artículos 11 y 12)

El diseño transitorio de la Resolución 101 121 de 2026 genera asimetrías regulatorias que afectan de forma diferenciada a los CNIOR (asociados ACCE):

- **Caja garantizada para el OR:** El Comercializador Incumbente del Operador de Red recibe los giros del PUI sí o sí (principio de caja garantizada), sin asumir pérdida por incobrabilidad.
- **Riesgo de cartera 100% en el CNIOR:** El comercializador no integrado debe girar lo **facturado** aunque no lo haya **recaudado** (Artículo 12: 'pague lo facturado, no lo recaudado'). El faltante resultante es el sobrecosto por incobrabilidad.
- **Ausencia de subsidio cruzado:** A diferencia de los grupos integrados, un CNIOR no cuenta con ingresos de generación o distribución para compensar el déficit de caja; depende enteramente del recaudo diario.

> **Conclusión del cliente (ACCE):** la norma no discrimina de forma directa, pero al aplicar una regla homogénea ('todos pagan independientemente del recaudo') a agentes con condiciones heterogéneas, **asfixia financieramente al eslabón más débil** y favorece indirectamente a los operadores integrados, concentrando aún más el mercado.

## 7. Comparativa: Esquema Transitorio (Art. 11 y 12) vs Mecanismo Competitivo Definitivo

El mecanismo competitivo definitivo desmonta el esquema transitorio asimétrico: el precio se fija por oferta ganadora en subasta, la participación es voluntaria y el riesgo de cartera pasa a ser un **componente remunerado** del cargo aprobado. El siguiente cuadro muestra cómo el faltante de caja de los CNIOR se reduce a medida que el esquema reconoce (remunera) la incobrabilidad en lugar de cargarla en su totalidad al comercializador:

| Escenario | Factor Recaudo Efectivo | Faltante de caja (agregado) | % del giro al CIOR |
|---|---|---|---|
| Transitorio hoy (Art. 12: 'pague lo facturado, no lo recaudado') | 92% | **$9.235,84 B** | 8.00% |
| Competitivo con reconocimiento parcial del riesgo | 95% | **$5.772,40 B** | 5.00% |
| Competitivo con reconocimiento pleno del riesgo | 97% | **$3.463,44 B** | 3.00% |
| Competitivo con riesgo 100% remunerado (neutralidad competitiva) | 100% | **$0** | 0.00% |

> **Interpretación para ACCE:** el sobrecosto por incobrabilidad **no es un costo inherente del servicio**, sino una consecuencia de un diseño transitorio que traslada todo el riesgo al CNIOR. Un mecanismo competitivo que remunere el riesgo de cartera reduciría el faltante agregado de forma sustancial, nivelando la cancha de juego frente a los operadores integrados.

## 8. Conclusiones Ejecutivas

1. **El PUI es financieramente deficitario en el agregado:** el mercado, en conjunto, deja de recuperar una porción significativa del PUI facturado por cuenta de la incobrabilidad de los usuarios finales.
2. **La cobertura por contratos es alta**, lo que reduce el riesgo de volatilidad de precios de compra para los comercializadores.
3. **El sobrecosto se concentra:** un número reducido de agentes concentra la mayor parte de la pérdida financiera por incobrabilidad. Esto sugiere que las acciones de gestión de cartera tienen alto impacto si se focalizan en esos agentes.
4. **El forecast permite anticipar el faltante**, lo que habilita planes de cobertura de caja y de gestión de recaudo proactivo.

## 9. Anexo — Agentes Analizados (Listado Completo)

Los 61 siguientes comercializadores del MEM fueron incluidos en este análisis:

| #1 | #2 | #3 | #4 | #5 | #6 |
|---|---|---|---|---|---|
| `AMPC` | `ASCC★` | `BEIC` | `CBNC★` | `CBYC` | `CERC` |
| `CMXC` | `CNRC` | `COLC` | `DEPC★` | `DLRC★` | `DMRC` |
| `DRUC` | `DUCC` | `EFEC` | `EGTC★` | `ELIC` | `EMMC` |
| `ENBC` | `ENVC` | `ERNC` | `ESVC` | `ETTC★` | `EXIC★` |
| `EYCC★` | `FERC★` | `FREC` | `GAPC` | `GNCC★` | `GNYC` |
| `GREC` | `GWOC` | `IAEC` | `ITLC★` | `JRDC★` | `LESC` |
| `LMEC` | `LTEC` | `MERC★` | `NESC` | `NEUC★` | `NEXC` |
| `NMRC` | `NRCC★` | `PEEC` | `PLSC` | `PRYC` | `QIEC★` |
| `RPEC` | `RTAC` | `RTQC★` | `SCEC★` | `SEJC` | `SFEC★` |
| `SMTC` | `SOEC` | `SOUC` | `SPRC` | `TPLC` | `UNGC` |
| `VESC` | — | — | — | — | — |

> **★** = Asociado ACCE (Comercializador Independiente afiliado a la Asociación Colombiana de Comercializadores de Energía).

## 10. Ecuaciones y Modelo de Cálculo

> Modelo regulatorio descrito en la **Resolución CREG 101 121 de 2026** (Artículo 11: traslado del valor del PUI a los usuarios regulados antes del mecanismo competitivo; Artículo 12: recaudo y liquidación del costo asumido por el PUI, principio de 'pague lo facturado, no lo recaudado'). A continuación se presentan las ecuaciones en orden lógico de cálculo, de la demanda hasta el sobrecosto final.

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

**Esquema Transitorio** (Resolución 101 121 de 2026, Artículo 12) — aplica un cargo por riesgo de cartera:

```
CRPUI_unitario_m = (rcpui × VPUI_m-1) / (VR_m-1 × CU_m-1)   [COP/kWh]

Donde:
  rcpui  = Prima de riesgo de cartera (por defecto: $0.030 COP/kWh)
  VPUI   = Volumen de áreas especiales (Paso 3)
  VR_m-1 = Demanda del mercado rezago m-1
  CU_m-1 = Costo unitario rezago m-1
```

**Esquema Competitivo** (mecanismo competitivo definitivo) — cargo fijo:

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

## 11. Metodología y Fuentes de Datos

- **Datos fuente:** PostgreSQL (BD del SIN/XM), tabla `fact_hourly_*` y dimensiones `dim_*`. Conexión verificada por logs en `logs/pui_YYYYMMDD.log`.
- **Pronóstico:** Google TimesFM 3.0 (modo offline, sin peticiones HTTP tras descarga inicial).
- **Parámetros regulatorios:** Resolución CREG 101 121 de 2026 (Artículos 11 y 12).
- **Modelo:** Arquitectura MVC en Python, principios SOLID, logger centralizado con rotación diaria en `logs/`.

## 12. Glosario de Términos

> Definiciones para facilitar la comprensión del documento a auditores, gerentes financieros y áreas comerciales.

| Término | Sigla | Definición |
|---|---|---|
| **PUI** | PUI | Prestador de Última Instancia. Mecanismo transitorio por el cual los comercializadores deben asumir la atención de usuarios huérfanos y girar el valor del servicio al Comercializador Incumbente del Operador de Red (CIOR) antes de que opere el mecanismo competitivo (Resolución 101 121 de 2026, Artículos 11 y 12).
| **CIOR** | CIOR | Comercializador Incumbente del Operador de Red. Es el agente designado para recibir los giros del PUI de parte de los CNIORs. En este estudio, es ENEL Colombia S.A. E.S.P.
| **CNIOR** | CNIOR | Comercializador No Integrado con el Operador de Red. Son los comercializadores puros del MEM (sin generación propia) que participan en este estudio. Compran toda su energía en el mercado mayorista y son responsables de girar el PUI al CIOR. Asumen el riesgo de incobrabilidad sobre los giros.
| **ACCE** | ACCE | Asociación Colombiana de Comercializadores de Energía. Cliente del estudio; representa los intereses de los comercializadores independientes (CNIOR) y usa este análisis como soporte regulatorio ante la CREG.
| **Sobrecosto** | — | Diferencia entre el monto total que el agente debe girar al CIOR y el monto que efectivamente logra recaudar de sus usuarios. Representa la pérdida financiera por incobrabilidad.
| **Flujo Neto de Caja** | — | Resultado de restar los egresos por giros al CIOR menos el recaudo efectivo. Si es negativo, el agente está financiando la diferencia.
| **Recaudo Efectivo** | — | Porcentaje del PUI que el agente realmente logra cobrar a sus usuarios finales.Depende del factor de recaudo configurado (por defecto 92%).
| **Incobrabilidad** | — | Porcentaje del monto facturado que no se logra cobrar. Es la principal causa del sobrecosto en el mecanismo PUI.
| **Cobertura de Demanda** | — | Porcentaje de la demanda de energía del agente que está cubierta por contratos bilaterales de compra vs. lo que se compra en bolsa spot. A mayor cobertura por contratos, menor exposición a la volatilidad del mercado.
| **Bolsa Spot** | — | Mercado de compra-venta de energía a precio diario (PMEM). Es el precio de referencia del mercado eléctrico colombiano.
| **Contratos Bilaterales** | — | Acuerdos privados de compra de energía a precio fijo o indexado, que protegen al comercializador de la volatilidad del precio spot.
| **Áreas Especiales** | — | Zonas geográficas del país donde el PUI se aplica sobre un porcentaje de la demanda (por defecto 10%). Están definidas por la CREG.
| **rcpui** | rcpui | Prima de riesgo de cartera. Es un cargo adicional (en COP/kWh) que compensa el riesgo de no cobro del PUI. Por defecto: $0.030/kWh.
| **cfpui** | cfpui | Cargo fijo competitivo. Componente del PUI que representa el costo de la prestación del servicio en el mecanismo competitivo definitivo. Por defecto: $0.025/kWh.
| **Esquema Competitivo vs Transitorio** | — | El esquema transitorio (Artículos 11 y 12 de la Resolución 101 121 de 2026) impone tarifas reguladas ex-ante y giros obligatorios independientes del recaudo, mientras que el competitivo define el cargo por subasta de ofertas eficientes. Por defecto: Transitorio.
| **TimesFM** | — | Google TimesFM 3.0. Modelo de inteligencia artificial de pronóstico de series temporales utilizado para proyectar la demanda y cobertura de energía a futuro.
| **MEM** | MEM | Mercado Eléctrico Mayorista. El mercado mayorista de comercialización de energía eléctrica en Colombia, regulado por la CREG.
| **CREG** | CREG | Comisión de Regulación de Energía y Gas. Ente regulador del sector eléctrico y gasífero en Colombia.
| **SIN** | SIN | Sistema Interconectado Nacional. La red eléctrica nacional de Colombia, administrada por el operador XM.
| **PMEM** | PMEM | Precio Marginal de Energía en el Mercado. El precio de referencia diario de la energía en el MEM.
| **Forecast / Pronóstico** | — | Predicción de valores futuros basada en modelos estadísticos o de inteligencia artificial. En este estudio se usa para proyectar la demanda y cobertura a futuro.

---

_Documento generado automáticamente. Carpetas individuales por agente en `output/<SIGLA>/`._
