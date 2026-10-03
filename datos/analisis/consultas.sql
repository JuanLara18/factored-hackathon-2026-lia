-- Consultas del análisis del problema (criterio 1). Cada bloque empieza con `-- @nombre` y termina en `;`.
-- `{ds}` se reemplaza por proyecto.dataset. Todas leen plata (tipos canónicos, sin duplicados).
-- Ejecutar: uv run python -m latam_datos.analisis

-- @cobertura
-- Filas y ventana de fechas de las tablas plata que usa el análisis.
SELECT 'call_center_interactions' AS tabla, COUNT(*) AS filas, MIN(DATE(interaction_date)) AS desde, MAX(DATE(interaction_date)) AS hasta, COUNT(DISTINCT customer_id) AS clientes FROM `{ds}.plata_call_center_interactions`
UNION ALL SELECT 'complaints', COUNT(*), MIN(DATE(creation_date)), MAX(DATE(creation_date)), COUNT(DISTINCT customer_id) FROM `{ds}.plata_complaints`
UNION ALL SELECT 'satisfaction_surveys', COUNT(*), MIN(DATE(survey_date)), MAX(DATE(survey_date)), COUNT(DISTINCT customer_id) FROM `{ds}.plata_satisfaction_surveys`
UNION ALL SELECT 'transactions', COUNT(*), MIN(DATE(transaction_date)), MAX(DATE(transaction_date)), COUNT(DISTINCT customer_id) FROM `{ds}.plata_transactions`
UNION ALL SELECT 'service_agents', COUNT(*), MIN(hire_date), MAX(hire_date), NULL FROM `{ds}.plata_service_agents`;

-- @motivo_canal
-- Contactos por motivo y canal. plata_call_center_interactions, sin filtro.
SELECT reason_category AS motivo, channel AS canal, COUNT(*) AS n
FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2;

-- @motivo_pais
-- Contactos por motivo y país del cliente. plata_call_center_interactions con plata_customers.
SELECT i.reason_category AS motivo, c.country AS pais, COUNT(*) AS n
FROM `{ds}.plata_call_center_interactions` i JOIN `{ds}.plata_customers` c USING (customer_id) GROUP BY 1, 2;

-- @motivo_mes
-- Tendencia mensual por motivo. plata_call_center_interactions, mes de interaction_date.
SELECT DATE_TRUNC(DATE(interaction_date), MONTH) AS mes, reason_category AS motivo, COUNT(*) AS n
FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2;

-- @hora_dia
-- Estacionalidad: día de la semana (1 domingo a 7 sábado) y hora de interaction_date, por motivo.
SELECT EXTRACT(DAYOFWEEK FROM interaction_date) AS dia, EXTRACT(HOUR FROM interaction_date) AS hora, reason_category AS motivo, COUNT(*) AS n
FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2, 3;

-- @recurrencia
-- Contactos repetidos: otro contacto del mismo cliente en los 7 días previos (cualquier motivo, o el mismo motivo).
WITH t AS (
  SELECT reason_category AS motivo, interaction_date,
    LAG(interaction_date) OVER (PARTITION BY customer_id ORDER BY interaction_date) AS previo_cualquiera,
    LAG(interaction_date) OVER (PARTITION BY customer_id, reason_category ORDER BY interaction_date) AS previo_mismo
  FROM `{ds}.plata_call_center_interactions`)
SELECT motivo, COUNT(*) AS n,
  COUNTIF(DATETIME_DIFF(interaction_date, previo_cualquiera, DAY) < 7) AS repite_7d_cualquiera,
  COUNTIF(DATETIME_DIFF(interaction_date, previo_mismo, DAY) < 7) AS repite_7d_mismo,
  COUNTIF(DATETIME_DIFF(interaction_date, previo_mismo, DAY) < 30) AS repite_30d_mismo
FROM t GROUP BY 1;

-- @agentes
-- Capacidad humana: plata_service_agents por turno, tipo, estado, idioma y especialidad.
SELECT work_shift AS turno, agent_type AS tipo, agent_status AS estado, specialty AS especialidad,
  languages LIKE '%portugu%' AS portugues, COUNT(*) AS agentes, AVG(avg_csat) AS csat_prom, SUM(total_monthly_interactions) AS interacciones_mes
FROM `{ds}.plata_service_agents` GROUP BY 1, 2, 3, 4, 5;

