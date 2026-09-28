# Datos por capas: de la fuente cruda a la evidencia (borrador 1)

**Propósito:** diseñar el capítulo de ingeniería de datos con la mirada del jurado. El enunciado dice
que *"every team is assessed on data engineering and AI/ML rigor"* y pide, en el criterio 4,
preparación repetible con **contratos, chequeos de calidad, linaje y política de frescura**, y en la
sección de arquitectura, **demostrar la corrección de las actualizaciones con un fixture etiquetado**
si los datos son estáticos. Este documento dice qué capas hay, qué garantiza cada una, qué EDA se
hace en cuál y qué cambia en el resto del diseño a partir de lo que realmente trae el bucket.

**Base empírica:** el 26 de septiembre de 2026 se listó el bucket completo (solo lectura) y se
perfiló una muestra: `call_center_interactions`, `call_transcripts`, `complaints` y
`satisfaction_surveys` de enero, febrero y marzo (10 y 11) de 2025 y junio de 2026 (47.728
interacciones, 11.903 transcripciones, 4.790 quejas, 14.793 encuestas); `transactions` de enero y
febrero de 2025 (232.688 filas); `customers` y `products` completos. Las cifras de la sección 2 son
**de esa muestra** y se confirman sobre el total en F1. El método y las consultas para reproducirla
están en la [investigación 13](../Investigacion/13_Auditoria_del_dataset.md). Principios que rigen:
P10, P11, P13.

---

## 0. El veredicto del juez, en seis frases

1. El dataset no es lo que dice el diccionario: los valores están en español, `contact_reason` es
   una copia de `reason_category`, México no tiene pesos y hay una segunda generación del dataset en
   el mismo bucket. **Documentar esa distancia es el primer entregable de datos**, no un detalle.
2. Las transcripciones son plantillas: dos frases de apertura en total, marcadores sin llenar
   (`{monto} {moneda}`) y **ninguna relación con la categoría** (V de Cramér 0,011). No sirven para
   entrenar ni evaluar un clasificador de intención.
3. Las quejas no se pueden enlazar con nada: `origin_interaction_id` está vacío siempre y
   `affected_product_id` **pertenece a otro cliente en el 100% de los casos**. Eso es un caso de
   prueba de autorización servido, no un dato para anclar respuestas.
4. Donde sí hay estructura coherente es en `customers`, `products` y `transactions` (llaves
   foráneas y monedas consistentes, `fraud_score` con AUC 0,87 contra `is_fraud`). **El flujo de
   disputas se ancla ahí**, y la demanda del motivo se prueba con `complaints.subcategory`.
5. Las capas (bronce, plata, oro, platino) valen si cada una tiene **un contrato, una pregunta que
   responde y un consumidor**; si son solo carpetas, el jurado no ve rigor sino nombres.
6. Todo esto cabe en un portátil: 5,3 GB de CSV. DuckDB y Parquet, sin nube ni Spark. La
   sofisticación va en las garantías (idempotencia, cuarentena, linaje, frescura), no en la
   infraestructura.

---

## 1. Qué mira el jurado en este capítulo

| Exigencia del enunciado | Cómo se ve en una buena entrega | Capa donde vive |
|---|---|---|
| Preparación **repetible** | un comando reconstruye todo desde la fuente; correrlo dos veces da lo mismo (huella igual) | todas |
| **Contratos** | un YAML por tabla con esquema, dominios, llaves, reglas, PII y frescura; se valida en cada corrida | frontera bronce a plata y oro de consumo |
| **Chequeos de calidad** | severidad explícita (bloquea o advierte), filas rechazadas a cuarentena con motivo, reporte por corrida | plata |
| **Linaje** | de cada tabla de oro se puede llegar al archivo de S3 y a la versión del código | manifiesto por corrida y grafo de dbt |
| **Política de frescura** | por tabla: cadencia, retraso tolerado y qué hace el agente si el dato está viejo | contrato de oro |
| **Corrección de actualizaciones** | *fixture* etiquetado con llegada tardía, duplicado y cambio de esquema; resultado esperado verificado por prueba | pruebas del pipeline |
| Datos reales, sintéticos o del equipo, **identificados** | cada tabla y cada caso de evaluación lleva su origen | metadatos de todas las capas |
| Sin datos restringidos en solicitudes externas | el modelo solo ve vistas minimizadas y enmascaradas | oro operacional |

