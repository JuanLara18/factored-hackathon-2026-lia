-- Línea base de reclamos por país del cliente, canal de recepción y mes de radicación (fecha del evento).
-- Advertencia: la fuente es sintética; los tiempos sirven de referencia, no de meta.
select
  c.country as pais,
  q.reception_channel as canal,
  date_trunc(date(q.creation_date), month) as mes,
  count(*) as reclamos,
  countif(q.subcategory = 'Cargo no reconocido') as cargo_no_reconocido,
  countif(q.sla_breached) as sla_incumplido,
  safe_divide(countif(q.sla_breached), count(*)) as fraccion_sla_incumplido,
  avg(q.resolution_days) as dias_resolucion_promedio,
  approx_quantiles(q.resolution_days, 100)[offset(50)] as dias_resolucion_mediana,
  countif(q.is_repeat_complainer) as reincidentes
from {{ ref('plata_complaints') }} as q
left join {{ ref('plata_customers') }} as c using (customer_id)
group by pais, canal, mes
