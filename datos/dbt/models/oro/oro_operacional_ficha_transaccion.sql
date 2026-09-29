-- Ficha de la transacción: transacciones_recientes más directorio, historia previa del cliente con el comercio,
-- tasa del día y explicación del estado. Todo se calcula con datos anteriores al evento (ventanas que terminan
-- un segundo antes). Sin PII, is_fraud ni fraud_score.
with hist as (
  select
    transaction_id,
    countif(transaction_type = 'Purchase' and transaction_status = 'Approved') over w12 as compras_previas_mismo_comercio_12m,
    max(if(transaction_type = 'Purchase' and transaction_status = 'Approved', transaction_date, null)) over w12 as ultima_compra_previa,
    count(*) over w48 as posibles_duplicados_48h
  from {{ ref('plata_transactions') }}
  where _fk_ok and _owner_ok and merchant_name is not null
  window
    w12 as (partition by customer_id, merchant_name order by unix_seconds(timestamp(transaction_date))
            range between 31536000 preceding and 1 preceding),
    w48 as (partition by customer_id, merchant_name, amount order by unix_seconds(timestamp(transaction_date))
            range between 172800 preceding and 1 preceding)
),
tasa as (
  select `date` as fecha, source_currency as moneda, exchange_rate
  from {{ ref('plata_daily_exchange_rates') }} where target_currency = 'USD'
),
maxf as (select max(fecha) as f from tasa)
select
  r.*,
  {{ merchant_key('r.merchant_name') }} as merchant_key,
  d.razon_social, d.descriptor_extracto, d.marca,
  if(d.merchant_name is not null, 'equipo', null) as origen_directorio,
  coalesce(h.compras_previas_mismo_comercio_12m, 0) as compras_previas_mismo_comercio_12m,
  h.ultima_compra_previa,
  coalesce(h.posibles_duplicados_48h, 0) as posibles_duplicados_48h,
  if(r.currency = 'USD', 1.0, tasa.exchange_rate) as tasa_usd,
  if(r.currency = 'USD', r.event_date, if(tasa.exchange_rate is not null, tasa.fecha, null)) as fecha_tasa,
  case r.transaction_status
    when 'Pending' then 'Pendiente: aún no se liquida y puede cambiar de estado'
    when 'Reversed' then 'Revertida: el movimiento se devolvió a la cuenta'
    when 'Declined' then concat('Rechazada', if(t.response_code is not null, concat(' (código ', t.response_code, ')'), ''))
  end as explicacion_estado_clave
from {{ ref('oro_operacional_transacciones_recientes') }} as r
join {{ ref('plata_transactions') }} as t on t.transaction_id = r.transaction_id
left join hist as h on h.transaction_id = r.transaction_id
left join {{ ref('oro_operacional_directorio_comercios') }} as d on d.merchant_name = r.merchant_name
cross join maxf
left join tasa on tasa.fecha = least(r.event_date, maxf.f) and tasa.moneda = r.currency
