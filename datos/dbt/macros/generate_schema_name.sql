{# Todas las capas viven en un solo dataset; la capa es el prefijo del nombre de la tabla.
   Los fallos guardados de las pruebas y las tablas temporales de las pruebas unitarias van a
   latam_pruebas, para que latam_bank solo muestre capas. #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if node.resource_type in ['test', 'unit_test'] -%}
        latam_pruebas
    {%- else -%}
        {{ target.schema }}
    {%- endif -%}
{%- endmacro %}
