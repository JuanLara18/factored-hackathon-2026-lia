# Investigación 13: auditoría del dataset LATAM Bank (muestra)

**Pregunta:** ¿el bucket trae lo que dicen el resumen y el diccionario? ¿Qué etiquetas tienen señal,
qué relaciones son coherentes y qué problemas de calidad existen de verdad?

**Hallazgo central:** la estructura transaccional (clientes, productos, transacciones) es coherente;
la capa de servicio (motivos, transcripciones, quejas) es en buena parte **plantilla o sorteo
independiente**. Eso invalida varios supuestos de las investigaciones anteriores (sección 5) y
cambia el componente aprendido (D-09, y en la segunda pasada, D-14).

**Estado:** muestra, no total. Cada cifra se confirma sobre el total al construir la capa bronce
([03_Datos_por_capas.md](../Diseno/03_Datos_por_capas.md), sección 11).

---

## 1. Método

- **Fecha:** 26 de septiembre de 2026.
- **Acceso:** listado completo del bucket y descarga de muestras con la llave de solo lectura, leída
  en memoria desde el PDF del diccionario; nunca escrita en disco, en el repositorio ni en un prompt.
- **Muestra:**

| Tabla | Particiones | Filas |
|---|---|---|
| `call_center_interactions` | ene y feb 2025, 10 y 11 mar 2025, jun 2026 | 47.728 |
| `call_transcripts` | idem | 11.903 |
| `complaints` | idem | 4.790 |
| `satisfaction_surveys` | idem | 14.793 |
| `transactions` | ene y feb 2025 | 232.688 |
| `customers`, `products` | completas | 150.000 y 400.000 |
| `data_backup_20260831/call_center_interactions` | 10 mar 2025 | 707 |

- **Herramientas:** pandas y scikit-learn en Python 3.12; los scripts fueron exploratorios y **no se
  conservaron**. Las pruebas quedan escritas en la sección 3 como consultas de DuckDB para
  reproducirlas sobre bronce.

## 2. Resultados

Las tablas completas están en [03_Datos_por_capas.md](../Diseno/03_Datos_por_capas.md), sección 2.
Resumen:

| Frente | Resultado |
|---|---|
| Forma física | CSV con BOM, particiones Hive diarias (1.097), 5,3 GB en `data/`; una segunda generación en `data_backup_20260831/` sin IDs en común |
| Diccionario contra datos | valores en español; `contact_reason` = `reason_category` (6 valores, uno no documentado); México sin MXN (todo USD); NPS entre 2 y 7 |
| Calidad | 0 duplicados en la muestra (se anunciaba ~2%); nulos estructurales altos; `process_date` desplazado respecto al evento (00:00 a 07:59 al día anterior; encuestas hasta 2 días "antes") |
| Integridad | transacciones, productos y clientes coherentes; `complaints.origin_interaction_id` vacío siempre; `complaints.affected_product_id` de otro cliente en el 100% |
| Señal | texto de transcripción independiente de la categoría (V de Cramér 0,011); `main_topics` = etiqueta; `was_escalated` AUC 0,51; `was_resolved` 0,77; `fraud_score` 0,87 contra `is_fraud` (prevalencia 0,10%) |
| Demanda | "Cargo no reconocido" = 18% de las quejas (866 de 4.790) |
| Idioma | `detected_language` = `es` en todas las filas; sin portugués |

## 3. Pruebas reproducibles (para la capa bronce)

Consultas en DuckDB sobre las tablas de bronce (todo como texto). Cada una es un chequeo del
reporte de auditoría.

```sql
-- 1. Duplicados por llave y por contenido
SELECT count(*) - count(DISTINCT interaction_id) AS dup_pk FROM bronce.call_center_interactions;

-- 2. contact_reason es copia de reason_category
SELECT avg((contact_reason = reason_category)::INT) FROM bronce.call_center_interactions;

-- 3. Desfase entre process_date y la fecha del evento
SELECT date_diff('day', CAST(interaction_date AS TIMESTAMP)::DATE, CAST(process_date AS DATE)) AS lag,
       count(*) FROM bronce.call_center_interactions GROUP BY 1 ORDER BY 1;

-- 4. Coherencia de dueño en quejas
SELECT avg((q.customer_id = p.customer_id)::INT) AS mismo_duenio
FROM bronce.complaints q JOIN bronce.products p ON q.affected_product_id = p.product_id;

-- 5. Monto reclamado respaldado por una transacción del cliente
SELECT count(DISTINCT q.complaint_id) FROM bronce.complaints q
JOIN bronce.transactions t ON t.customer_id = q.customer_id
 AND round(CAST(t.amount AS DOUBLE), 2) = round(CAST(q.claimed_amount AS DOUBLE), 2)
WHERE q.subcategory = 'Cargo no reconocido';

-- 6. Plantillas en transcripciones
SELECT count(DISTINCT full_text), count(DISTINCT split_part(full_text, chr(10), 1)),
       avg(regexp_matches(full_text, '\{\w+\}')::INT) FROM bronce.call_transcripts;

-- 7. Moneda por país del cliente
SELECT c.country, p.currency, count(*) FROM bronce.products p
JOIN bronce.customers c USING (customer_id) GROUP BY ALL ORDER BY ALL;

-- 8. Generaciones distintas en el bucket
SELECT count(*) FROM bronce.call_center_interactions a
JOIN bronce_backup.call_center_interactions b USING (interaction_id);
```

