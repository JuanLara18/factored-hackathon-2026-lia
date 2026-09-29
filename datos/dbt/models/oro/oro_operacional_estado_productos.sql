-- Estado de cada producto para el servicio de tarjetas (leer antes de bloquear). Sin número de producto ni saldo.
select
  p.product_id, p.customer_id, p.product_type, p.product_status, p.currency,
  p._moneda_anomala, date('{{ var("as_of") }}') as fecha_corte
from {{ ref('plata_products') }} as p
where p._fk_ok
