-- _moneda_anomala: cliente de México con producto en USD (la fuente no trae MXN; no se convierte nada)
with p as ({{ plata_base('products') }})
select p.*, (c.country = 'MX' and p.currency = 'USD') as _moneda_anomala, c.customer_id is not null as _fk_ok
from p left join {{ ref('plata_customers') }} as c using (customer_id)
