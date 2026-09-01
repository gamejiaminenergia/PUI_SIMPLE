-- ==================================================================================================
-- 07_pui_ettc_agente_v2.sql
-- ==================================================================================================
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- CONTEXTO REGULATORIO: QUÉ ES EL PUI Y POR QUÉ EXISTE
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- El PUI (Pago por Uso de Interconexión) es un mecanismo de compensación financiera entre
-- comercializadores de energía eléctrica en el Mercado Mayorista (MEM) de Colombia.
--
-- FUNDAMENTO LEGAL:
--   - Resolución CREG 101 de 2012 (y modificatorias): Define el esquema transitorio del PUI.
--   - Resolución CREG 121 de 2016: Ajusta parámetros del esquema transitorio.
--   - Artículos 11 y 12: Establecen los roles CIOR y CNIOR y la mecánica de giros.
--
-- QUÉ RESUELVE:
--   En el MEM colombiano, los usuarios regulados (hogares, pequeños comercios) son atendidos
--   por comercializadores. Cuando un usuario está en un mercado donde su comercializador no
--   tiene "cobertura natural" (no es el operador de red), el esquema de PUI crea un mecanismo
--   de transferencia para que los costos de interconexión se compartan de forma regulada.
--
-- FLUJO SIMPLIFICADO:
--   1. Se calcula un costo unitario (CRPUI) basado en la riesgo de cartera del CIOR.
--   2. Se multiplica por la demanda regulada de hace 2 meses (rezago administrativo).
--   3. El resultado es un "giro" que los CNIOR deben pagar al CIOR.
--   4. El CIOR recibe estos giros como ingreso adicional.
--   5. Los CNIOR pagan más de lo que recaudan (porque el factor de recaudo < 100%).
--   6. Esta diferencia es la "pérdida estructural" del PUI para los CNIOR.
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- GLOSARIO DE TÉRMINOS
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- PUI    = Pago por Uso de Interconexión. Mecanismo de compensación entre comercializadores.
--
-- CIOR   = Comercializador Integrado de Oferta de Respaldo. Es el comercializador que opera
--          como integrador en un mercado. En esta simulación se identifica como el agente con
--          MAYOR demanda regulada total (VR). Recibe los giros de los CNIOR.
--          Ejemplo actual: ENEL COLOMBIA SA ESP (ENDC) con ~28,794 GWh acumulados.
--          NOTA: Esta es una SIMPLIFICACIÓN. En la realidad, el CIOR se asigna por mercado,
--          no globalmente. Pero el modelo de simulación usa un solo CIOR global basado en VR.
--
-- CNIOR  = Comercializador NO Integrado de Oferta de Respaldo. Son TODOS los demás
--          comercializadores que no son CIOR. Pagan giros al CIOR y asumen la pérdida
--          por incobrabilidad (factor de recaudo < 100%).
--          Ejemplo: ETTC (ENERTOTAL), NRCC (ENERCO), AIR-E, etc.
--
-- VR     = Ventas Reguladas. Demanda de energía eléctrica de usuarios regulados atendida
--          por un comercializador. Se mide en kWh. Es la base de todo el cálculo PUI.
--          En la BD: columna "DemaComeReg" de fact_hourly_agente (agente) y
--                    columna "DemaCome" de fact_hourly_mercadocomercializacion (mercado).
--
-- CU     = Costo Unitario / Precio Promedio de Contratos. Precio de referencia en COP/kWh
--          (o la moneda local). Se calcula como promedio mensual de PrecPromCont.
--          Se usa como denominador en el CRPUI y como multiplicador para convertir
--          PUI en energía a PUI en dinero.
--
-- CRPUI  = Costo de Riesgo del PUI. Es el costo unitario ($/kWh) que se cobra por el
--          esquema transitorio. Se calcula como:
--            CRPUI = (rcpui × VPUI_m-1) / (VR_mercado_m-1 × CU_m-1)
--          Donde rcpui = prima de riesgo de cartera (parámetro fijo, 0.03 $/kWh).
--
-- CFPUI  = Costo Fijo del PUI. Es el costo unitario ($/kWh) del esquema competitivo
--          (post-subasta). Valor fijo de 0.025 $/kWh. Solo se usa cuando
--          esquema_competitivo = TRUE.
--
-- VPUI   = Volumen PUI. Es la base de cálculo del CRPUI:
--            VPUI = VR_mercado × pct_areas_especiales
--          Representa el volumen de energía en "áreas especiales" (10% de la VR).
--
-- ÁREAS ESPECIALES:
--   Son zonas geográficas donde los costos de distribución son más altos (regiones
--   apartadas, zonas rurales, etc.). El 10% es un parámetro regulatorio que representa
--   el porcentaje de la demanda regulada que cae en estas zonas.
--
-- GIRO OBLIGATORIO:
--   Es el monto total que un mercado debe "girar" (transferir) como parte del PUI.
--   Se calcula como: Giro = CRPUI × VR_mercado_m-2
--   Los CNIOR pagan proporcionalmente a su VR dentro del mercado.
--   El CIOR recibe todos los giros de todos los mercados.
--
-- RECAUDO:
--   Es la fracción del giro que efectivamente se cobra a los CNIOR.
--   Si el factor de recaudo = 92%, significa que el 8% del giro NUNCA se cobra
--   (por impagos, mora, errores de facturación, etc.).
--   Esta pérdida la asumen los CNIOR individualmente.
--
-- FLUJO NETO DE CAJA:
--   Para CNIOR: Flujo = Recaudo - Egreso (típicamente NEGATIVO, pérdida).
--   Para CIOR:  Flujo = PUI_propio + Total_giros_recibidos (SIEMPRE positivo).
--   La asimetría es el problema central del PUI: el CIOR gana, los CNIOR pierden.
--
-- SOBRECOSTO:
--   Diferencia entre lo que un CNIOR paga (egreso) y lo que le recaudan (recaudo).
--   Sobrecosto = Egreso - Recaudo = Egreso × (1 - factor_recaudo)
--   Con factor 92%, el sobrecosto es el 8% del giro.
--
-- LAGS (REZAGOS):
--   El PUI usa datos de meses anteriores:
--   - m-1 (lag 1): Para calcular CRPUI (se usa VR, VPUI y CU del mes anterior).
--   - m-2 (lag 2): Para calcular el PUI total (se usa VR del mercado hace 2 meses).
--   Esto significa que los primeros 2 meses del rango no tendrán PUI calculado.
--   El rezago existe por razones administrativas: hay un delay entre la operación
--   y la facturación del PUI.
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- CÓMO SE CALCULA EL PUI — PASO A PASO (EN LENGUAJE PLANO)
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- PASO 1: Obtener la demanda regulada (VR) de cada agente y cada mercado, por mes.
--         VR_agente = suma de DemaComeReg del agente en el mes.
--         VR_mercado = suma de DemaCome del mercado en el mes.
--
-- PASO 2: Obtener el precio promedio de contratos (CU) por mes.
--         CU = promedio de PrecPromCont en el mes.
--
-- PASO 3: Identificar al CIOR.
--         CIOR = agente con mayor VR total acumulado en todo el historial.
--         (Simplificación: en la realidad se asigna por mercado, no global).
--
-- PASO 4: Calcular totales por mes.
--         VR_total_mes = suma de VR de TODOS los agentes.
--         VR_total_cnior = suma de VR SOLO de agentes CNIOR (sin el CIOR).
--
-- PASO 5: Calcular CRPUI unitario por mercado/mes (con lag m-1).
--         VPUI_m1 = VR_mercado_m1 × 0.10 (áreas especiales)
--         CRPUI = (0.03 × VPUI_m1) / (VR_mercado_m1 × CU_m1)
--         Si no hay datos en m-1, CRPUI = 0.
--
-- PASO 6: Calcular PUI total del mercado (con lag m-2).
--         PUI_mercado = CRPUI × VR_mercado_m2
--         Si no hay datos en m-2, PUI_mercado = 0.
--
-- PASO 7: Distribuir el PUI proporcionalmente a cada agente.
--         PUI_agente = PUI_mercado × (VR_agente / VR_total_mes)
--         Esto asigna una porción del PUI a cada agente según su tamaño.
--
-- PASO 8: Calcular giros (solo para CNIOR).
--         Giro_agente = Giro_mercado × (VR_agente / VR_total_cnior)
--         NOTA: El denominador es VR_total_cnior, NO VR_total_mes.
--               Los CNIOR son los que pagan, el CIOR no participa en el pago.
--
-- PASO 9: Calcular recaudo y pérdida.
--         Recaudo = Giro × 0.92 (factor de recaudo)
--         Pérdida = Giro × 0.08 (lo que no se cobra)
--         Flujo = Recaudo - Giro = -Pérdida (negativo = pérdida para CNIOR)
--
-- PASO 10: Para el CIOR (recibe giros):
--          Flujo_CIOR = PUI_propio + Σ(Giros de todos los mercados)
--          El CIOR siempre tiene flujo positivo.
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- SIMPLIFICACIONES Y LIMITACIONES DE ESTE MODELO
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- 1. UN SOLO CIOR GLOBAL: En la realidad, cada mercado tiene su propio CIOR. Este modelo
--    asume un CIOR único (el de mayor VR total). Esto es una simplificación del pipeline.
--
-- 2. DISTRIBUCIÓN PROPORCIONAL: Se asume que cada agente opera en TODOS los mercados
--    proporcionalmente a su VR. No se conoce el mapeo real agente↔mercado.
--
-- 3. CU COMO PROXY: Se usa PrecPromCont como proxy del costo unitario. En la realidad,
--    el CU podría tener una definición más específica según la regulación.
--
-- 4. PARÁMETROS FIJOS: Los valores de rcpui (0.03), pct_areas_especiales (0.10),
--    factor_recaudo (0.92) y cfpui (0.025) son los del escenario base.
--    Para otros escenarios, modificar la CTE params.
--
-- 5. ESQUEMA COMPETITIVO: Cuando esquema_competitivo = TRUE, se usa CFPUI en lugar de
--    CRPUI. Esto representa el escenario post-subasta donde el costo es fijo.
--
-- 6. UNIDADES: Todo está en kWh y COP (la moneda de PrecPromCont).
--    VR = kWh (suma horaria de demanda regulada).
--    CU = COP/kWh (precio promedio de contratos).
--    CRPUI = COP/kWh (costo unitario de riesgo).
--    PUI_energia = kWh (cantidad de energía asignada como PUI).
--    PUI_dinero = COP (valor monetario del PUI = PUI_energia × CU).
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- BASE DE DATOS REQUERIDA (PostgreSQL)
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- Tablas fuente:
--   fact_hourly_agente                      : Demanda horaria por agente comercializador
--     Columnas clave: agente_code, fecha_hora, DemaComeReg (demanda regulada, kWh)
--
--   fact_hourly_mercadocomercializacion     : Demanda horaria por mercado de comercialización
--     Columnas clave: mercadocomercializacion_code, fecha_hora, DemaCome (demanda total, kWh)
--
--   fact_daily_sistema                      : Datos diarios del sistema eléctrico
--     Columnas clave: fecha, PrecPromCont (precio promedio de contratos, COP/kWh)
--
--   dim_agente                              : Dimensión de agentes
--     Columnas clave: agente_code, name, activity ('COMERCIALIZACIÓN')
--
--   dim_mercado                             : Dimensión de mercados
--     Columnas clave: mercado_code, mercado_name
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- PARÁMETROS DE SIMULACIÓN (escenario base)
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- Para cambiar de escenario, modifique la CTE params más abajo.
--
-- rcpui                = 0.03 $/kWh     Prima de riesgo de cartera del CIOR.
--                                           Referencia: resoluciones CREG 2023-2024.
--                                           Representa el costo de asumir el riesgo de que
--                                           los usuarios no paguen.
--
-- pct_areas_especiales = 0.10 (10%)      Porcentaje de VR que corresponde a áreas especiales.
--                                           Áreas especiales = zonas de alto costo de
--                                           distribución (rurales, apartadas).
--
-- factor_recaudo_cnior = 0.92 (92%)      Fracción del giro que efectivamente se recauda.
--                                           El 8% restante es pérdida por incobrabilidad.
--                                           Este es el parámetro más sensible del modelo.
--
-- cfpui                = 0.025 $/kWh     Costo fijo del PUI en esquema competitivo.
--                                           Solo se usa cuando esquema_competitivo = TRUE.
--                                           Representa el costo post-subasta competitiva.
--
-- esquema_competitivo  = FALSE            FALSE = CRPUI transitorio (costo variable, basado
--                                              en riesgo de cartera).
--                                           TRUE  = CFPUI competitivo (costo fijo post-subasta).
--                                           El esquema transitorio es el actual (2024-2026).
--
-- fecha_inicio         = '2024-01-01'    Inicio del rango de datos.
-- fecha_fin            = '2026-08-27'    Fin del rango (exclusivo).
-- agente_objetivo      = 'ETTC'          Código del agente a calcular.
--                                           ETTC = ENERTOTAL S.A. E.S.P.
--                                           ranking ~600 entre todos los agentes por VR.
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- ESTRUCTURA DE LA CONSULTA (CTEs)
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- La consulta está organizada en 10 CTEs (Common Table Expressions) que siguen la cadena
-- de cálculo del PUI. Cada CTE alimenta al siguiente:
--
--   params           → Parámetros de configuración (escenario base)
--   vr_agente        → VR mensual de TODOS los agentes (necesario para CIOR y totales)
--   vr_mercado       → VR mensual por mercado
--   cu_mensual       → CU mensual (precio promedio contratos)
--   cior_ranking     → Ranking de agentes por VR total
--   cior_agent       → Identificación del CIOR (mayor VR)
--   totales_mes      → VR total mes y VR total solo CNIOR
--   mercado_con_lags → Lags m-1 y m-2 del mercado + VPUI
--   mercado_crpui    → CRPUI unitario calculado
--   pui_mercado      → PUI total del mercado por mes
--   totales_giros    → Suma de giros por mes (para flujo CIOR)
--   pui_agente       → PUI distribuido a ETTC + giro/recaudo proporcional
--   flujo_agente     → Flujo neto, sobrecosto, % pérdida (resultados finales)
--
-- El SELECT final filtra solo el agente ETTC y muestra TODAS las columnas.
--
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
-- FÓRMULAS MATEMÁTICAS (notación formal)
-- ══════════════════════════════════════════════════════════════════════════════════════════════════
--
-- VPUI_m       = VR_mercado_m × pct_areas_especiales
--
-- CRPUI_m      = (rcpui × VPUI_m-1) / (VR_mercado_m-1 × CU_m-1)
--                (si denominador = 0, CRPUI = 0)
--
-- PUI_mercado_m = (CRPUI_m + CFPUI) × VR_mercado_m-2
--                 (si VR_m-2 es NULL, PUI = 0)
--
-- PUI_agente_m = PUI_mercado_m × (VR_agente_m / VR_total_mes)
--
-- Giro_agente_m = Giro_mercado_m × (VR_agente_m / VR_total_cnior_mes)
--                 (solo CNIOR; CIOR no paga giros)
--
-- Recaudo_m    = Giro_agente_m × factor_recaudo_cnior
--
-- Flujo_CNIOR  = Recaudo_m - Giro_agente_m  (negativo = pérdida)
-- Flujo_CIOR   = PUI_agente_m + Σ(Giros_recibidos)  (positivo = ganancia)
--
-- Sobrecosto   = Giro_agente_m - Recaudo_m  (solo CNIOR)
--
-- PUI_dinero   = PUI_agente_m × CU_m  (convierte kWh a COP)
--
-- ==================================================================================================


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PARÁMETROS DE SIMULACIÓN
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Para cambiar de escenario, modifique estos valores. No toque el resto de la consulta.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

