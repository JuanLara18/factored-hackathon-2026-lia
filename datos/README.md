# VP Datos: ingesta, capas y contratos

| Ruta | Qué es |
|---|---|
| `definicion.md` | definición de la cara (reglas R-DAT) |
| `contratos/` | contratos ODCS |
| `dominios/` | mapeos de valores crudos a canónicos |
| `dbt/` | plata, oro y platino |
| `fixtures/` | fixture de actualización, generado por el equipo |
| `src/latam_datos/` | bronce, vigilancia del bucket, tokenización |

## Carga supuesta

La carga del dataset queda fuera de alcance (D-30). Un proceso externo baja el bucket del organizador y deja
cada archivo como tabla cruda en el dataset `latam_bank` de BigQuery: tabla `bronce_<archivo>` (la capa es el prefijo del nombre) y
todas las columnas `STRING`. Este es el contrato que ese proceso debe cumplir (`src/latam_datos/contrato.py`);
las columnas listadas son las que `definicion.md` nombra de forma explícita, el resto se confirma en F1.

| Tabla (`latam_bank.bronce_<tabla>`) | Llave | Columnas requeridas | Partición diaria |
|---|---|---|---|
| `customers` | `customer_id` | `customer_id`, `document_type` | no |
| `products` | `product_id` | `product_id`, `customer_id` | no |
| `transactions` | `transaction_id` | `transaction_id`, `product_id`, `customer_id`, `process_date` | `process_date` |
| `call_center_interactions` | `interaction_id` | `interaction_id`, `customer_id`, `process_date` | `process_date` |
| `complaints` | `complaint_id` | `complaint_id`, `customer_id`, `affected_product_id` | no |
| `satisfaction_surveys` | sin llave | `interaction_id`, `survey_date` | no |
| `call_transcripts` | sin llave | `interaction_id` | no |
| `digital_events` | sin llave | `customer_id`, `process_date` | `process_date` |
| `campaign_sends` | sin llave | `process_date` | `process_date` |
| `service_agents`, `daily_exchange_rates`, `branches`, `marketing_campaigns` | sin llave | ninguna todavía | no |

## Validación de bronce

`just validar` (o `python -m latam_datos validar`, con `LATAM_GCP_PROJECT` y `LATAM_GCP_LOCATION`) evalúa las
reglas sobre esas tablas y escribe una fila por hallazgo, y una fila `ok` por regla sin hallazgos, en
`latam_bank.platino_reporte_calidad_corrida`. Sale con código 1 si hay un hallazgo bloqueante.

| Regla | Qué comprueba | Severidad |
|---|---|---|
| Q-BRZ-01 | días de la ventana 2023-06-17 a 2026-06-17 sin filas, en tablas con `process_date` | aviso |
| Q-BRZ-03 | tabla esperada y columnas requeridas presentes; columnas que no son texto | bloqueante o aviso |
| Q-BRZ-05 | llave vacía; `process_date` no interpretable como fecha | aviso |
| Q-BRZ-06 | filas por día fuera de los percentiles 1 y 99 de su día de la semana | aviso |
| Q-BRZ-11 | tabla vacía | aviso |
| Q-BRZ-12 | llaves repetidas (plata elige el ganador) | aviso |
| Q-BRZ-13 | columnas requeridas con más de 0,5% de vacíos | aviso |

Reglas descartadas de la definición, porque hablan de objetos, archivos o lotes que ya no vemos:
Q-BRZ-02 (BOM), Q-BRZ-04 (codificación UTF-8), Q-BRZ-07 (generación única de objetos), Q-BRZ-08
(solapamiento de llaves de una reentrega), Q-BRZ-09 (objetos fuera de la fuente autorizada) y Q-BRZ-10
(mismo etag). Q-BRZ-05 (filas malformadas) se reinterpreta como llave vacía y fecha ilegible, y
Q-BRZ-03 (encabezado) como columnas requeridas presentes. Q-BRZ-12 y Q-BRZ-13 son nuevas. Tampoco hay
`_lotes` ni `_linea`: sin lotes, la detección de regeneración y la idempotencia por etag son del proceso de carga.
