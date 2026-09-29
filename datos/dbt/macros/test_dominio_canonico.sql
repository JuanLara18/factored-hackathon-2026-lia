{# Prueba genérica: los valores no vacíos de la columna existen en el dominio canónico (seed dominios_canonicos). #}
{% test dominio_canonico(model, column_name, dominio) %}
select {{ column_name }} as valor_fuera_de_dominio, count(*) as filas
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} not in (select valor from {{ ref('dominios_canonicos') }} where dominio = '{{ dominio }}')
group by 1
{% endtest %}
