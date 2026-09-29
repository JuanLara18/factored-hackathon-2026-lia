{# Especificación de plata por tabla: llave, columna de orden para elegir ganador y columnas [origen, tipo, alias?].
   Lo que no está listado no pasa a plata (PII directa, texto libre, IP, geolocalización).
   Tipos: str int dinero num flt fecha ts bool pais moneda tokdoc tokmail tokfono #}
{% macro esquema() %}
{% set e = {
 'customers': {'llave': ['customer_id'], 'orden': 'last_updated', 'cols': [
   ['customer_id','str'], ['document_type','str'],
   ['document_number','tokdoc','document_number_token'], ['email','tokmail','email_token'],
   ['mobile_phone','tokfono','mobile_phone_token'], ['landline_phone','tokfono','landline_phone_token'],
   ['city','str'], ['state','str'], ['country','pais'], ['detected_accent','str'], ['segment','str'],
   ['credit_score','int'], ['estimated_monthly_income','dinero'], ['occupation','str'],
   ['registration_date','ts'], ['registration_branch_id','str'], ['customer_status','str'],
   ['last_updated','ts'], ['accepts_marketing','bool']]},
 'products': {'llave': ['product_id'], 'orden': 'last_updated', 'cols': [
   ['product_id','str'], ['customer_id','str'], ['product_type','str'],
   ['product_number','tokdoc','product_number_token'], ['currency','moneda'],
   ['current_balance','dinero'], ['credit_limit','dinero'], ['interest_rate','num'],
   ['opening_date','fecha'], ['expiration_date','fecha'], ['opening_branch_id','str'],
   ['product_status','str'], ['opening_channel','str'], ['has_linked_app','bool'],
   ['days_past_due','int'], ['last_transaction_date','ts'], ['last_updated','ts']]},
 'transactions': {'llave': ['transaction_id'], 'orden': 'transaction_date', 'cols': [
   ['transaction_id','str'], ['transaction_date','ts'], ['process_date','fecha'], ['product_id','str'],
   ['customer_id','str'], ['transaction_type','str'], ['transaction_category','str'],
   ['amount','dinero'], ['currency','moneda'], ['amount_usd','dinero','amount_usd_fuente'],
   ['channel','str'], ['branch_id','str'], ['merchant_name','str'], ['merchant_category','str'],
   ['transaction_country','pais'], ['transaction_city','str'], ['transaction_status','str'],
   ['response_code','str'], ['is_fraud','bool'], ['fraud_score','flt']]},
 'call_center_interactions': {'llave': ['interaction_id'], 'orden': 'interaction_date', 'cols': [
   ['interaction_id','str'], ['interaction_date','ts'], ['process_date','fecha'], ['customer_id','str'],
   ['agent_id','str'], ['interaction_type','str'], ['channel','str'], ['contact_reason','str'],
   ['reason_category','str'], ['duration_seconds','int'], ['wait_time_seconds','int'],
   ['was_resolved','bool'], ['requires_followup','bool'], ['detected_sentiment','str'],
   ['sentiment_score','flt'], ['customer_detected_accent','str'], ['agent_used_accent','str'],
   ['was_escalated','bool'], ['mentioned_products','str'], ['has_transcript','bool'], ['has_recording','bool']]},
 'complaints': {'llave': ['complaint_id'], 'orden': 'creation_date', 'cols': [
   ['complaint_id','str'], ['creation_date','ts'], ['process_date','fecha'], ['customer_id','str'],
   ['case_type','str'], ['category','str'], ['subcategory','str'], ['reception_channel','str'],
   ['affected_product_id','str'], ['related_branch_id','str'], ['origin_interaction_id','str'],
   ['claimed_amount','dinero'], ['currency','moneda'], ['priority','str'], ['status','str'],
   ['assigned_agent_id','str'], ['assignment_date','ts'], ['first_response_date','ts'],
   ['resolution_date','ts'], ['closing_date','ts'], ['sla_breached','bool'], ['resolution_days','flt'],
   ['compensation_granted','dinero'], ['resolution_satisfaction','flt'], ['is_repeat_complainer','bool']]},
 'satisfaction_surveys': {'llave': ['survey_id'], 'orden': 'survey_date', 'cols': [
   ['survey_id','str'], ['survey_date','ts'], ['process_date','fecha'], ['interaction_id','str'],
   ['customer_id','str'], ['agent_id','str'], ['survey_type','str'], ['send_channel','str'],
   ['main_score','flt'], ['nps_category','str'], ['question_1_response','flt'],
   ['question_2_response','flt'], ['question_3_response','flt'], ['comment_sentiment','str'],
   ['response_time_hours','flt'], ['campaign_response_rate','flt']]},
 'service_agents': {'llave': ['agent_id'], 'orden': none, 'cols': [
   ['agent_id','str'], ['native_accent','str'], ['country_of_origin','pais'], ['assigned_branch_id','str'],
   ['agent_type','str'], ['experience_level','str'], ['languages','str'], ['specialty','str'],
   ['hire_date','fecha'], ['avg_csat','flt'], ['total_monthly_interactions','int'],
   ['agent_status','str'], ['work_shift','str']]},
 'daily_exchange_rates': {'llave': ['date','source_currency','target_currency'], 'orden': none, 'cols': [
   ['date','fecha'], ['source_currency','moneda'], ['target_currency','moneda'],
   ['exchange_rate','num'], ['buy_rate','num'], ['sell_rate','num'], ['source','str']]},
 'call_transcripts': {'llave': ['transcript_id'], 'orden': 'process_date', 'cols': [
   ['transcript_id','str'], ['interaction_id','str'], ['process_date','fecha'], ['customer_id','str'],
   ['agent_id','str'], ['detected_language','str'], ['detected_accent','str'], ['accent_confidence','flt'],
   ['detected_keywords','str'], ['detected_intents','str'], ['main_topics','str'],
   ['transcription_model','str'], ['audio_quality','str'], ['duration_seconds','int']]},
 'digital_events': {'llave': ['event_id'], 'orden': 'event_date', 'cols': [
   ['event_id','str'], ['event_date','ts'], ['process_date','fecha'], ['customer_id','str'],
   ['session_id','str'], ['event_type','str'], ['event_category','str'], ['channel','str'],
   ['platform','str'], ['app_version','str'], ['page_title','str'], ['action','str'],
   ['element_id','str'], ['product_id','str'], ['event_value','flt'], ['duration_seconds','int'],
   ['ip_country','pais'], ['is_mobile','bool']]},
 'branches': {'llave': ['branch_id'], 'orden': none, 'cols': [
   ['branch_id','str'], ['branch_code','str'], ['branch_name','str'], ['branch_type','str'],
   ['city','str'], ['state','str'], ['country','pais'], ['geographic_zone','str'],
   ['opening_time','str'], ['closing_time','str'], ['has_atms','bool'], ['atm_count','int'],
   ['has_teller_windows','bool'], ['teller_window_count','int'], ['branch_opening_date','fecha'],
   ['branch_status','str']]},
 'marketing_campaigns': {'llave': ['campaign_id'], 'orden': none, 'cols': [
   ['campaign_id','str'], ['campaign_name','str'], ['campaign_type','str'], ['campaign_objective','str'],
   ['promoted_product','str'], ['target_segment','str'], ['target_country','pais'],
   ['start_date','fecha'], ['end_date','fecha'], ['budget','dinero'], ['campaign_status','str'],
   ['expected_conversion_rate','flt']]},
 'campaign_sends': {'llave': ['send_id'], 'orden': 'send_date', 'cols': [
   ['send_id','str'], ['send_date','ts'], ['process_date','fecha'], ['campaign_id','str'],
   ['customer_id','str'], ['send_channel','str'], ['send_status','str'], ['was_delivered','bool'],
   ['was_opened','bool'], ['open_date','ts'], ['was_clicked','bool'], ['click_date','ts'],
   ['click_count','int'], ['had_conversion','bool'], ['conversion_date','ts'],
   ['conversion_value','dinero'], ['open_country','pais'], ['failure_reason','str'], ['send_cost','num']]}
} %}
{{ return(e) }}
{% endmacro %}

{# Texto sin vacíos: nulo si es cadena vacía #}
{% macro vacio(c) %}nullif(trim(`{{ c }}`), ''){% endmacro %}

{% macro pais_iso(c) %}
case regexp_replace(normalize(lower(trim(`{{ c }}`)), NFD), r'\pM', '')
  when 'mexico' then 'MX' when 'colombia' then 'CO' when 'argentina' then 'AR'
  when 'usa' then 'US' when 'united states' then 'US' when 'estados unidos' then 'US'
  when 'spain' then 'ES' when 'espana' then 'ES' when 'brazil' then 'BR' when 'brasil' then 'BR'
end
{%- endmacro %}

{# Seudónimo: SHA-256(secreto || valor normalizado); el secreto vive en latam_seguridad.llave #}
{% macro token(valor) %}
to_hex(sha256(concat((select secret from {{ source('seguridad', 'llave') }}), cast({{ valor }} as bytes))))
{%- endmacro %}

{# Expresión canónica de una columna cruda #}
{% macro expr(c, tipo) %}
{%- if tipo == 'str' -%}{{ vacio(c) }}
{%- elif tipo == 'int' -%}safe_cast(round(safe_cast({{ vacio(c) }} as numeric)) as int64)
{%- elif tipo == 'dinero' -%}round(safe_cast({{ vacio(c) }} as numeric), 2)
{%- elif tipo == 'num' -%}safe_cast({{ vacio(c) }} as numeric)
{%- elif tipo == 'flt' -%}safe_cast({{ vacio(c) }} as float64)
{%- elif tipo == 'fecha' -%}safe_cast({{ vacio(c) }} as date)
{%- elif tipo == 'ts' -%}safe_cast({{ vacio(c) }} as datetime)
{%- elif tipo == 'bool' -%}safe_cast({{ vacio(c) }} as bool)
{%- elif tipo == 'pais' -%}{{ pais_iso(c) }}
{%- elif tipo == 'moneda' -%}if(regexp_contains(upper({{ vacio(c) }}), r'^[A-Z]{3}$'), upper({{ vacio(c) }}), null)
{%- elif tipo == 'tokdoc' -%}{{ token('upper(' ~ vacio(c) ~ ')') }}
{%- elif tipo == 'tokmail' -%}{{ token('lower(' ~ vacio(c) ~ ')') }}
{%- elif tipo == 'tokfono' -%}{{ token("nullif(regexp_replace(`" ~ c ~ "`, r'[^0-9]', ''), '')") }}
{%- endif -%}
{% endmacro %}

{# Bronce sin duplicados: gana el mayor `orden`, luego la huella de la fila (determinista) #}
{% macro dedup_bronce(tabla, relacion=none) %}
{%- set s = esquema()[tabla] -%}
select * from {{ relacion if relacion else source('bronce', 'bronce_' ~ tabla) }} as b
qualify row_number() over (
  partition by {% for k in s['llave'] %}`{{ k }}`{{ ', ' if not loop.last }}{% endfor %}
  order by {% if s['orden'] %}safe_cast(`{{ s['orden'] }}` as datetime) desc nulls last, {% endif %}
  farm_fingerprint(to_json_string(b)) desc
) = 1
{% endmacro %}

{# Plata de una tabla: dedup, luego tipos canónicos. `relacion` permite sustituir la entrada (pruebas unitarias) #}
{% macro plata_base(tabla, relacion=none) %}
{%- set s = esquema()[tabla] -%}
select
{%- for col in s['cols'] %}
  {{ expr(col[0], col[1]) }} as `{{ col[2] if col|length > 2 else col[0] }}`{{ ',' if not loop.last }}
{%- endfor %}
from ({{ dedup_bronce(tabla, relacion) }})
{% endmacro %}

{# Condición de "no vacío pero no se pudo convertir" para una columna #}
{% macro fallo(c, tipo) %}
{{ vacio(c) }} is not null and {{ expr(c, tipo) }} is null
{%- endmacro %}