## 2. Lo que realmente trae el bucket

### 2.1 Forma física

| Hecho | Detalle | Consecuencia |
|---|---|---|
| Formato | CSV UTF-8 **con BOM** (`U+FEFF` antes del primer encabezado) | leer con `utf-8-sig`; si no, la primera columna se llama `U+FEFF` pegado a `interaction_id` y todos los joins fallan en silencio |
| Particionado | estilo Hive `year=/month=/day=`, un archivo por día, 1.097 particiones (17 de junio de 2023 a 17 de junio de 2026); `campaign_sends` 1.083 | la unidad de ingesta y de reproceso es la partición diaria |
| Tamaño | `data/` pesa 5,3 GB; `digital_events` sola son 3,8 GB | todo cabe local; `digital_events` se ingiere a bronce pero se difiere en plata si el flujo no la usa |
| Dimensiones | un solo archivo por tabla (`customers.csv`, `products.csv`...) aunque el diccionario dice *monthly_snapshot* | no hay historia: no se puede hacer SCD2 real ni consultas "a la fecha" sobre clientes y productos |
| **Segunda generación** | `data_backup_20260831/` con 11 tablas: sin `call_transcripts` ni `satisfaction_surveys`, `transactions` solo hasta el 25 de septiembre de 2024, y **ningún ID en común** con `data/` en la misma partición (707 contra 768 interacciones el 10 de marzo de 2025) | no es una versión anterior de las mismas filas sino otra corrida del generador; ver 5.3 |
| Archivo suelto | `marketing_campaigns.csv` en la raíz del bucket, de julio | la fuente autorizada es `data/`; se declara en el contrato |

### 2.2 Diccionario contra realidad

| Campo | El diccionario dice | Los datos traen |
|---|---|---|
| `reason_category` | Transactional, Product, Technical, Commercial, Complaint | Transaccional, Producto, Técnico, Comercial, Queja **y Retención** (no documentada) |
| `contact_reason` | "main contact reason", VARCHAR(100) | **idéntico a `reason_category` en el 100% de las filas**: no hay motivo fino |
| `product_type` | Checking Account, Credit Card... | Cuenta Ahorro, Tarjeta Crédito, Préstamo Hipotecario... |
| `document_type` | DNI, CURP, CC, CE, Passport | DNI, CC, CE, **Pasaporte**; no hay CURP; México y Argentina usan DNI |
| Moneda de México | MXN | **no existe MXN**: productos y transacciones de clientes mexicanos están en USD |
| `transaction_country` | país | "México" y "Mexico" conviven; además USA, Brazil y Spain (cerca del 3%) |
| `main_score` | CSAT 1 a 5, NPS 0 a 10 | CSAT y CES entre 1 y 4, NPS entre 2 y 7: **no hay promotores** |
| `detected_intents` | intenciones identificadas | `consulta_general` en todas las filas no vacías |
| `main_topics` | tópicos | **idéntico a `reason_category`** |
| `complaints.category` | categoría | inglés (Fees, Branch...), mientras `subcategory` va en español |

**Lectura de experto:** esto es **deriva semántica** entre la documentación y la fuente, el problema
más común y más caro en un banco real. La capa plata la resuelve con tablas de mapeo versionadas
(`dominios/*.csv`) y el contrato registra ambos valores, el crudo y el canónico.

### 2.3 Calidad anunciada contra observada

