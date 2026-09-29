-- Conteos que cuadran: filas de bronce, filas de plata y duplicados descartados (digital_events omitida: es vista de 15,6 M)
{% set tablas = ['customers','products','transactions','call_center_interactions','complaints','satisfaction_surveys','service_agents','daily_exchange_rates','call_transcripts','branches','marketing_campaigns','campaign_sends'] %}
{% for t in tablas %}
select '{{ t }}' as tabla,
  (select count(*) from {{ source('bronce', 'bronce_' ~ t) }}) as filas_bronce,
  (select count(*) from {{ ref('plata_' ~ t) }}) as filas_plata,
  (select count(*) from {{ source('bronce', 'bronce_' ~ t) }}) - (select count(*) from {{ ref('plata_' ~ t) }}) as duplicados_descartados
{{ 'union all' if not loop.last }}
{% endfor %}
