{# Llave estable del comercio: 10 primeros hex del MD5 del nombre en minúsculas. #}
{% macro merchant_key(col) %}substr(to_hex(md5(lower({{ col }}))), 1, 10){% endmacro %}