-- @carga_turno
-- Interacciones por turno del agente asignado y por hora de la interacción.
SELECT a.work_shift AS turno, EXTRACT(HOUR FROM i.interaction_date) AS hora, COUNT(*) AS n
FROM `{ds}.plata_call_center_interactions` i JOIN `{ds}.plata_service_agents` a USING (agent_id) GROUP BY 1, 2;

-- @tiempos_resultados
-- Duración, espera y resultado por motivo, canal y tipo. Duración y espera solo sobre valores no vacíos.
SELECT reason_category AS motivo, channel AS canal, interaction_type AS tipo, COUNT(*) AS n,
  COUNTIF(was_resolved) AS resueltos, COUNTIF(was_escalated) AS escalados, COUNTIF(requires_followup) AS seguimiento,
  COUNT(duration_seconds) AS n_dur, SUM(duration_seconds) AS sum_dur,
  APPROX_QUANTILES(duration_seconds, 100)[OFFSET(50)] AS dur_p50, APPROX_QUANTILES(duration_seconds, 100)[OFFSET(90)] AS dur_p90,
  COUNT(wait_time_seconds) AS n_esp, SUM(wait_time_seconds) AS sum_esp,
  APPROX_QUANTILES(wait_time_seconds, 100)[OFFSET(50)] AS esp_p50, APPROX_QUANTILES(wait_time_seconds, 100)[OFFSET(90)] AS esp_p90,
  COUNTIF(detected_sentiment = 'Negativo') AS sent_negativo, COUNT(detected_sentiment) AS n_sent
FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2, 3;

-- @encuestas
-- Satisfacción por motivo y canal de la interacción. plata_satisfaction_surveys con plata_call_center_interactions por interaction_id.
SELECT s.survey_type AS tipo, i.reason_category AS motivo, i.channel AS canal, COUNT(*) AS n, SUM(s.main_score) AS sum_score,
  COUNTIF(s.main_score >= 3) AS altos, COUNTIF(s.nps_category = 'Detractor') AS detractores
FROM `{ds}.plata_satisfaction_surveys` s JOIN `{ds}.plata_call_center_interactions` i USING (interaction_id) GROUP BY 1, 2, 3;

-- @quejas_linea_base
-- Línea base de quejas por subcategoría (nulo agrupado). plata_complaints, sin filtro. Horas desde creation_date.
SELECT COALESCE(subcategory, 'Sin subcategoría') AS subcategoria, COUNT(*) AS n,
  APPROX_QUANTILES(DATETIME_DIFF(assignment_date, creation_date, HOUR), 100)[OFFSET(50)] AS h_asig_p50,
  APPROX_QUANTILES(DATETIME_DIFF(first_response_date, creation_date, HOUR), 100)[OFFSET(50)] AS h_resp_p50,
  APPROX_QUANTILES(DATETIME_DIFF(first_response_date, creation_date, HOUR), 100)[OFFSET(90)] AS h_resp_p90,
  COUNT(first_response_date) AS n_resp, COUNT(resolution_days) AS n_res,
  APPROX_QUANTILES(resolution_days, 100)[OFFSET(50)] AS dias_res_p50, APPROX_QUANTILES(resolution_days, 100)[OFFSET(90)] AS dias_res_p90,
  AVG(resolution_days) AS dias_res_prom,
  COUNTIF(sla_breached) AS sla_incumplido, COUNTIF(is_repeat_complainer) AS reincidentes, COUNTIF(priority = 'Critical') AS criticas,
  COUNTIF(status IN ('Resolved', 'Closed')) AS cerradas, COUNTIF(status = 'Escalated') AS escaladas, COUNTIF(status IN ('Open', 'In Process')) AS abiertas,
  COUNT(resolution_satisfaction) AS n_csat, SUM(resolution_satisfaction) AS sum_csat
FROM `{ds}.plata_complaints` GROUP BY 1;

-- @quejas_mes_pais_canal
-- Quejas por mes, país del cliente, canal de recepción y si son cargo no reconocido.
SELECT DATE_TRUNC(DATE(q.creation_date), MONTH) AS mes, c.country AS pais, q.reception_channel AS canal,
  q.subcategory = 'Cargo no reconocido' AS es_disputa, COUNT(*) AS n
FROM `{ds}.plata_complaints` q JOIN `{ds}.plata_customers` c USING (customer_id) GROUP BY 1, 2, 3, 4;

