-- ==================================================================================================
-- CONSULTA PARAMETRIZADA PUI (Pago por Uso de Interconexión)
-- Basada en CREG 101/2012 y 121/2016
-- ==================================================================================================

WITH params AS (
    SELECT
        {rcpui}::numeric                    AS rcpui,                  -- $/kWh — prima riesgo cartera CIOR
        {pct_areas_especiales}::numeric    AS pct_areas_especiales,   -- Fracción de VR en áreas especiales (ej. 0.10)
        {factor_recaudo_cnior}::numeric    AS factor_recaudo_cnior,   -- Fracción de recaudo efectivo (ej. 0.92)
        {cfpui}::numeric                   AS cfpui,                  -- $/kWh — costo competitivo fijo
        {esquema_competitivo}::boolean     AS esquema_competitivo,    -- FALSE = CRPUI transitorio, TRUE = CFPUI competitivo
        '{fecha_inicio}'::date             AS fecha_inicio,           -- Inicio rango datos
        '{fecha_fin}'::date                AS fecha_fin,              -- Fin rango datos (exclusivo)
        '{agente_objetivo}'::text          AS agente_objetivo         -- Código del agente objetivo (ej. ETTC)
),

-- PASO 1: VR MENSUAL POR AGENTE
vr_agente AS (
    SELECT
        ha.agente_code,
        a.name                                                              AS agente_name,
        date_trunc('month', ha.fecha_hora)::date                            AS mes,
        SUM(ha."DemaComeReg")                                               AS vr_kwh,
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

-- PASO 2: VR MENSUAL POR MERCADO
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

-- PASO 3: CU MENSUAL (PRECIO PROMEDIO DE CONTRATOS)
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

-- PASO 4: IDENTIFICACIÓN DEL CIOR
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

-- PASO 5: TOTALES VR POR MES (TODOS LOS AGENTES Y SOLO CNIOR)
totales_mes AS (
    SELECT
        va.mes,
        SUM(va.vr_kwh)                                                     AS vr_total_mes,
        SUM(CASE WHEN ca.cior_code IS NULL THEN va.vr_kwh ELSE 0 END)     AS vr_total_cnior,
        MAX(CASE WHEN va.agente_code = p.agente_objetivo THEN va.vr_kwh END) AS vr_ettc_mes
    FROM vr_agente va
    LEFT JOIN cior_agent ca ON va.agente_code = ca.cior_code
    CROSS JOIN params p
    WHERE va.vr_kwh > 0
    GROUP BY va.mes
),

-- PASO 6: LAGS Y CRPUI POR MERCADO/MES
mercado_con_lags AS (
    SELECT
        vm.mercado_code,
        vm.mercado_name,
        vm.mes,
        vm.vr_mercado_kwh,
        cu.cu,
        vm.vr_mercado_kwh * p.pct_areas_especiales                        AS vpui_actual,
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
        CASE
            WHEN p.esquema_competitivo THEN 0.0
            WHEN mc.vr_m1 > 0 AND mc.cu_m1 > 0 AND mc.vpui_m1 > 0
            THEN (p.rcpui * mc.vpui_m1) / (mc.vr_m1 * mc.cu_m1)
            ELSE 0.0
        END                                                                 AS crpui_unitario,
        CASE
            WHEN p.esquema_competitivo THEN p.cfpui
            ELSE 0.0
        END                                                                 AS cfpui_unitario
    FROM mercado_con_lags mc
    CROSS JOIN params p
),

-- PASO 7: PUI TOTAL DEL MERCADO POR MES
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
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0)                                        AS pui_mercado_total,
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0)                                        AS giro_obligatorio,
        (mc.crpui_unitario + mc.cfpui_unitario)
            * COALESCE(mc.vr_m2, 0) * p.factor_recaudo_cnior               AS recaudo_real_estimado
    FROM mercado_crpui mc
    CROSS JOIN params p
),

