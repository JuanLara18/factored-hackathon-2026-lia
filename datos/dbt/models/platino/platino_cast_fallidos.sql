-- Valores no vacíos de bronce que no se pudieron convertir al tipo canónico, por tabla y columna.
-- Un fallo pasa a NULL en plata; aquí queda contado, sin perder la señal.
{% set tablas = esquema() %}
{% for tabla, s in tablas.items() %}
select
  '{{ tabla }}' as tabla, c.columna, c.tipo, n.filas, c.no_vacios, c.fallidos,
  safe_divide(c.fallidos, c.no_vacios) as fraccion_fallida
from (
  select
    count(*) as filas,
    [
    {%- set cols = s['cols'] | rejectattr(1, 'in', ['str', 'tokdoc', 'tokmail', 'tokfono']) | list %}
    {%- for col in cols %}
      struct('{{ col[0] }}' as columna, '{{ col[1] }}' as tipo,
             countif({{ vacio(col[0]) }} is not null) as no_vacios,
             countif({{ fallo(col[0], col[1]) }}) as fallidos){{ ',' if not loop.last }}
    {%- endfor %}
    ] as r
  from {{ source('bronce', 'bronce_' ~ tabla) }}
) as n, unnest(n.r) as c
{{ 'union all' if not loop.last }}
{% endfor %}
