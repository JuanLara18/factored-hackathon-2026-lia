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

## Trazabilidad, respaldo y vencimiento

`just manifiesto` recorre el espejo local y escribe `platino_manifiesto_carga` (un registro por archivo:
ruta relativa a `s3://<bucket>/data/`, bytes, sha256, filas de datos, tabla destino) y `platino_manifiesto_tablas`
(por tabla: archivos, suma de filas de CSV, filas en BigQuery, bandera `coincide`, `job_id` y huella encadenada
`sha256(huella previa + registro)`). El resumen por tabla, sin PII, queda en `manifiestos/`. `just verificar-cadena`
recomputa la cadena y sale con 1 si alguien editó un manifiesto viejo. La primera corrida (13 de 13 tablas con
`coincide = true`) se calculó sobre la carga ya hecha: su `job_id` es `null` porque esa carga se hizo antes de que el cargador lo
registrara. El cargador ahora escribe a `bronce_<t>_nuevo`, compara con las filas de los CSV y solo entonces
reemplaza la tabla vigente (si no cuadra, la borra y no toca la vigente). Límite del sandbox: recargar `digital_events` (3,9 GB) necesita
espacio para `_nuevo` y la vigente a la vez, y el tope de 10 GB no lo permite hoy; habría que borrar tablas que no se usan.

`just comparar-respaldo` compara `respaldo_20260831` con el espejo por ruta relativa y sha256 (y filas donde difieren) y
guarda solo el resumen en `platino_comparacion_respaldo` y `manifiestos/comparacion_respaldo.json`. El respaldo no se carga.
Hallazgo: solo `branches`, `daily_exchange_rates` y `marketing_campaigns` son idénticos; el respaldo no trae `call_transcripts` ni
`satisfaction_surveys`; `transactions` del respaldo llega hasta 2024-09-25 (453 de 1.097 archivos), y así está en el bucket
del organizador (verificado con `aws s3 ls` el 29 sep: 453 objetos; la descarga local está completa); el resto difiere en contenido con conteos de filas distintos en `call_center_interactions`, `campaign_sends`,
`digital_events` y `transactions`.

**Vencimiento.** Las tablas del sandbox vencen el 2026-11-28. Fuente reproducible: el espejo local
(`aws s3 sync`) más el manifiesto, que dice qué archivos y qué huellas produjeron cada tabla; con eso se recarga y se verifica.
`just inventario` deja `platino_inventario_insumos` (clase de procedencia, origen, `AS_OF`); la política de
actualización está en `POLITICA_ACTUALIZACION.md`.

## Plata, oro y platino (dbt)

`just dbt-build` crea la llave (una sola vez, idempotente) y corre `dbt build` sobre BigQuery (`datos/dbt`, perfil
`profiles.yml` sin secretos: identidad por gcloud/ADC; `LATAM_GCP_PROJECT`, `LATAM_BQ_DATASET`, `LATAM_GCP_LOCATION`).
Todo vive en el dataset `latam_bank` con prefijo de capa.

| Modelo | Qué es |
|---|---|
| `plata_<tabla>` (13) | tipos canónicos con `SAFE_CAST` (dinero `NUMERIC(2)`, fechas `DATE`, marcas `DATETIME`, país ISO 3166), dedup por llave (gana la mayor fecha de actualización, luego la huella de la fila). `plata_digital_events` es **vista** (15,6 M filas) por el tope de 10 GB del sandbox |
| `plata_transactions.amount_usd` | si la fuente lo trae vacío (57% de las filas) se recalcula: USD igual al monto, otras monedas por la tasa del día de `plata_daily_exchange_rates`; `amount_usd_origen` marca `fuente`, `igual_monto`, `recalculado_tasa` o `sin_tasa` |
| `platino_cast_fallidos` | por columna, cuántos valores no vacíos no se pudieron convertir (pasan a NULL en plata). Ya detectó `products.last_transaction_date`, que es marca de tiempo y no fecha |
| `platino_huerfanos`, `platino_conteos_plata` | llaves huérfanas por relación; filas de bronce contra plata y duplicados descartados |
| `oro_operacional_*` (7) | `transacciones_recientes` (180 días antes de `AS_OF`, sin `is_fraud` ni `fraud_score`), `estado_productos`, `vista_cliente_segura`, `reclamos_cliente` (sin producto afectado ni monto reclamado), `directorio_comercios` (24 comercios; razón social, descriptor y marca inventados por el equipo, `origen = 'equipo'`), y las **vistas** `ficha_transaccion` (directorio, compras previas 12 meses, posibles duplicados 48 h, tasa y explicación del estado, todo con datos anteriores al evento, sin `fraud_score`) y `riesgo_transaccion` (`fraud_score` y `banda_riesgo`: alto sobre 30, zona gris desde 25, parámetros `riesgo_*` de `dbt_project.yml`; sin `is_fraud`); contratos ODCS en `contratos/` |
| `dominios_canonicos` (seed) | dominios de `dominios/dominios_canonicos.csv`: canal, tipo y estado de transacción, categoría de comercio, tipo y estado de producto, categoría, subcategoría, canal, prioridad y estado de reclamo, banda de riesgo (valor de la fuente y etiqueta en español). Prueba genérica `dominio_canonico` con severidad `warn` en cada columna de oro |
| `oro_analitico_linea_base_reclamos` | reclamos por país, canal y mes |

Tests: llaves `unique`/`not_null` y `relationships` (huérfanas) con severidad `warn` y `store_failures` (tablas en `latam_pruebas`).
Fixture: `fixtures/refresco.yml` son 10 casos FX-01 a FX-10 (duplicado, reentrega, llegada tardía, fallo de conversión, moneda inválida,
huérfano, dueño ajeno, `amount_usd` recalculado, país, seudónimos) como unit tests de dbt (`just dbt-test-fixture`).

**Privacidad (C2).** La llave vive en `latam_seguridad.llave` (32 bytes aleatorios, generados dentro de BigQuery por `crear_llave`,
nunca en el repositorio). Documento, correo y teléfonos (y el número de producto) llegan a plata como `SHA-256(secreto || valor
normalizado)`; nombres, dirección, fecha de nacimiento, IP y texto libre no pasan. `plata_restringida_clientes` guarda género, estado civil,
educación y banda de edad solo para auditar equidad. En el sandbox el IAM es de proyecto, así que esa separación es por construcción, no por
control de acceso; el destino de producción son etiquetas de política (policy tags) en las columnas, vistas autorizadas para oro operacional
y acceso a `latam_seguridad` solo para la cuenta del pipeline.

**Recortes.** Sin cuarentena por fila ni lotes (bronce sin `_lote_id`); los dominios canónicos conservan los valores de la fuente (en inglés salvo producto y subcategoría), la traducción es solo etiqueta; las bandas de riesgo son provisionales hasta que Gobierno fije la zona gris; `plata_digital_events` sin conteos de plata.

## Dataset de pruebas

`latam_pruebas` guarda los fallos de las pruebas de dbt (`store_failures`) y las tablas temporales de las
pruebas unitarias, con vencimiento de 7 días, para que `latam_bank` solo muestre las capas.