-- PASO 8: TOTALES DE GIROS POR MES
totales_giros AS (
    SELECT
        mes,
        SUM(giro_obligatorio)                                              AS total_giros_mes
    FROM pui_mercado
    WHERE giro_obligatorio > 0
    GROUP BY mes
),

-- PASO 9: PUI DISTRIBUIDO POR AGENTE
pui_agente AS (
    SELECT
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
        va.agente_code,
        va.agente_name,
        va.vr_kwh                                                           AS vr_agente,
        va.dias_activos,
        va.promedio_diario_kwh,
        tm.vr_total_mes,
        tm.vr_total_cnior,
        CASE WHEN ca.cior_code IS NOT NULL THEN 'CIOR' ELSE 'CNIOR' END    AS rol_pui,
        ca.cior_code,
        ca.cior_vr_total,
        CASE
            WHEN tm.vr_total_mes > 0 AND pm.pui_mercado_total > 0
            THEN pm.pui_mercado_total * (va.vr_kwh / tm.vr_total_mes)
            ELSE 0.0
        END                                                                 AS pui_energia_kwh,
        CASE
            WHEN ca.cior_code IS NULL
                 AND pm.giro_obligatorio > 0
                 AND tm.vr_total_cnior > 0
            THEN pm.giro_obligatorio * (va.vr_kwh / tm.vr_total_cnior)
            ELSE 0.0
        END                                                                 AS egreso_giro,
        CASE
            WHEN ca.cior_code IS NULL
                 AND pm.recaudo_real_estimado > 0
                 AND tm.vr_total_cnior > 0
            THEN pm.recaudo_real_estimado * (va.vr_kwh / tm.vr_total_cnior)
            ELSE 0.0
        END                                                                 AS recaudo_agente
    FROM pui_mercado pm
    JOIN vr_agente va ON pm.mes = va.mes
    JOIN totales_mes tm ON pm.mes = tm.mes
    LEFT JOIN cior_agent ca ON va.agente_code = ca.cior_code
    WHERE va.vr_kwh > 0
),

-- PASO 10: FLUJO NETO Y SOBRECOSTO
flujo_agente AS (
    SELECT
        pa.*,
        tg.total_giros_mes,
        pa.pui_energia_kwh * pa.cu                                         AS pui_dinero_cop,
        CASE
            WHEN pa.rol_pui = 'CIOR'
            THEN pa.pui_energia_kwh + COALESCE(tg.total_giros_mes, 0)
            ELSE pa.pui_energia_kwh
        END                                                                 AS ingresos_pui_facturado,
        CASE
            WHEN pa.rol_pui = 'CIOR'
            THEN pa.pui_energia_kwh + COALESCE(tg.total_giros_mes, 0)
            ELSE pa.recaudo_agente - pa.egreso_giro
        END                                                                 AS flujo_neto_caja_pui,
        CASE
            WHEN pa.rol_pui = 'CNIOR' AND pa.egreso_giro > 0
            THEN pa.egreso_giro - pa.recaudo_agente
            ELSE 0.0
        END                                                                 AS sobrecosto_pui,
        CASE
            WHEN pa.rol_pui = 'CNIOR' AND pa.egreso_giro > 0
            THEN ((pa.egreso_giro - pa.recaudo_agente) / pa.egreso_giro) * 100
            ELSE 0.0
        END                                                                 AS pct_perdida_incobrabilidad,
        ROW_NUMBER() OVER (
            PARTITION BY pa.mes
            ORDER BY pa.vr_agente DESC
        )                                                                   AS ranking_agente_vr
    FROM pui_agente pa
    LEFT JOIN totales_giros tg ON pa.mes = tg.mes
)

