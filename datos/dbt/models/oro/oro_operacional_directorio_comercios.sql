-- Directorio de comercios: los del dataset (nombre y categoría más frecuente) más razón social, descriptor y marca
-- inventados por el equipo (seed directorio_comercios_equipo). Versión y semilla en cada fila (R-DAT-40).
with cat as (
  select merchant_name, merchant_category,
    row_number() over (partition by merchant_name order by count(*) desc, merchant_category) as rn
  from {{ ref('plata_transactions') }}
  where merchant_name is not null and merchant_category is not null
  group by merchant_name, merchant_category
),
nombres as (
  select distinct merchant_name from {{ ref('plata_transactions') }} where merchant_name is not null
)
select
  {{ merchant_key('n.merchant_name') }} as merchant_key,
  n.merchant_name,
  e.razon_social, e.descriptor_extracto, e.marca,
  c.merchant_category,
  'equipo' as origen,
  '{{ var("directorio_version") }}' as version,
  {{ var("directorio_semilla") }} as semilla
from nombres as n
left join cat as c on c.merchant_name = n.merchant_name and c.rn = 1
left join {{ ref('directorio_comercios_equipo') }} as e on e.merchant_name = n.merchant_name