| Problema anunciado | Observado en la muestra | Qué hacer |
|---|---|---|
| ~2% de duplicados | **cero** por llave primaria, cero exactos y cero por contenido sin llave, en todas las tablas de la muestra | medir en el total antes de afirmar nada; si no aparecen, se reporta y el *fixture* los prueba igual |
| ~5% de nulos | muchos campos por encima: `wait_time_seconds` 28%, acento 28%, `amount_usd` 56% | separar **nulo estructural** (`amount_usd` vacío porque la moneda ya es USD: 100% en USD, 5% en ARS y COP) de **nulo faltante**; el contrato lo dice por columna |
| Llegadas tardías | ninguna fila con `process_date` distinto del día del archivo; ninguna partición anómala en tamaño | se simulan en el *fixture*; el mecanismo existe aunque la fuente no lo ejercite |
| Evolución de esquema | encabezados idénticos entre `data/` y el respaldo | igual: se prueba con el *fixture* |

**Un hallazgo que no anunciaron:** `process_date` no es la fecha del evento. En interacciones,
quejas y transacciones, los eventos entre las 00:00 y las 07:59 llevan el `process_date` del día
**anterior** (un tercio de las filas); en encuestas, `survey_date` llega hasta **dos días después**
de su `process_date`, es decir, se "procesó" antes de ocurrir. Regla: **`process_date` es metadato
de carga y llave de partición; toda métrica de negocio usa la fecha del evento.** Las marcas de tiempo
no traen zona horaria y los clientes están en tres husos distintos; plata guarda la hora tal cual y
declara el supuesto.

### 2.4 Integridad semántica: lo que las llaves foráneas no dicen

| Relación | Resultado | Lectura |
|---|---|---|
| `transactions.product_id` a `products` | 100% existe, mismo cliente, misma moneda | **coherente**: base confiable para disputas |
| `call_transcripts` a `call_center_interactions` | 100%; `has_transcript` cuadra exacto | coherente |
| `satisfaction_surveys.interaction_id` a interacciones | 100% | coherente |
| `complaints.origin_interaction_id` | **vacío en el 100%** | no se puede saber qué llamada originó una queja |
| `complaints.affected_product_id` | existe, pero **el dueño es otro cliente en el 100%** | el generador sorteó el producto; usarlo expondría datos ajenos |
| `complaints.claimed_amount` | **0 de 224** coincide con alguna transacción del cliente; la moneda coincide con la del producto solo el 29% | monto sin respaldo transaccional |
| `is_fraud` y quejas | 0 de 231 clientes con fraude tienen queja de "cargo no reconocido" | fraude y reclamos se generaron por separado |

Un chequeo de integridad referencial clásico **pasa** todas estas relaciones. Por eso la capa plata
necesita chequeos de **coherencia de dueño** (la fila hija y la madre tienen el mismo `customer_id`)
además de existencia. Es el tipo de chequeo que distingue a un equipo que entendió los datos.

### 2.5 Dónde hay señal para aprender

| Candidato | Resultado | Veredicto |
|---|---|---|
| Texto de transcripción a categoría | 2 frases de apertura distintas; 541 textos distintos en 11.903; V de Cramér 0,011 (p = 0,92) | **sin señal**; además `main_topics` es la etiqueta misma (fuga total) |
| `was_escalated` desde canal, motivo, sentimiento, duración, espera, segmento | AUC 0,51 (validación cruzada, gradient boosting) | **ruido**; no sirve ni como etiqueta ni como línea base de escalamiento |
| `was_resolved` | AUC 0,77, sobre todo por la categoría (Transaccional 91%, Queja 43%) | señal real pero de baja utilidad para el agente |
| `requires_followup` | AUC 0,68 | débil |
| `is_fraud` con `fraud_score` | prevalencia 0,10%; AUC 0,87 del puntaje existente | **señal real** y relevante para disputas |
| Demanda del motivo | "Cargo no reconocido" es **18%** de las quejas (866 de 4.790), toda en la categoría Transactions | respalda D-02 desde `complaints`, no desde interacciones |

## 3. La arquitectura por capas

La regla: **cada capa responde una pregunta distinta y tiene un consumidor distinto**. Se usan los
nombres de la arquitectura *medallion* porque el jurado los reconoce, con su traducción.

