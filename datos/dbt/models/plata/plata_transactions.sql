-- amount_usd: si la fuente lo trae vacío se recalcula (monto en USD, o monto por la tasa del día de la transacción)
-- y `amount_usd_origen` lo marca: fuente | igual_monto | recalculado_tasa | sin_tasa
with t as ({{ plata_base('transactions') }}),
tasa as (
  select `date` as fecha, source_currency as moneda, exchange_rate
  from {{ ref('plata_daily_exchange_rates') }} where target_currency = 'USD'
)
select
  t.* except (amount_usd_fuente),
  date(t.transaction_date) as event_date,
  coalesce(
    t.amount_usd_fuente,
    if(t.currency = 'USD', t.amount, round(t.amount * tasa.exchange_rate, 2))
  ) as amount_usd,
  case
    when t.amount_usd_fuente is not null then 'fuente'
    when t.currency = 'USD' and t.amount is not null then 'igual_monto'
    when tasa.exchange_rate is not null and t.amount is not null then 'recalculado_tasa'
    else 'sin_tasa'
  end as amount_usd_origen,
  p.product_id is not null as _fk_ok,
  coalesce(p.customer_id = t.customer_id, false) as _owner_ok,
  coalesce(p._moneda_anomala, false) as _moneda_anomala
from t
-- después de la última tasa publicada se usa la última (least): el reloj AS_OF llega un día más allá de la serie
cross join (select max(fecha) as f from tasa) as maxf
left join tasa on tasa.fecha = least(date(t.transaction_date), maxf.f) and tasa.moneda = t.currency
left join {{ ref('plata_products') }} as p on p.product_id = t.product_id
