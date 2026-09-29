-- Puntaje de fraude por transacción de la ventana, solo para el servicio de diagnóstico de la política (R-DAT-39).
-- Sin is_fraud. Bandas: alto sobre `riesgo_alto_sobre`; zona gris (revisión humana) desde `riesgo_zona_gris_desde`.
select
  r.transaction_id, r.customer_id, t.fraud_score,
  case
    when t.fraud_score is null then null
    when t.fraud_score > {{ var("riesgo_alto_sobre") }} then 'alto'
    when t.fraud_score >= {{ var("riesgo_zona_gris_desde") }} then 'zona_gris'
    else 'bajo'
  end as banda_riesgo,
  r.fecha_corte
from {{ ref('oro_operacional_transacciones_recientes') }} as r
join {{ ref('plata_transactions') }} as t on t.transaction_id = r.transaction_id
