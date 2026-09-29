-- Atributos protegidos solo para auditar equidad (4.5). Justificación: Gobierno los necesita para medir
-- disparidad por género, estado civil, educación y edad; sin nombres, documento, contacto ni dirección.
-- La fecha de nacimiento se reduce a banda de edad a la fecha AS_OF.
with c as ({{ dedup_bronce('customers') }})
select
  customer_id,
  {{ vacio('gender') }} as gender,
  {{ vacio('marital_status') }} as marital_status,
  {{ vacio('education_level') }} as education_level,
  case
    when age is null then null
    when age < 25 then '18-24' when age < 35 then '25-34' when age < 45 then '35-44'
    when age < 55 then '45-54' when age < 65 then '55-64' else '65+'
  end as banda_edad
from (
  select c.*, date_diff(date('{{ var("as_of") }}'), safe_cast(date_of_birth as date), year) as age from c
)
