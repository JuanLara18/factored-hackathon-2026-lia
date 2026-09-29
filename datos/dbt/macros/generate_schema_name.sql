{# Todas las capas viven en un solo dataset; la capa es el prefijo del nombre de la tabla #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ target.schema }}
{%- endmacro %}