| Capa | También llamada | Pregunta que responde | Consumidor | Garantía | Formato |
|---|---|---|---|---|---|
| **Bronce** | cruda, *raw* | ¿qué llegó exactamente y cuándo? | el pipeline y la auditoría | inmutable, completa, trazable al archivo de origen | Parquet por `process_date`, todo como texto, más metadatos |
| **Plata** | curada, conformada | ¿qué es verdad sobre cada entidad? | analistas y la capa oro | tipada, deduplicada, dominios canónicos, PII tokenizada, filas malas en cuarentena | Parquet o DuckDB, modelos incrementales |
| **Oro** | consumo | ¿qué necesita cada uso, en la forma exacta en que lo necesita? | el EDA de negocio, el agente, el entrenamiento | contrato de consumo con frescura; mínima y estable | vistas y tablas en DuckDB |
| **Platino** | resultados, evidencia | ¿qué hizo el sistema y qué tan bien? | el jurado, el operador | cada cifra del reporte sale de aquí, con su linaje | tablas de resultados y reportes versionados |

### 3.1 Bronce: guardar sin opinar

- **Copia fiel** del CSV a Parquet, una partición por archivo de origen, **todas las columnas como
  texto**. No se corrige nada: si mañana cambia un tipo, bronce no se rompe y la diferencia se ve.
- **Metadatos por fila:** `_source_key` (ruta en S3), `_source_etag`, `_batch_id`, `_ingested_at`,
  `_row_hash` (huella del contenido), `_schema_hash` (huella del encabezado), `_dataset_generation`
  (`data` o `data_backup_20260831`).
- **Manifiesto de ingesta:** una fila por archivo con etag, tamaño, número de filas y encabezado.
  Si el etag no cambió, no se vuelve a ingerir (idempotencia barata).
- **Qué no hace bronce:** deduplicar, filtrar, tipar, unir. Tampoco se ingiere el archivo suelto de la
  raíz ni el respaldo como si fueran la misma fuente.
- **EDA de bronce:** la auditoría de la fuente, es decir, la sección 2 de este documento en forma de
  reporte reproducible: conteos contra el diccionario, dominios reales, nulos, duplicados, desfase de
  fechas, diferencias entre generaciones.

### 3.2 Plata: una verdad por entidad

Transformaciones, en este orden, cada una con su prueba:

1. **Tipado** según el contrato; lo que no convierte (fecha ilegible, número con texto) va a
   `_rechazos` con tabla, llave, columna, valor y regla violada. **Nunca se descarta en silencio.**
2. **Dominios canónicos** con tablas de mapeo versionadas: español e inglés, "México" y "Mexico",
   `Retención` como valor nuevo documentado. El valor crudo se conserva al lado.
3. **Deduplicación determinista:** por llave primaria, se queda la fila con mayor `last_updated` y,
   en empate, mayor `_ingested_at`. Las copias descartadas se cuentan y se reportan.
4. **Integridad y coherencia:** existencia de la llave foránea y **mismo dueño** entre hija y madre.
   Las filas que fallan no se borran: llevan una bandera (`_fk_ok`, `_owner_ok`) y el oro decide.
5. **Fechas:** `event_ts` desde la fecha del evento, `process_date` como metadato; supuesto de zona
   horaria declarado en el contrato.
6. **Moneda:** `amount_usd` recalculado con `daily_exchange_rates` por unión *as of* cuando falte y la
   moneda no sea USD; la anomalía de México en USD se marca, no se "arregla".
7. **Privacidad:** `document_number`, correo, teléfonos y dirección se reemplazan por un token
   determinista (HMAC con una llave fuera del repositorio). Los nombres van a una tabla aparte de
   acceso restringido. El resto de plata no tiene PII directa.
8. **Carga incremental:** `MERGE` por llave primaria sobre las particiones nuevas más una **ventana
   de corrección** (los últimos N días de `process_date`, N fijado con el retraso observado; si no
   hay retraso observado, N = 3 y se declara).

