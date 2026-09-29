-- Conteo completo de llaves huérfanas (los tests relationships guardan filas, esto guarda el total)
{% set rels = [
  ('products', 'customer_id', 'customers', 'customer_id'),
  ('transactions', 'product_id', 'products', 'product_id'),
  ('transactions', 'customer_id', 'customers', 'customer_id'),
  ('complaints', 'customer_id', 'customers', 'customer_id'),
  ('complaints', 'affected_product_id', 'products', 'product_id'),
  ('call_center_interactions', 'customer_id', 'customers', 'customer_id'),
  ('satisfaction_surveys', 'interaction_id', 'call_center_interactions', 'interaction_id')
] %}
{% for h, hc, p, pc in rels %}
select 'plata_{{ h }}.{{ hc }} -> plata_{{ p }}.{{ pc }}' as relacion,
       count(*) as filas_con_llave, countif(p.`{{ pc }}` is null) as huerfanas
from {{ ref('plata_' ~ h) }} as h
left join (select distinct `{{ pc }}` from {{ ref('plata_' ~ p) }}) as p on p.`{{ pc }}` = h.`{{ hc }}`
where h.`{{ hc }}` is not null
{{ 'union all' if not loop.last }}
{% endfor %}
union all
select 'plata_transactions.owner: producto de otro cliente', count(*), countif(not _owner_ok and _fk_ok)
from {{ ref('plata_transactions') }}
