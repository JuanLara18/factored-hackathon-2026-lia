{# dbt run-operation crear_llave: crea una sola vez la llave aleatoria (32 bytes: SHA-256 de cuatro UUID v4, BigQuery no tiene RANDOM_BYTES) de seudonimización (nunca en el repo).
   Idempotente: si ya existe no la reemplaza, porque rotarla rompería las uniones entre tablas. #}
{% macro crear_llave() %}
    {% set ds = target.project ~ '.latam_seguridad' %}
    {% do run_query('create schema if not exists `' ~ ds ~ '` options(location="' ~ target.location ~ '")') %}
    {% do run_query('create table if not exists `' ~ ds ~ '.llave` as select sha256(concat(generate_uuid(), generate_uuid(), generate_uuid(), generate_uuid())) as secret, current_timestamp() as creada_en') %}
    {{ log('llave lista en ' ~ ds ~ '.llave', info=True) }}
{% endmacro %}