Tablas de plata que usa el flujo: `clientes`, `productos`, `transacciones`, `interacciones`, `quejas`,
`encuestas`, `agentes`, `tasas_cambio`. `digital_events`, campañas y envíos quedan en bronce salvo que
el flujo los necesite (P8).

**EDA de plata:** el **problema respaldado por datos** que pide el criterio 1: demanda por motivo,
país, canal y mes; FCR, espera y duración por categoría; peso de "cargo no reconocido" y su SLA;
estacionalidad. Se hace sobre plata y no sobre bronce porque ya no hay duplicados ni dominios mezclados.

### 3.3 Oro: tres familias con contratos distintos

| Familia | Tablas | Grano | Contrato clave |
|---|---|---|---|
| **Analítica** | `demanda_motivo_semana`, `kpi_contacto_categoria`, `quejas_subcategoria_sla` | agregados | definiciones de métricas fijas; sirven para la línea base de negocio |
| **Operacional para el agente** | `vista_cliente_segura`, `estado_productos`, `transacciones_recientes` (90 días), `candidatos_disputa` | por cliente | solo columnas que el flujo necesita, sin PII, siempre filtradas por el cliente de la sesión en el servicio; frescura con fecha de corte visible |
| **Aprendizaje** | `features_transaccion` con corte en el tiempo, `particiones_congeladas` | por transacción | cada característica calculada solo con datos anteriores al evento; particiones con huella |

Tres reglas de experto para oro:

- **El agente no lee plata ni escribe en oro.** Lee oro operacional a través de los servicios
  simulados, que aplican la autorización (P5). Lo que el agente crea (disputas radicadas, bloqueos)
  vive en la base de los servicios simulados, no en el *lakehouse*.
- **Oro operacional es estrecho a propósito:** si una columna no la usa ninguna herramienta, no
  existe. Eso es minimización de datos (P11) y además reduce lo que un ataque puede extraer.
- **Las características de aprendizaje respetan el tiempo:** nada calculado con información posterior
  a la transacción que se puntúa. Es la forma concreta de "prevenir fuga" que pide el enunciado.

**EDA de oro:** validez de etiquetas y características: señal contra azar, fuga por plantilla,
estabilidad en el tiempo, balance por país y segmento. La sección 2.5 es el primer borrador.

### 3.4 Platino: la evidencia

Platino no es "oro más limpio". Es donde aterriza **lo que produce el sistema y la evaluación**, y es
la capa que el jurado lee:

- `reporte_calidad_corrida`: por corrida y tabla, filas leídas, rechazadas por regla, duplicados
  quitados, huérfanos, frescura.
- `manifiesto_linaje`: entradas con etag, versión del código, versión de contratos y de dominios,
  salidas con conteo y huella.
- `resultados_evaluacion`: por caso del retenido, ruta esperada y observada, acciones, latencia,
  costo, idioma, segmento, versión de modelo y prompt.
- `trazas_resumen` y `traspasos`: exportación de las trazas y de los paquetes de traspaso.
- `metricas_reporte`: cada número del informe final, con la consulta que lo produce.

Regla: **ninguna cifra del reporte se escribe a mano**; sale de una consulta sobre platino.

## 4. Decisiones técnicas

| Decisión | Alternativa | Por qué |
|---|---|---|
| **DuckDB + Parquet** local | Spark, Databricks, un *warehouse* en la nube | 5,3 GB caben en memoria de portátil; reproducible sin credenciales de nube (P13, P9) |
| **dbt con el adaptador de DuckDB** para plata y oro | SQL suelto, SQLMesh | pruebas declarativas, modelos incrementales y **grafo de linaje gratis**, que el jurado reconoce |
| Bronce con un script de Python (boto3 o `aws s3 sync` + DuckDB `read_csv`) | dbt también en bronce | la ingesta es E y L, no T; lleva el manifiesto y los metadatos por fila |
| Contratos **ODCS 3.1** en YAML, uno por tabla de plata y uno por vista de oro operacional | solo pruebas de dbt | el contrato es el artefacto legible; de él se derivan las pruebas; incluye PII y frescura |
| Cuarentena en tabla (`_rechazos`) | descartar o fallar la corrida | ni se pierde información ni se detiene todo por una fila; severidad por regla |
| Formato de tabla | Delta, Iceberg, DuckLake | Parquet más manifiesto basta; DuckLake daría instantáneas y viaje en el tiempo si sobra tiempo, pero no es necesario para puntuar |

