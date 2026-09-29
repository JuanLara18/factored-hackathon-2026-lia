-- Una fila por cliente sin segmento, acento ni contacto: país y estado para elegir la norma aplicable
select customer_id, country, customer_status, date('{{ var("as_of") }}') as fecha_corte
from {{ ref('plata_customers') }}