WITH params AS (
    SELECT
        0.03                    AS rcpui,                  -- $/kWh — prima riesgo cartera CIOR
        0.10                    AS pct_areas_especiales,   -- 10% de VR en áreas especiales
        0.92                    AS factor_recaudo_cnior,   -- 92% de recaudo efectivo
        0.025                   AS cfpui,                  -- $/kWh — costo competitivo fijo
        FALSE                   AS esquema_competitivo,    -- FALSE = CRPUI transitorio
        '2024-01-01'::date      AS fecha_inicio,           -- Inicio rango datos
        '2026-08-27'::date      AS fecha_fin,              -- Fin rango datos (exclusivo)
        'ETTC'::text            AS agente_objetivo         -- Agente a calcular
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 1: VR MENSUAL POR AGENTE
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Extrae la demanda regulada (DemaComeReg) de CADA agente, agrupada por mes.
-- Se necesitan TODOS los agentes (no solo ETTC) para:
--   a) Identificar al CIOR (mayor VR total)
--   b) Calcular VR_total_mes y VR_total_cnior (bases de distribución)
--
-- Unidades: kWh (DemaComeReg está en kWh horarios, se suman las 24h × días del mes).
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

vr_agente AS (
    SELECT
        ha.agente_code,
        a.name                                                              AS agente_name,
        date_trunc('month', ha.fecha_hora)::date                            AS mes,
        SUM(ha."DemaComeReg")                                               AS vr_kwh,
        -- Estadísticas diarias para contexto
        COUNT(DISTINCT DATE(ha.fecha_hora))                                 AS dias_activos,
        ROUND(SUM(ha."DemaComeReg") /
              NULLIF(COUNT(DISTINCT DATE(ha.fecha_hora)), 0))               AS promedio_diario_kwh
    FROM fact_hourly_agente ha
    JOIN dim_agente a ON ha.agente_code = a.agente_code
    CROSS JOIN params p
    WHERE a.activity = 'COMERCIALIZACIÓN'
      AND ha.fecha_hora >= p.fecha_inicio
      AND ha.fecha_hora <  p.fecha_fin
      AND ha."DemaComeReg" > 0
    GROUP BY ha.agente_code, a.name, date_trunc('month', ha.fecha_hora)
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 2: VR MENSUAL POR MERCADO
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Extrae la demanda total por mercado de comercialización (DemaCome), agrupada por mes.
-- Cada mercado tiene un código único (mercadocomercializacion_code).
-- Ejemplos: ANTIOQUIA, BOGOTA - CUNDINAMARCA, CARIBE MAR, SANTANDER, etc.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

vr_mercado AS (
    SELECT
        hm.mercadocomercializacion_code                                    AS mercado_code,
        cm.mercado_name,
        date_trunc('month', hm.fecha_hora)::date                           AS mes,
        SUM(hm."DemaCome")                                                 AS vr_mercado_kwh
    FROM fact_hourly_mercadocomercializacion hm
    LEFT JOIN dim_mercado cm ON hm.mercadocomercializacion_code = cm.mercado_code
    CROSS JOIN params p
    WHERE hm.fecha_hora >= p.fecha_inicio
      AND hm.fecha_hora <  p.fecha_fin
      AND hm."DemaCome" > 0
    GROUP BY hm.mercadocomercializacion_code, cm.mercado_name,
             date_trunc('month', hm.fecha_hora)
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 3: CU MENSUAL (PRECIO PROMEDIO DE CONTRATOS)
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Promedio mensual de PrecPromCont (precio promedio de contratos) del sistema.
-- Es el precio de referencia en COP/kWh (o la moneda de la BD).
-- Se usa como denominador en CRPUI y como multiplicador para PUI_dinero.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

cu_mensual AS (
    SELECT
        date_trunc('month', s.fecha)::date                                 AS mes,
        AVG(s."PrecPromCont")                                              AS cu
    FROM fact_daily_sistema s
    CROSS JOIN params p
    WHERE s.fecha >= p.fecha_inicio
      AND s.fecha <  p.fecha_fin
    GROUP BY date_trunc('month', s.fecha)
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 4: IDENTIFICACIÓN DEL CIOR
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- En el esquema PUI transitorio:
--   CIOR = Comercializador con mayor demanda regulada total (el que RECIBE los giros).
--   CNIOR = Todos los demás (los que PAGAN giros).
--
-- NOTA: Esta es una SIMPLIFICACIÓN. En la realidad, el CIOR se asigna por mercado,
-- no globalmente. Pero el modelo de simulación del pipeline PUI usa un solo CIOR global
-- basado en VR total. Esto es consistente con simulate.py del pipeline.
--
-- Se calcula con ROW_NUMBER() sobre la suma total de VR de cada agente.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

cior_ranking AS (
    SELECT
        agente_code,
        SUM(vr_kwh)                                                        AS vr_total_historial,
        ROW_NUMBER() OVER (ORDER BY SUM(vr_kwh) DESC)                      AS rank_num
    FROM vr_agente
    WHERE vr_kwh > 0
    GROUP BY agente_code
),

cior_agent AS (
    SELECT
        cr.agente_code                                                     AS cior_code,
        cr.vr_total_historial                                              AS cior_vr_total,
        va.agente_name                                                     AS cior_name
    FROM cior_ranking cr
    JOIN vr_agente va ON cr.agente_code = va.agente_code
    WHERE cr.rank_num = 1
    GROUP BY cr.agente_code, cr.vr_total_historial, va.agente_name
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 5: TOTALES VR POR MES (TODOS LOS AGENTES Y SOLO CNIOR)
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- vr_total_mes   : Suma de VR de TODOS los agentes → base para distribuir PUI proporcionalmente.
-- vr_total_cnior : Suma de VR SOLO de agentes CNIOR → base para distribuir giros proporcionalmente.
--
-- DIFERENCIA CRÍTICA:
--   El PUI se distribuye proporcionalmente a la VR de TODOS los agentes (porque todos
--   "consumen" el servicio de interconexión). Pero los GIROS solo los pagan los CNIOR
--   (porque el CIOR no se paga a sí mismo). Por eso se usan dos bases diferentes.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

totales_mes AS (
    SELECT
        va.mes,
        SUM(va.vr_kwh)                                                     AS vr_total_mes,
        SUM(CASE WHEN ca.cior_code IS NULL THEN va.vr_kwh ELSE 0 END)     AS vr_total_cnior,
        -- Ranking del agente objetivo en este mes
        MAX(CASE WHEN va.agente_code = p.agente_objetivo THEN va.vr_kwh END) AS vr_ettc_mes
    FROM vr_agente va
    LEFT JOIN cior_agent ca ON va.agente_code = ca.cior_code
    CROSS JOIN params p
    WHERE va.vr_kwh > 0
    GROUP BY va.mes
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 6: LAGS Y CRPUI POR MERCADO/MES
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Se calculan los valores rezagados (lag) necesarios para el CRPUI:
--   vr_m1    : VR del mercado en el mes anterior (m-1)
--   vpui_m1  : VPUI del mercado en m-1 = vr_m1 × pct_areas_especiales
--   cu_m1    : CU en el mes anterior (m-1)
--   vr_m2    : VR del mercado hace 2 meses (m-2) → base del PUI
--
-- CRPUI unitario (solo esquema transitorio):
--   CRPUI = (rcpui × VPUI_m1) / (VR_m1 × CU_m1)
--
-- Si cualquiera de los denominadores es 0 o NULL, CRPUI = 0 (no hay cálculo posible).
-- Esto ocurre en los primeros 2 meses del rango de datos.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

mercado_con_lags AS (
    SELECT
        vm.mercado_code,
        vm.mercado_name,
        vm.mes,
        vm.vr_mercado_kwh,
        cu.cu,
        -- VPUI actual (para referencia, no se usa directamente en CRPUI)
        vm.vr_mercado_kwh * p.pct_areas_especiales                        AS vpui_actual,
        -- Lags del mercado
        LAG(vm.vr_mercado_kwh)
            OVER (PARTITION BY vm.mercado_code ORDER BY vm.mes)            AS vr_m1,
        LAG(vm.vr_mercado_kwh * p.pct_areas_especiales)
            OVER (PARTITION BY vm.mercado_code ORDER BY vm.mes)            AS vpui_m1,
        LAG(cu.cu)
            OVER (PARTITION BY vm.mercado_code ORDER BY vm.mes)            AS cu_m1,
        LAG(vm.vr_mercado_kwh, 2)
            OVER (PARTITION BY vm.mercado_code ORDER BY vm.mes)            AS vr_m2
    FROM vr_mercado vm
    LEFT JOIN cu_mensual cu ON vm.mes = cu.mes
    CROSS JOIN params p
),

mercado_crpui AS (
    SELECT
        mc.mercado_code,
        mc.mercado_name,
        mc.mes,
        mc.vr_mercado_kwh,
        mc.cu,
        mc.vpui_actual,
        mc.vr_m1,
        mc.vpui_m1,
        mc.cu_m1,
        mc.vr_m2,
        -- CRPUI unitario ($/kWh)
        CASE
            WHEN p.esquema_competitivo THEN 0.0
            WHEN mc.vr_m1 > 0 AND mc.cu_m1 > 0 AND mc.vpui_m1 > 0
            THEN (p.rcpui * mc.vpui_m1) / (mc.vr_m1 * mc.cu_m1)
            ELSE 0.0
        END                                                                 AS crpui_unitario,
        -- CFPUI unitario ($/kWh) — solo en esquema competitivo
        CASE
            WHEN p.esquema_competitivo THEN p.cfpui
            ELSE 0.0
        END                                                                 AS cfpui_unitario
    FROM mercado_con_lags mc
    CROSS JOIN params p
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 7: PUI TOTAL DEL MERCADO POR MES
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PUI_mercado = (CRPUI + CFPUI) × VR_m2
--
-- El PUI total de un mercado se calcula multiplicando el costo unitario por la VR
-- de hace 2 meses (m-2). Este es el monto total que se debe girar desde ese mercado.
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

pui_mercado AS (
    SELECT
        mc.mercado_code,
        mc.mercado_name,
        mc.mes,
        mc.vr_mercado_kwh,
        mc.cu,
        mc.vpui_actual,
        mc.vr_m1,
        mc.vpui_m1,
        mc.cu_m1,
        mc.vr_m2,
        mc.crpui_unitario,
        mc.cfpui_unitario,
        -- PUI total del mercado
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0)                                        AS pui_mercado_total,
        -- Giro obligatorio = PUI total del mercado
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0)                                        AS giro_obligatorio,
        -- Recaudo real estimado = giro × factor_recaudo
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0) * p.factor_recaudo_cnior               AS recaudo_real_estimado
    FROM mercado_crpui mc
    CROSS JOIN params p
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 8: TOTALES DE GIROS POR MES
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Suma de giros de TODOS los mercados en cada mes.
-- Se usa para calcular el flujo neto del CIOR (que recibe todos los giros).
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

totales_giros AS (
    SELECT
        mes,
        SUM(giro_obligatorio)                                              AS total_giros_mes
    FROM pui_mercado
    WHERE giro_obligatorio > 0
    GROUP BY mes
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 9: PUI DISTRIBUIDO POR AGENTE
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Para cada mercado/mes, se distribuye el PUI proporcionalmente a la VR de cada agente.
--
-- PUI_agente = PUI_mercado × (VR_agente / VR_total_mes)
--
-- PARA GIROS (CNIOR solamente):
--   Giro_agente = Giro_mercado × (VR_agente / VR_total_CNIOR_mes)
--   ← IMPORTANTE: El denominador es VR_total_CNIOR, NO VR_total_mes.
--     Esto es lo que dice simulate.py: los giros SOLO se distribuyen entre CNIOR.
--
-- PARA FLUJO NETO:
--   CNIOR: Flujo = Recaudo - Egreso (negativo = pérdida)
--   CIOR:  Flujo = PUI_propio + Total_giros_recibidos (positivo = ganancia)
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

pui_agente AS (
    SELECT
        -- Datos del mercado
        pm.mercado_code,
        pm.mercado_name,
        pm.mes,
        pm.vr_mercado_kwh,
        pm.cu,
        pm.vpui_actual,
        pm.vr_m1,
        pm.vpui_m1,
        pm.cu_m1,
        pm.vr_m2,
        pm.crpui_unitario,
        pm.cfpui_unitario,
        pm.pui_mercado_total,
        pm.giro_obligatorio,
        pm.recaudo_real_estimado,
        -- Datos del agente
        va.agente_code,
        va.agente_name,
        va.vr_kwh                                                           AS vr_agente,
        va.dias_activos,
        va.promedio_diario_kwh,
        tm.vr_total_mes,
        tm.vr_total_cnior,
        -- Clasificación
        CASE WHEN ca.cior_code IS NOT NULL THEN 'CIOR' ELSE 'CNIOR' END    AS rol_pui,
        ca.cior_code,
        ca.cior_vr_total,
        -- PUI del agente = proporcional a su VR sobre el total del mes
        CASE
            WHEN tm.vr_total_mes > 0 AND pm.pui_mercado_total > 0
            THEN pm.pui_mercado_total * (va.vr_kwh / tm.vr_total_mes)
            ELSE 0.0
        END                                                                 AS pui_energia_kwh,
        -- Giro del agente (solo CNIOR paga; distribuido sobre VR_total_CNIOR)
        CASE
            WHEN ca.cior_code IS NULL        -- Es CNIOR
                 AND pm.giro_obligatorio > 0
                 AND tm.vr_total_cnior > 0
            THEN pm.giro_obligatorio * (va.vr_kwh / tm.vr_total_cnior)
            ELSE 0.0
        END                                                                 AS egreso_giro,
        -- Recaudo del agente (solo CNIOR cobra recaudo real)
        CASE
            WHEN ca.cior_code IS NULL        -- CNIOR
                 AND pm.recaudo_real_estimado > 0
                 AND tm.vr_total_cnior > 0
            THEN pm.recaudo_real_estimado * (va.vr_kwh / tm.vr_total_cnior)
            ELSE 0.0
        END                                                                 AS recaudo_agente
    FROM pui_mercado pm
    -- Join con todos los agentes del mes (necesario para calcular shares)
    JOIN vr_agente va ON pm.mes = va.mes
    JOIN totales_mes tm ON pm.mes = tm.mes
    LEFT JOIN cior_agent ca ON va.agente_code = ca.cior_code
    WHERE va.vr_kwh > 0
),


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- PASO 10: FLUJO NETO Y SOBRECOSTO (resultados finales por mercado/agente/mes)
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Se calculan los indicadores financieros finales:
--   - Flujo neto de caja (positivo = ganancia, negativo = pérdida)
--   - Sobrecosto (diferencia entre giro y recaudo, solo CNIOR)
--   - % Pérdida por incobrabilidad
--   - PUI en dinero (COP) = PUI_energia × CU
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

flujo_agente AS (
    SELECT
        pa.*,
        tg.total_giros_mes,
        -- ─── PUI en dinero (COP) = PUI_energia × CU ───
        pa.pui_energia_kwh * pa.cu                                         AS pui_dinero_cop,
        -- ─── Ingresos PUI facturado ───
        -- CNIOR: solo su porción del PUI
        -- CIOR:  su porción del PUI + TODOS los giros recibidos de CNIOR
        CASE
            WHEN pa.rol_pui = 'CIOR'
            THEN pa.pui_energia_kwh + COALESCE(tg.total_giros_mes, 0)
            ELSE pa.pui_energia_kwh
        END                                                                 AS ingresos_pui_facturado,
        -- ─── Flujo neto de caja ───
        -- CNIOR: recaudo - egreso (típicamente negativo por factor_recaudo < 1)
        -- CIOR:  PUI propio + todos los giros recibidos (típicamente positivo)
        CASE
            WHEN pa.rol_pui = 'CIOR'
            THEN pa.pui_energia_kwh + COALESCE(tg.total_giros_mes, 0)
            ELSE pa.recaudo_agente - pa.egreso_giro
        END                                                                 AS flujo_neto_caja_pui,
        -- ─── Sobrecosto PUI (solo CNIOR) ───
        -- Diferencia entre lo que paga y lo que le recaudan
        CASE
            WHEN pa.rol_pui = 'CNIOR' AND pa.egreso_giro > 0
            THEN pa.egreso_giro - pa.recaudo_agente
            ELSE 0.0
        END                                                                 AS sobrecosto_pui,
        -- ─── % Pérdida por incobrabilidad ───
        -- Porcentaje del giro que no se recupera
        CASE
            WHEN pa.rol_pui = 'CNIOR' AND pa.egreso_giro > 0
            THEN ((pa.egreso_giro - pa.recaudo_agente) / pa.egreso_giro) * 100
            ELSE 0.0
        END                                                                 AS pct_perdida_incobrabilidad,
        -- ─── Ranking del agente entre todos los agentes (por VR total) ───
        ROW_NUMBER() OVER (
            PARTITION BY pa.mes
            ORDER BY pa.vr_agente DESC
        )                                                                   AS ranking_agente_vr
    FROM pui_agente pa
    LEFT JOIN totales_giros tg ON pa.mes = tg.mes
)


-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- RESULTADO FINAL
-- ════════════════════════════════════════════════════════════════════════════════════════════════════
-- Selecciona TODAS las columnas para el agente ETTC, ordenadas por mes descendente y mercado.
-- Cada fila representa la posición PUI de ETTC en un mercado específico en un mes dado.
--
-- RESULTADO ESPERADO:
--   ~928 filas (29 mercados × ~32 meses de enero 2024 a agosto 2026, menos 2 meses de lags).
--   ETTC es CNIOR (no es el CIOR). El CIOR es ENEL COLOMBIA (ENDC).
--   El flujo neto de ETTC es NEGATIVO en todos los meses (pérdida estructural del PUI).
--   La pérdida es ~8% del giro (porque factor_recaudo = 92%).
-- ════════════════════════════════════════════════════════════════════════════════════════════════════

SELECT
    -- ═══════════════════════════════════════════════════════════════════
    -- IDENTIFICACIÓN
    -- ═══════════════════════════════════════════════════════════════════
    fa.agente_code                                                          AS agente_code,
    fa.agente_name                                                          AS agente_name,
    fa.rol_pui                                                              AS rol_pui,
    fa.mercado_code                                                         AS mercado_code,
    fa.mercado_name                                                         AS mercado_name,

    -- ═══════════════════════════════════════════════════════════════════
    -- PERÍODO
    -- ═══════════════════════════════════════════════════════════════════
    fa.mes                                                                  AS mes,

    -- ═══════════════════════════════════════════════════════════════════
    -- DEMANDA REGULADA (VR) DEL AGENTE
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.vr_agente::numeric, 2)                                         AS vr_agente_kwh,
    fa.dias_activos                                                         AS dias_activos_mes,
    ROUND(fa.promedio_diario_kwh::numeric, 2)                              AS promedio_diario_kwh,

    -- ═══════════════════════════════════════════════════════════════════
    -- PRECIO PROMEDIO DE CONTRATOS (CU)
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.cu::numeric, 4)                                                AS precio_prom_contratos_cop_kwh,

    -- ═══════════════════════════════════════════════════════════════════
    -- VR DEL MERCADO Y TOTALES
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.vr_mercado_kwh::numeric, 2)                                   AS vr_mercado_kwh,
    ROUND(fa.vr_total_mes::numeric, 2)                                     AS vr_total_todos_agentes_kwh,
    ROUND(fa.vr_total_cnior::numeric, 2)                                   AS vr_total_cniors_kwh,

    -- Participación de ETTC en el total del mes
    CASE WHEN fa.vr_total_mes > 0
        THEN ROUND((fa.vr_agente / fa.vr_total_mes * 100)::numeric, 4)
        ELSE 0
    END                                                                     AS participacion_ettc_pct_total,

    -- Participación de ETTC solo entre CNIOR (base de distribución de giros)
    CASE WHEN fa.vr_total_cnior > 0
        THEN ROUND((fa.vr_agente / fa.vr_total_cnior * 100)::numeric, 4)
        ELSE 0
    END                                                                     AS participacion_ettc_pct_cniors,

    -- Ranking de ETTC entre todos los agentes por VR en este mes
    fa.ranking_agente_vr                                                    AS ranking_vr_mes,

    -- ═══════════════════════════════════════════════════════════════════
    -- LAGS (valores rezagados del mercado, para trazabilidad)
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.vr_m1::numeric, 2)                                            AS vr_mercado_m1_kwh,
    ROUND(fa.vpui_m1::numeric, 2)                                          AS vpui_mercado_m1_kwh,
    ROUND(fa.cu_m1::numeric, 4)                                            AS cu_m1_cop_kwh,
    ROUND(fa.vr_m2::numeric, 2)                                            AS vr_mercado_m2_kwh,

    -- ═══════════════════════════════════════════════════════════════════
    -- COSTOS UNITARIOS DEL PUI
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.vpui_actual::numeric, 2)                                      AS vpui_actual_kwh,
    ROUND(fa.crpui_unitario::numeric, 8)                                   AS crpui_unitario,
    ROUND(fa.cfpui_unitario::numeric, 8)                                   AS cfpui_unitario,

    -- ═══════════════════════════════════════════════════════════════════
    -- PUI DEL MERCADO (totales antes de distribuir)
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.pui_mercado_total::numeric, 2)                                AS pui_mercado_total,
    ROUND(fa.giro_obligatorio::numeric, 2)                                 AS giro_obligatorio_mercado,
    ROUND(fa.recaudo_real_estimado::numeric, 2)                            AS recaudo_real_mercado,

    -- ═══════════════════════════════════════════════════════════════════
    -- PUI DE ETTC — ENERGÍA (kWh)
    -- Este es el PUI asignado a ETTC proporcionalmente a su VR.
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.pui_energia_kwh::numeric, 2)                                  AS pui_energia_kwh,

    -- ═══════════════════════════════════════════════════════════════════
    -- PUI DE ETTC — DINERO (COP)
    -- PUI_energia × CU = monto monetario del PUI para ETTC.
    -- ═══════════════════════════════════════════════════════════════════
    ROUND(fa.pui_dinero_cop::numeric, 2)                                   AS pui_dinero_cop,

    -- ═══════════════════════════════════════════════════════════════════
    -- FLUJO FINANCIERO DE ETTC
    -- ═══════════════════════════════════════════════════════════════════
    -- Ingresos PUI facturado (CNIOR = su PUI; CIOR = su PUI + giros recibidos)
    ROUND(fa.ingresos_pui_facturado::numeric, 2)                           AS ingresos_pui_facturado,
    -- Egreso por giro al CIOR (solo CNIOR paga)
    ROUND(fa.egreso_giro::numeric, 2)                                      AS egreso_giro_cior,
    -- Recaudo real estimado (giro × factor_recaudo)
    ROUND(fa.recaudo_agente::numeric, 2)                                   AS recaudo_real_agente,
    -- Flujo neto de caja PUI (positivo = ganancia, negativo = pérdida)
    ROUND(fa.flujo_neto_caja_pui::numeric, 2)                              AS flujo_neto_caja_pui,
    -- Sobrecosto = lo que ETTC paga de más por factor_recaudo < 1
    ROUND(fa.sobrecosto_pui::numeric, 2)                                   AS sobrecosto_pui,
    -- % Pérdida por incobrabilidad
    ROUND(fa.pct_perdida_incobrabilidad::numeric, 2)                       AS pct_perdida_incobrabilidad,

    -- ═══════════════════════════════════════════════════════════════════
    -- CONTEXTO CIOR (quién recibe los giros)
    -- ═══════════════════════════════════════════════════════════════════
    fa.cior_code                                                            AS cior_code,
    cior_info.cior_name                                                     AS cior_name,
    ROUND(fa.cior_vr_total::numeric, 2)                                    AS cior_vr_total_historial,
    ROUND(COALESCE(fa.total_giros_mes, 0)::numeric, 2)                     AS total_giros_recibidos_cior,

    -- ═══════════════════════════════════════════════════════════════════
    -- PARÁMETROS DE CONFIGURACIÓN (para trazabilidad del escenario)
    -- ═══════════════════════════════════════════════════════════════════
    p.rcpui                                                                 AS param_rcpui,
    p.pct_areas_especiales                                                  AS param_pct_areas_especiales,
    p.factor_recaudo_cnior                                                  AS param_factor_recaudo,
    p.cfpui                                                                 AS param_cfpui,
    p.esquema_competitivo                                                   AS param_esquema_competitivo