## 5. Actualizaciones: incremental, llegadas tardías, esquema y el *fixture*

### 5.0 Ruta operativa y ruta analítica

El enunciado pide elegir batch, incremental o *streaming* **según los insumos y las necesidades de
latencia y frescura del flujo**. Un cliente puede preguntar por un cargo de hace cinco minutos: eso
no lo resuelve ningún pipeline diario. Por eso hay dos rutas, y se declaran:

| Ruta | Qué sirve | En producción | En el prototipo |
|---|---|---|---|
| **Operativa** | lo que consultan las herramientas del agente: transacciones, estado de productos, casos | APIs del core en tiempo real (dominios BIAN) | servicios simulados que leen oro operacional con el reloj `AS_OF`; sesiones, estado de la conversación y casos en una base operativa (SQLite o Postgres), no en DuckDB, que admite un solo escritor |
| **Analítica** | EDA, métricas oficiales, características y evaluación | capas bronce a platino, **incremental diario**, porque la fuente entrega un archivo por día | lo mismo, con el *fixture* |

*Streaming* no se justifica: la fuente es un archivo diario y la necesidad de tiempo real está en la
ruta operativa, que en producción la cubre el core.

### 5.1 Reloj simulado

Los datos terminan el 17 de junio de 2026. Todo el sistema corre con un **reloj simulado** fijado en
esa fecha (`AS_OF`), nunca con la hora real. La frescura se mide contra ese reloj. Sin esto, todo
dato sería "viejo" y la política de frescura no se puede demostrar.

### 5.2 Política de frescura

| Tabla de oro | Cadencia supuesta en producción | Retraso tolerado | Si se excede |
|---|---|---|---|
| `transacciones_recientes` | diaria (en producción, casi en tiempo real) | 1 día | el agente dice "con corte al día X" y no afirma que un cargo **no** existe; ofrece seguimiento (escenario D3) |
| `estado_productos` | diaria | 1 día | no afirma estado de bloqueo sin consultar el servicio de tarjetas |
| `vista_cliente_segura` | mensual (instantánea) | 35 días | datos de contacto no se usan para verificar identidad |
| agregados analíticos | semanal | 7 días | se reportan con fecha de corte |

### 5.3 Dos generaciones en el bucket

`data/` y `data_backup_20260831/` no comparten IDs. Un pipeline ingenuo que las una duplicaría la
historia. El pipeline debe **detectar una regeneración de la fuente**: si en una partición ya cargada
cambia más de un umbral de las llaves (por ejemplo, 50%), no se hace `MERGE` sino que se **detiene y
alerta** para refresco completo. Es un caso real y medible: se ingiere el respaldo como si fuera
una entrega nueva y la prueba verifica que el pipeline se niega a mezclarlo.

**Vigilancia del bucket durante el evento.** El resumen del dataset dice que las particiones *pueden*
llegar tarde y los esquemas *pueden* cambiar, y el bucket ya cambió una vez (1 de septiembre). Un
trabajo programado lista el bucket, compara etags contra el manifiesto de bronce y, si aparece algo
nuevo, lo ingiere con la ruta incremental. Si hay entregas reales, se demuestran con datos reales y
el *fixture* queda como prueba adicional; si no, el *fixture* es la demostración, como pide el
enunciado.

### 5.4 El *fixture* de actualización

Un lote pequeño, en `tests/fixtures/actualizacion/`, marcado en su nombre y en sus filas como
**generado por el equipo para prueba**. Cada archivo tiene su resultado esperado:

