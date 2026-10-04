-- Consultas de la línea base de equidad (criterio de equidad del enunciado). Mismo formato que consultas.sql.
-- Salen SOLO agregados: cada celda con menos de 20 casos (k-anonimato) se descarta dentro de BigQuery y nunca
-- sale fila por cliente. Los atributos de plata_restringida_clientes (género, banda de edad) solo se usan aquí,
-- agregados, para auditar; estado civil y educación no se usan (minimización, R-GOB-46).
-- Ejecutar: uv run python -m latam_datos.analisis.equidad

-- @equidad_quejas
-- Quejas: respuesta, SLA, resolución, escalamiento y CSAT de resolución (1 a 5) por segmento autorizado y ámbito.
-- Ámbitos: 'todas' (toda plata_complaints) y 'disputa' (subcategoría 'Cargo no reconocido'). Para cada fila se calcula
-- la tasa esperada por mezcla (canal, tipo de caso, categoría, moneda y tercil del monto reclamado) dentro del ámbito.
WITH b AS (
  SELECT c.complaint_id, c.reception_channel AS canal, c.case_type, c.category, c.subcategory, c.currency,
    cu.country AS pais, cu.segment AS segmento, COALESCE(cu.detected_accent, 'sin_acento') AS acento,
    IF(r.banda_edad = '65+', '65+', '<65') AS franja_edad, r.banda_edad, r.gender AS genero,
    IF(c.claimed_amount IS NULL, 0, NTILE(3) OVER (PARTITION BY c.currency, c.claimed_amount IS NULL ORDER BY c.claimed_amount)) AS terc_monto,
    CAST(c.first_response_date IS NOT NULL AS INT64) AS resp,
    DATETIME_DIFF(c.first_response_date, c.creation_date, HOUR) AS h_resp,
    CAST(COALESCE(c.sla_breached, FALSE) AS INT64) AS sla,
    CAST(c.resolution_date IS NOT NULL AS INT64) AS res,
    CAST(c.status = 'Escalated' AS INT64) AS esc,
    c.resolution_satisfaction AS csat
  FROM `{ds}.plata_complaints` c
  JOIN `{ds}.plata_customers` cu USING (customer_id)
  JOIN `{ds}.plata_restringida_clientes` r USING (customer_id)),
e AS (
  SELECT b.*, ambito FROM b, UNNEST(IF(subcategory = 'Cargo no reconocido', ['todas', 'disputa'], ['todas'])) AS ambito),
s AS (
  SELECT e.*,
    AVG(resp) OVER w AS e_resp, AVG(sla) OVER w AS e_sla, AVG(res) OVER w AS e_res, AVG(esc) OVER w AS e_esc
  FROM e WINDOW w AS (PARTITION BY ambito, canal, case_type, category, currency, terc_monto))
SELECT ambito, dim.d AS dimension, dim.g AS grupo, COUNT(*) AS n,
  SUM(resp) AS resp, SUM(sla) AS sla, SUM(res) AS res, SUM(esc) AS esc,
  SUM(e_resp) AS e_resp, SUM(e_sla) AS e_sla, SUM(e_res) AS e_res, SUM(e_esc) AS e_esc,
  COUNT(h_resp) AS n_h, AVG(h_resp) AS h_prom, APPROX_QUANTILES(h_resp, 100)[OFFSET(50)] AS h_p50,
  IF(COUNT(csat) >= 20, COUNT(csat), NULL) AS n_csat, IF(COUNT(csat) >= 20, SUM(csat), NULL) AS s_csat,
  IF(COUNT(csat) >= 20, SUM(csat * csat), NULL) AS ss_csat
FROM s, UNNEST([
  STRUCT('pais' AS d, pais AS g), STRUCT('segmento', segmento), STRUCT('canal', canal),
  STRUCT('acento', acento), STRUCT('franja_edad', franja_edad), STRUCT('banda_edad', banda_edad),
  STRUCT('genero', genero)]) AS dim
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 20;

-- @equidad_contactos
-- Contactos (plata_call_center_interactions): resolución, escalamiento, seguimiento, espera y CSAT de encuesta (main_score).
-- Ámbitos: 'todos' y 'transaccional' (reason_category = 'Transaccional', donde caen las disputas de cargo). Mezcla esperada
-- por canal, tipo de interacción, motivo y tercio del día.
WITH enc AS (
  SELECT interaction_id, AVG(main_score) AS csat FROM `{ds}.plata_satisfaction_surveys` GROUP BY 1),
b AS (
  SELECT i.interaction_id, i.channel AS canal, i.interaction_type AS tipo, i.contact_reason AS motivo,
    CASE WHEN EXTRACT(HOUR FROM i.interaction_date) < 8 THEN 'noche' WHEN EXTRACT(HOUR FROM i.interaction_date) < 16 THEN 'manana' ELSE 'tarde' END AS tercio,
    cu.country AS pais, cu.segment AS segmento, COALESCE(i.customer_detected_accent, 'sin_acento') AS acento,
    IF(r.banda_edad = '65+', '65+', '<65') AS franja_edad, r.banda_edad, r.gender AS genero,
    CAST(i.was_resolved AS INT64) AS res, CAST(i.was_escalated AS INT64) AS esc, CAST(i.requires_followup AS INT64) AS seg,
    i.wait_time_seconds AS espera, enc.csat, i.reason_category
  FROM `{ds}.plata_call_center_interactions` i
  JOIN `{ds}.plata_customers` cu USING (customer_id)
  JOIN `{ds}.plata_restringida_clientes` r USING (customer_id)
  LEFT JOIN enc USING (interaction_id)),
e AS (
  SELECT b.*, ambito FROM b, UNNEST(IF(reason_category = 'Transaccional', ['todos', 'transaccional'], ['todos'])) AS ambito),
s AS (
  SELECT e.*, AVG(res) OVER w AS e_res, AVG(esc) OVER w AS e_esc, AVG(seg) OVER w AS e_seg
  FROM e WINDOW w AS (PARTITION BY ambito, canal, tipo, motivo, tercio))
SELECT ambito, dim.d AS dimension, dim.g AS grupo, COUNT(*) AS n,
  SUM(res) AS res, SUM(esc) AS esc, SUM(seg) AS seg,
  SUM(e_res) AS e_res, SUM(e_esc) AS e_esc, SUM(e_seg) AS e_seg,
  COUNT(espera) AS n_espera, AVG(espera) AS espera_prom, APPROX_QUANTILES(espera, 100)[OFFSET(50)] AS espera_p50,
  IF(COUNT(csat) >= 20, COUNT(csat), NULL) AS n_csat, IF(COUNT(csat) >= 20, SUM(csat), NULL) AS s_csat,
  IF(COUNT(csat) >= 20, SUM(csat * csat), NULL) AS ss_csat
FROM s, UNNEST([
  STRUCT('pais' AS d, pais AS g), STRUCT('segmento', segmento), STRUCT('canal', canal),
  STRUCT('acento', acento), STRUCT('franja_edad', franja_edad), STRUCT('banda_edad', banda_edad),
  STRUCT('genero', genero)]) AS dim
GROUP BY 1, 2, 3
HAVING COUNT(*) >= 20;