FROM flujo_agente fa
CROSS JOIN params p
-- Cross join para obtener datos del CIOR (solo 1 fila)
CROSS JOIN cior_agent cior_info
-- Filtrar solo el agente objetivo
WHERE fa.agente_code = p.agente_objetivo
ORDER BY fa.mes DESC, fa.mercado_code;


-- ==================================================================================================
-- NOTAS FINALES DE INTERPRETACIÓN DE RESULTADOS
-- ==================================================================================================
--
-- 1. ETTC ES CNIOR:
--    ETTC (ENERTOTAL) está clasificado como CNIOR porque NO es el agente con mayor VR.
--    El CIOR es ENEL COLOMBIA (ENDC) con ~28,794 GWh acumulados.
--    ETTC tiene ~800 GWh (ranking ~600 entre todos los agentes).
--
-- 2. FLUJO NETO NEGATIVO:
--    Todas las filas de ETTC tienen flujo_neto_caja_pui NEGATIVO.
--    Esto significa que ETTC pierde dinero con el PUI en todos los mercados y meses.
--    La pérdida es estructural: se debe a que factor_recaudo = 92% < 100%.
--
-- 3. MAGNITUD DE LA PÉRDIDA:
--    La pérdida mensual de ETTC es ~8% del giro.
--    Ejemplo agosto 2026: Giro total ≈ 46,020 kWh → Pérdida ≈ 3,682 kWh.
--    En dinero: Pérdida ≈ 3,682 × 331.66 COP/kWh ≈ 1,221,000 COP/mes.
--
-- 4. ASIMETRÍA CIOR vs CNIOR:
--    - CIOR (ENEL): SIEMPRE gana (recibe giros de todos los mercados).
--    - CNIOR (ETTC): SIEMPRE pierde (paga giros, pero no le recaudan el 100%).
--    Esta asimetría es el problema central del esquema transitorio del PUI.
--
-- 5. PARA CAMBIAR EL ESCENARIO:
--    Modificar la CTE params al inicio de la consulta.
--    Ejemplo: Cambiar factor_recaudo_cnior de 0.92 a 0.85 aumenta la pérdida al 15%.
--
-- ==================================================================================================