| Archivo del *fixture* | Qué simula | Resultado esperado en plata |
|---|---|---|
| partición de un día ya cargado, reentregada con una fila corregida | llegada tardía dentro de la ventana | la fila queda con el valor nuevo; ninguna otra cambia |
| la misma fila con `last_updated` mayor en otra partición | duplicado | una sola fila, la más reciente; el conteo de duplicados sube en uno |
| partición fuera de la ventana de corrección | llegada muy tardía | no se aplica sola; queda registrada para reproceso manual |
| encabezado con una columna nueva al final | evolución aditiva | columna agregada con nulos hacia atrás; contrato en versión menor nueva |
| encabezado con una columna renombrada o faltante | evolución que rompe | partición en cuarentena completa; la corrida advierte y no corrompe plata |
| valor fuera de dominio y huérfano de llave foránea | datos malos | filas en `_rechazos` o con bandera, según la severidad de la regla |
| un producto de otro cliente en una queja | coherencia de dueño | bandera `_owner_ok = falso`; no llega al oro operacional |

Pruebas: (a) cada archivo produce su resultado esperado; (b) **correr la carga dos veces da la misma
huella** de cada tabla; (c) cargar en otro orden da el mismo resultado final.

## 6. Chequeos de calidad por capa

| Capa | Chequeo | Severidad |
|---|---|---|
| Bronce | archivo esperado presente por día; encabezado igual al del contrato; BOM detectado y manejado; conteo de filas dentro del rango histórico | advierte (bloquea si cambia el encabezado) |
| Plata | llave primaria única y no nula; tipos; dominios; nulos solo donde el contrato los permite, separando estructurales | bloquea la fila (cuarentena) |
| Plata | llave foránea existe; **mismo dueño** entre hija y madre; moneda coherente con el país y con el producto | bandera |
| Plata | fecha de evento dentro del rango del dataset; desfase con `process_date` dentro de lo observado | advierte |
| Oro | frescura contra `AS_OF`; sin PII directa (prueba que busca patrones de documento, correo, teléfono); cada fila operacional con `_owner_ok` verdadero | bloquea la publicación |
| Oro de aprendizaje | ninguna característica con fecha posterior al evento; particiones disjuntas por cliente y por tiempo | bloquea |

## 7. Linaje y reproducibilidad

- **Manifiesto por corrida** en platino: etags de entrada, commit del código, versiones de contratos
  y dominios, conteos por capa, rechazos por regla, huella de cada tabla de salida.
- **Grafo de dbt** para el linaje de tabla a tabla; los contratos marcan las columnas PII, así que
  se puede mostrar a qué tablas llega un dato personal (y que a oro operacional no llega ninguno).
- OpenLineage con Marquez solo si sobra tiempo: el manifiesto y el grafo ya cubren lo que pide el
  enunciado.
- `just data` reconstruye bronce, plata y oro desde S3; `just data-test` corre el *fixture*.

## 8. Privacidad y retención por capa

| Capa | PII | Acceso | Retención propuesta en producción |
|---|---|---|---|
| Bronce | completa | solo el pipeline | corta (por ejemplo, 30 días) y cifrada; es la capa de mayor riesgo |
| Plata | tokenizada; nombres en tabla aparte | analistas con rol | la del regulador para la entidad |
| Oro operacional | ninguna directa | solo servicios, filtrado por sesión | igual que plata |
| Platino | ninguna; las trazas se redactan antes de guardarse | equipo y auditoría | la de auditoría |
| Audio de voz | la voz es dato personal (y biométrico si identificara) | nadie por defecto: se transcribe en streaming y no se guarda el audio crudo | cero en operación; las grabaciones de evaluación, con consentimiento y borrado al cierre |

El dataset es sintético, pero el diseño se defiende como si no lo fuera: el enunciado pide explicar
retención y controles de acceso.

## 9. Qué cambia en el resto del diseño