-- RESULTADO FINAL
SELECT
    fa.agente_code                                                          AS agente_code,
    fa.agente_name                                                          AS agente_name,
    fa.rol_pui                                                              AS rol_pui,
    fa.mercado_code                                                         AS mercado_code,
    fa.mercado_name                                                         AS mercado_name,
    fa.mes                                                                  AS mes,
    ROUND(fa.vr_agente::numeric, 2)                                         AS vr_agente_kwh,
    fa.dias_activos                                                         AS dias_activos_mes,
    ROUND(fa.promedio_diario_kwh::numeric, 2)                              AS promedio_diario_kwh,
    ROUND(fa.cu::numeric, 4)                                                AS precio_prom_contratos_cop_kwh,
    ROUND(fa.vr_mercado_kwh::numeric, 2)                                   AS vr_mercado_kwh,
    ROUND(fa.vr_total_mes::numeric, 2)                                     AS vr_total_todos_agentes_kwh,
    ROUND(fa.vr_total_cnior::numeric, 2)                                   AS vr_total_cniors_kwh,
    CASE WHEN fa.vr_total_mes > 0
        THEN ROUND((fa.vr_agente / fa.vr_total_mes * 100)::numeric, 4)
        ELSE 0
    END                                                                     AS participacion_ettc_pct_total,
    CASE WHEN fa.vr_total_cnior > 0
        THEN ROUND((fa.vr_agente / fa.vr_total_cnior * 100)::numeric, 4)
        ELSE 0
    END                                                                     AS participacion_ettc_pct_cniors,
    fa.ranking_agente_vr                                                    AS ranking_vr_mes,
    ROUND(fa.vr_m1::numeric, 2)                                            AS vr_mercado_m1_kwh,
    ROUND(fa.vpui_m1::numeric, 2)                                          AS vpui_mercado_m1_kwh,
    ROUND(fa.cu_m1::numeric, 4)                                            AS cu_m1_cop_kwh,
    ROUND(fa.vr_m2::numeric, 2)                                            AS vr_mercado_m2_kwh,
    ROUND(fa.vpui_actual::numeric, 2)                                      AS vpui_actual_kwh,
    ROUND(fa.crpui_unitario::numeric, 8)                                   AS crpui_unitario,
    ROUND(fa.cfpui_unitario::numeric, 8)                                   AS cfpui_unitario,
    ROUND(fa.pui_mercado_total::numeric, 2)                                AS pui_mercado_total,
    ROUND(fa.giro_obligatorio::numeric, 2)                                 AS giro_obligatorio_mercado,
    ROUND(fa.recaudo_real_estimado::numeric, 2)                            AS recaudo_real_mercado,
    ROUND(fa.pui_energia_kwh::numeric, 2)                                  AS pui_energia_kwh,
    ROUND(fa.pui_dinero_cop::numeric, 2)                                   AS pui_dinero_cop,
    ROUND(fa.ingresos_pui_facturado::numeric, 2)                           AS ingresos_pui_facturado,
    ROUND(fa.egreso_giro::numeric, 2)                                      AS egreso_giro_cior,
    ROUND(fa.recaudo_agente::numeric, 2)                                   AS recaudo_real_agente,
    ROUND(fa.flujo_neto_caja_pui::numeric, 2)                              AS flujo_neto_caja_pui,
    ROUND(fa.sobrecosto_pui::numeric, 2)                                   AS sobrecosto_pui,
    ROUND(fa.pct_perdida_incobrabilidad::numeric, 2)                       AS pct_perdida_incobrabilidad,
    fa.cior_code                                                            AS cior_code,
    cior_info.cior_name                                                     AS cior_name,
    ROUND(fa.cior_vr_total::numeric, 2)                                    AS cior_vr_total_historial,
    ROUND(COALESCE(fa.total_giros_mes, 0)::numeric, 2)                     AS total_giros_recibidos_cior,
    p.rcpui                                                                 AS param_rcpui,
    p.pct_areas_especiales                                                  AS param_pct_areas_especiales,
    p.factor_recaudo_cnior                                                  AS param_factor_recaudo,
    p.cfpui                                                                 AS param_cfpui,
    p.esquema_competitivo                                                   AS param_esquema_competitivo
FROM flujo_agente fa
CROSS JOIN params p
CROSS JOIN cior_agent cior_info
WHERE fa.agente_code = p.agente_objetivo
ORDER BY fa.mes DESC, fa.mercado_code;
