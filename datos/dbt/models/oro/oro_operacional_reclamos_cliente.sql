-- Quejas del cliente para el servicio de casos. Sin affected_product_id ni claimed_amount y sin
-- agente asignado, compensación ni texto libre. Solo quejas anteriores a AS_OF.
select
  complaint_id, customer_id, case_type, category, subcategory, status, priority,
  reception_channel, creation_date as fecha_radicacion, first_response_date as fecha_primera_respuesta,
  resolution_date as fecha_resolucion, sla_breached,
  date('{{ var("as_of") }}') as fecha_corte
from {{ ref('plata_complaints') }}
where creation_date < datetime('{{ var("as_of") }}')
