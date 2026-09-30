-- Saldo y cupo de cada producto para la banca en línea (el cliente ve lo suyo). Separado de
-- oro_operacional_estado_productos a propósito: las herramientas del agente no leen saldos (minimización).
select
  p.product_id, p.customer_id, p.currency,
  p.current_balance as saldo, p.credit_limit as limite,
  date('{{ var("as_of") }}') as fecha_corte
from {{ ref('plata_products') }} as p
where p._fk_ok
