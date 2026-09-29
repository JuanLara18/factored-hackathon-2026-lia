-- Lo que lee la herramienta de cuentas y transacciones: ventana de `ventana_dias` antes de AS_OF, sin PII,
-- sin is_fraud ni fraud_score (R-DAT-39) y solo transacciones con producto existente y del mismo cliente.
select
  t.transaction_id, t.customer_id, t.product_id, p.product_type,
  t.transaction_date as event_ts, t.event_date,
  t.amount, t.currency, t.amount_usd, t.amount_usd_origen,
  t.transaction_type, t.transaction_status, t.channel,
  t.merchant_name, t.merchant_category, t.transaction_country,
  (t.transaction_country is not null and c.country is not null and t.transaction_country != c.country) as es_extranjera,
  t._moneda_anomala,
  date('{{ var("as_of") }}') as fecha_corte
from {{ ref('plata_transactions') }} as t
join {{ ref('plata_products') }} as p on p.product_id = t.product_id
left join {{ ref('plata_customers') }} as c on c.customer_id = t.customer_id
where t._fk_ok and t._owner_ok
  and t.transaction_date >= datetime_sub(datetime('{{ var("as_of") }}'), interval {{ var('ventana_dias') }} day)
  and t.transaction_date < datetime('{{ var("as_of") }}')