-- @fraude
-- Fraude por mes, país de la transacción, canal y estado. plata_transactions, amount_usd con la regla de plata.
SELECT DATE_TRUNC(DATE(transaction_date), MONTH) AS mes, transaction_country AS pais, channel AS canal, transaction_status AS estado,
  COUNT(*) AS n, COUNTIF(is_fraud) AS fraudes, SUM(IF(is_fraud, amount_usd, 0)) AS usd_fraude, SUM(amount_usd) AS usd_total,
  COUNTIF(is_fraud AND fraud_score IS NULL) AS fraude_sin_score
FROM `{ds}.plata_transactions` GROUP BY 1, 2, 3, 4;

-- @montos_disputa
-- Monto reclamado en cargos no reconocidos, por moneda (sin conversión). plata_complaints, subcategory = 'Cargo no reconocido'.
SELECT COALESCE(currency, 'sin moneda') AS moneda, COUNT(*) AS n, COUNT(claimed_amount) AS con_monto,
  APPROX_QUANTILES(claimed_amount, 100)[OFFSET(50)] AS monto_p50, APPROX_QUANTILES(claimed_amount, 100)[OFFSET(90)] AS monto_p90,
  COUNTIF(compensation_granted > 0) AS con_compensacion
FROM `{ds}.plata_complaints` WHERE subcategory = 'Cargo no reconocido' GROUP BY 1;

-- @calidad
-- Calidad: vacíos y procedencia en las tablas plata que consume el flujo.
SELECT 'transactions.amount_usd_origen' AS control, amount_usd_origen AS valor, COUNT(*) AS n FROM `{ds}.plata_transactions` GROUP BY 1, 2
UNION ALL SELECT 'interactions.duracion_vacia', CAST(duration_seconds IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2
UNION ALL SELECT 'interactions.espera_vacia_llamada_entrante', CAST(wait_time_seconds IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_call_center_interactions` WHERE interaction_type = 'Inbound Call' GROUP BY 1, 2
UNION ALL SELECT 'interactions.espera_vacia_otros', CAST(wait_time_seconds IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_call_center_interactions` WHERE interaction_type != 'Inbound Call' GROUP BY 1, 2
UNION ALL SELECT 'interactions.motivo_distinto_categoria', CAST(contact_reason != reason_category AS STRING), COUNT(*) FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2
UNION ALL SELECT 'interactions.con_transcripcion', CAST(has_transcript AS STRING), COUNT(*) FROM `{ds}.plata_call_center_interactions` GROUP BY 1, 2
UNION ALL SELECT 'complaints.subcategoria_vacia', CAST(subcategory IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` GROUP BY 1, 2
UNION ALL SELECT 'complaints.producto_afectado_vacio', CAST(affected_product_id IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` GROUP BY 1, 2
UNION ALL SELECT 'complaints.interaccion_origen_vacia', CAST(origin_interaction_id IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` GROUP BY 1, 2
UNION ALL SELECT 'complaints.disputa_monto_vacio', CAST(claimed_amount IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` WHERE subcategory = 'Cargo no reconocido' GROUP BY 1, 2
UNION ALL SELECT 'complaints.sin_primera_respuesta', CAST(first_response_date IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` GROUP BY 1, 2
UNION ALL SELECT 'complaints.sin_resolucion', CAST(resolution_date IS NULL AS STRING), COUNT(*) FROM `{ds}.plata_complaints` GROUP BY 1, 2
UNION ALL SELECT 'surveys.escala_main_score', survey_type || ' ' || CAST(MIN(main_score) AS STRING) || '-' || CAST(MAX(main_score) AS STRING), COUNT(*) FROM `{ds}.plata_satisfaction_surveys` GROUP BY survey_type
UNION ALL SELECT 'agents.idiomas', languages, COUNT(*) FROM `{ds}.plata_service_agents` GROUP BY 1, 2
UNION ALL SELECT 'agents.estado', agent_status, COUNT(*) FROM `{ds}.plata_service_agents` GROUP BY 1, 2;

-- @digital
-- Eventos digitales (vista sobre bronce, un escaneo): volumen por categoría y acción, con la fracción sin cliente.
SELECT event_category AS categoria, action AS accion, COUNT(*) AS n, COUNTIF(customer_id IS NULL) AS sin_cliente,
  COUNTIF(session_id IS NULL) AS sin_sesion
FROM `{ds}.plata_digital_events` GROUP BY 1, 2;

-- @transcripciones
-- Idioma e intención detectados en las transcripciones. plata_call_transcripts, sin filtro.
SELECT detected_language AS idioma, COALESCE(detected_intents, 'sin intención') AS intencion, COUNT(*) AS n
FROM `{ds}.plata_call_transcripts` GROUP BY 1, 2;