1. **D-02 (flujo de disputas) se respalda con quejas, no con interacciones.** `contact_reason` no
   distingue "cargo no reconocido"; `complaints.subcategory` sí, con un 18%. La evidencia del
   criterio 1 se construye con esa tabla, más el SLA incumplido de esa subcategoría.
2. **El caso de disputa se ancla en transacciones y productos**, que son coherentes, y nunca en el
   `affected_product_id` ni en el `claimed_amount` de las quejas.
3. **El componente aprendido cambia de candidato** (y cambió otra vez: la segunda pasada de la
   auditoría mostró que `is_fraud` no tiene señal fuera de `fraud_score`; ver D-14 y
   [05](05_Cobertura_del_enunciado.md)). El clasificador de intención sobre
   transcripciones no tiene señal; entrenarlo daría un número sin sentido. Dos caminos honestos:
   - **Principal: puntaje de riesgo de la transacción disputada** (para decidir entre R3, R4 y R5),
     con `fraud_score` como **línea base**, características de oro con corte temporal, partición por
     tiempo, métricas para clase rara (PR AUC, sensibilidad a tasa de falsos positivos fija) y
     calibración. Hay señal comprobada y encaja en el flujo.
   - **Secundario: clasificador de intención** entrenado y evaluado sobre conversaciones **escritas
     o generadas por el equipo**, etiquetadas como tales, con TF-IDF como línea base y la prueba
     de español a portugués. Se reporta explícitamente que el dataset no permitía hacerlo con datos
     del organizador.
4. **Casos de evaluación que salen de los datos:** el producto de otro cliente en una queja (S y D),
   México en USD (D4, moneda inconsistente), transacciones en Brasil como puerta natural al escenario
   en portugués, y la regeneración del bucket como falla del pipeline.
5. **El plan F1 queda parcialmente adelantado:** la auditoría sintética y de calidad de la muestra ya
   está; falta confirmarla sobre el total y convertirla en el reporte reproducible de bronce.

## 10. Preguntas que haría el jurado, y la respuesta que hay que tener

| Pregunta | Respuesta que debe existir |
|---|---|
| ¿Por qué cuatro capas y no dos? | cada capa tiene consumidor y contrato distinto (tabla de la sección 3); platino es evidencia, no datos más limpios |
| ¿Cómo sé que no perdieron filas? | conteos de entrada, salida, rechazos y duplicados por corrida cuadran en el manifiesto |
| ¿Qué pasa si llega el día de ayer otra vez? | ventana de corrección y `MERGE` idempotente; el *fixture* lo prueba |
| ¿Qué pasa si cambian el esquema? | aditivo se absorbe con versión menor; lo que rompe va a cuarentena; ambos en el *fixture* |
| ¿Cómo evitan que el modelo vea datos de otro cliente? | oro operacional sin PII, filtrado por la sesión en el servicio, chequeo de mismo dueño en plata |
| ¿Su componente aprendido aprende algo real? | auditoría de señal (sección 2.5) antes de entrenar; línea base existente; partición temporal |
| ¿Qué tan fresco es el dato que dice el agente? | reloj simulado, política por tabla, fecha de corte en la respuesta |
| ¿Qué es sintético y qué hizo el equipo? | columna de origen en cada tabla y en cada caso de evaluación |

## 11. Siguientes pasos

1. Crear el repositorio (D-03) con el esqueleto de `pipeline/`, `contracts/`, `dominios/` y
   `tests/fixtures/`.
2. Bronce completo de `data/` con manifiesto; el respaldo, en una generación aparte.
3. Reporte de auditoría de bronce sobre el total: confirma o corrige cada cifra de la sección 2.
4. Contratos ODCS de las ocho tablas de plata, empezando por `transacciones`, `productos`,
   `clientes` y `quejas`.
5. Plata incremental con cuarentena y el *fixture*; prueba de idempotencia.
6. EDA de negocio sobre plata para cerrar D-02.
7. Oro operacional y de aprendizaje; auditoría de señal del puntaje de riesgo antes de entrenar.