Las pruebas de señal (V de Cramér del texto contra la categoría; AUC con validación cruzada de un
*gradient boosting* sobre canal, motivo, sentimiento, duración, espera y segmento; AUC de
`fraud_score`) se rehacen en el notebook de EDA de oro con partición temporal.

## 4. Limitaciones de esta auditoría

- Tres meses de servicio y dos de transacciones: los duplicados y las llegadas tardías pueden estar
  en otras particiones (2023, 2024).
- `campaign_sends` no se auditó; `digital_events` y `service_agents` se revisaron en la segunda
  pasada (sección 6), `digital_events` solo con enero de 2025.
- La AUC de `was_resolved` se estimó con validación cruzada aleatoria, no temporal.

## 5. Qué cambia en lo escrito antes

| Documento | Supuesto previo | Estado tras la auditoría |
|---|---|---|
| Investigación 1, sección 3 | verificar que `contact_reason` muestre las transacciones no reconocidas | `contact_reason` no distingue motivos finos; la evidencia está en `complaints.subcategory` (18%) |
| Investigación 4, secciones 5 y 7 | semillas de casos desde transcripciones y quejas; línea base de negocio con `was_escalated` | transcripciones inservibles como semilla; quejas sin transacción enlazable; `was_escalated` es ruido. Semillas desde **transacciones y productos** reales y conversaciones escritas por el equipo |
| Investigación 5, secciones 1 y 3 | clasificador de intención con `contact_reason` como etiqueta | confirmada la trampa que la propia investigación anticipaba: sin señal; componente principal pasa al riesgo de transacción (D-09) |
| Investigación 7, sección 1 | el dataset trae las métricas del contact center | trae los campos, pero escalamiento sin señal y NPS truncado; la línea base de negocio se reporta con esa advertencia |
| Investigación 9, secciones 1 y 3 | grafo con aristas interacción, reclamo y producto; punto de compromiso medible con quejas | esas aristas no son reales; el punto de compromiso solo puede venir de `transactions` (comercio en 23% de las filas, fraude 0,1%); **no hay contraparte en transferencias**, así que las mulas no son modelables |
| Diseño 01, secciones 5.4, 5.8 y 6 | clasificador de motivo como componente; ~2% de duplicados; semillas de transcripciones | actualizado |
| Diseño 02, F1 y F4 | EDA y clasificador por hacer | actualizado |
| README | tabla del dataset con `contact_reason` e intenciones como útiles | actualizado |

## 6. Segunda pasada (26 de septiembre de 2026)

Hecha al releer el enunciado ([05 de diseño](../Diseno/05_Cobertura_del_enunciado.md)). Muestra
adicional: `service_agents`, `daily_exchange_rates` y `digital_events` de enero de 2025 (443.948
eventos). El bucket no cambió desde el 1 de septiembre.

| Frente | Resultado |
|---|---|
| Etiqueta de fraude | sin `fraud_score`, un modelo entrenado en enero y probado en febrero da AUC 0,504 y PR AUC igual a la prevalencia; la tasa de fraude es plana por canal, tipo y país |
| `fraud_score` | ninguna transacción legítima pasa de 30; `fraud_score > 30` es fraude con precisión 1,0 y recuperación 0,57: **fuga de la etiqueta** |
| `digital_events` | la IP nunca es de otro país que el del cliente; menos del 1% de las transacciones tiene eventos en las 24 h previas, sin diferencia por fraude; 23,6% de eventos sin cliente; "México" y "Mexico" conviven |
| Comercios | 24 nombres genéricos; mediana de 2 transacciones por cliente en dos meses; 1,9% de pares cliente y comercio repetidos |
| Agentes | 129 de 1.200 hablan portugués; 105 especialistas en fraude, 7 con portugués; 25 especialistas en fraude de noche, 1 con portugués en turno de noche o rotativo |
| Demanda | plana por hora; fines de semana a la mitad; 84,8% telefónica |
| Proceso de reclamos | mediana de 38 h a la primera respuesta, 17 días a la resolución, 20,6% de SLA incumplido; iguales entre subcategorías, y `sla_breached` sin relación con `resolution_days` |
| Tasas de cambio | 13.164 filas y 12 pares con MXN (el diccionario dice 3.000 filas), aunque no hay transacciones en MXN |
| Clientes | edades entre 21 y 84, 31% de 65 años o más; género y estado civil repartidos casi en tercios y cuartos iguales |

**Qué cambia:** el componente aprendido sobre `is_fraud` no tiene cómo ganar (D-14 reemplaza a D-09 si
el total lo confirma); `digital_events` no sirve para modelar toma de cuenta; ubicar la transacción es
casi trivial con filtros; el traspaso en portugués y de noche es una restricción operativa real.
