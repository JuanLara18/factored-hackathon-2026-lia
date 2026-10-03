# Limitaciones de los datos crudos

Hallazgos reales de la corrida de `python -m latam_datos validar` sobre `latam_bank.bronce_*` (BigQuery, proyecto latam-bank-hackaton-2026). Las cifras salen de consultas directas al dataset. Todos son avisos: bronce conserva los datos tal como llegaron y plata decide cómo tratarlos.

## Resumen

| Regla | Tabla | Hallazgo | Magnitud |
|---|---|---|---|
| Q-BRZ-13 | transactions | `amount_usd` vacío | 2.537.456 de 4.425.008 (57,3%) |
| Q-BRZ-13 | digital_events | `customer_id` vacío | 3.745.446 de 15.620.994 (24,0%) |
| Q-BRZ-13 | complaints | `affected_product_id` vacío | 22.525 de 67.095 (33,6%) |
| Q-BRZ-01 | campaign_sends | faltan los primeros 14 días de la ventana | 2023-06-17 a 2023-06-30 |
| Q-BRZ-06 | digital_events | 7 días con volumen atípico | picos de 2,4x la mediana |

Las reglas de duplicados de fila completa (Q-BRZ-14, sobre las tablas sin llave declarada) y de huérfanos (Q-BRZ-15, nueve relaciones entre tablas) corrieron sin hallazgos. `is_fraud` no tiene vacíos sobre el umbral (4.316 verdaderos, 0,10%).

## transactions.amount_usd vacío (57,3%)

No es un fallo aleatorio, tiene dos causas distintas:

1. Todas las filas en USD lo traen vacío: 2.437.979 de 2.437.979 (100%). Para una moneda nativa USD el monto en dólares es el propio `amount`, así que el campo no se llenó por redundante. En las filas no vacías nunca hay USD.
2. Las filas en moneda local lo traen vacío en cerca de 5%: COP 59.436 de 1.194.444 (4,98%) y ARS 40.041 de 792.585 (5,05%). Este sí es un faltante real.

El resultado es que los 2.537.456 vacíos son 2.437.979 USD nativos más 99.477 en COP o ARS.

Recomendación para plata: no confiar en `amount_usd` crudo. Definir `amount_usd_plata` así: `amount` cuando la moneda es USD, el valor crudo cuando existe y, si falta, `amount * exchange_rate` con la tasa `source_currency = currency, target_currency = USD` de `daily_exchange_rates` en la fecha de `process_date`. Esa tasa existe para los 1.097 días de la ventana y todas las parejas de monedas, y los 99.477 vacíos en moneda local tienen tasa (0 sin cruce). Contra las 1.887.552 filas locales que sí traen el valor, la recomputación con esa tasa difiere 1,0% en promedio y 2,1% como máximo, así que sirve para análisis agregado pero no reproduce el valor al centavo. Conviene marcar con una bandera cuáles filas se recomputaron. `daily_exchange_rates` no trae MXN en las transacciones: las monedas presentes son USD, COP y ARS.

## digital_events.customer_id vacío (24,0%)

3.745.446 eventos sin cliente. La proporción es casi idéntica en todos los tipos de evento (PageView 24,0%, Click 24,0%, Login 24,0%, Purchase 24,1%), y todos esos eventos traen `session_id`. Lectura probable: sesiones anónimas, no un defecto por tipo. Consecuencia: los análisis por cliente pierden una cuarta parte del tráfico digital, y ni siquiera `Login` (que en teoría identifica al cliente) se salva. Plata debe conservar estas filas con `customer_id` nulo, atribuirlas por `session_id` cuando otra fila de la sesión sí tenga cliente, y no descartarlas del conteo de tráfico.

## complaints.affected_product_id vacío (33,6%)

22.525 de 67.095 reclamos. Tampoco depende del tipo de caso: Complaint 33,8%, Claim 33,3%, Request 33,0%, Suggestion 33,2%. Lo esperable es que Request y Suggestion no toquen un producto, pero Complaint y Claim tampoco lo traen en un tercio de los casos, así que no se puede leer como "no aplica". Sin producto no hay cruce con `products` ni con `transactions`. Plata debe permitir el nulo y no imputarlo. Cuando exista `origin_interaction_id` se puede intentar inferir por la interacción, pero eso es una decisión de plata, no de bronce.

## campaign_sends sin los primeros 14 días

La ventana del dataset es 2023-06-17 a 2026-06-17 (1.097 días), pero `campaign_sends` empieza el 2023-07-01. Faltan exactamente 14 días (2023-06-17 a 2023-06-30). Coincide con `marketing_campaigns.start_date`, cuyo mínimo también es 2023-07-01: no hay campañas antes de esa fecha, por lo que es una ausencia estructural y no una pérdida de carga. Las métricas de marketing solo son comparables desde el 2023-07-01. Además `marketing_campaigns.end_date` llega a 2026-08-20, posterior al fin de la ventana.

## digital_events con días atípicos (Q-BRZ-06)

La regla anterior (percentiles 1 y 99) marcaba unos 110 días de ruido por construcción. La actual usa mediana y MAD por día de la semana (z modificado mayor que 3,5 y desvío mayor que 30%, o caída mayor que 60%). Para `transactions`, `call_center_interactions` y `campaign_sends` no marca ningún día. Para `digital_events` marca 7 días, todos picos: 2023-07-09 y 2023-07-16 (21.556 y 21.557 eventos contra una mediana de 8.791 los domingos), 2026-03-15 y 2024-04-14 (alrededor de 21.000), entre otros. Esta tabla es inherentemente volátil (de 5.400 a 31.000 eventos por día), así que conviene verlos como picos de tráfico y no como pérdida de datos. No hay caídas.

## Sin hallazgos

Las tablas sin llave declarada (`satisfaction_surveys`, `call_transcripts`, `digital_events` y otras) no tienen filas idénticas repetidas. Las nueve relaciones revisadas no tienen huérfanos entre los valores no vacíos: transactions hacia customers y products; products, complaints e interacciones hacia customers; complaints hacia products e interacciones; transcripts y surveys hacia interacciones.

## Cobertura de idioma: español y portugués

El enunciado pide demostrar interacciones en español y en portugués y reportar los límites de los datos y del idioma. Estado al 3 de octubre de 2026:

| Qué | Cobertura | Límite |
|---|---|---|
| Datos de clientes | cuentas de México, Colombia y Argentina; los clientes de la demostración son de esos tres países | no hay cuentas, transacciones ni reclamos de Brasil |
| Idioma de los datos | la definición de Clientes (sección 2.3.3) anota `detected_language = es` en todas las filas de interacciones | no hay conversaciones reales en portugués para entrenar, calibrar ni medir; no se volvió a consultar en esta entrega |
| Plantillas | `clientes/plantillas/es.yaml` (usted y vos) y `clientes/plantillas/pt.yaml` (você, pt-BR), 41 plantillas cada una, mismos ids y marcadores, con retrotraducción al español y linter propio | sin revisor nativo (S-CLI-14): la retrotraducción la hizo el mismo equipo que escribió el texto |
| Agente | prompt `disputas/agente@1.3.0` con variante `pt voce` y guarda de idioma: responde en el idioma del último mensaje, con cambio de idioma y mezcla | 9 escenarios en portugués en el arnés, k=1 en casi todos (reporte `ia/evaluacion/reportes/geap_pt_2026-10-03.md`); sirven para ver que el camino funciona, no para estimar tasas |
| Banca, asistente y chat | selector "Español, usted", "Español, vos" y "Português, você" que viaja como `registro` (`usted`, `vos`, `voce`) por sesión, textos, aprobaciones y paquete de traspaso (`idioma = pt`) | las páginas públicas de marketing siguen en español, con una nota; las fichas de transacción llevan el comercio y los estados tal como los trae la base |
| Montos y fechas | siguen el formato del país de la cuenta (por ejemplo `1.234,56 COP`), no el de Brasil | un cliente en portugués ve montos en pesos colombianos, mexicanos o argentinos, sin conversión a reales |
| Normas | se nombra la del país de la cuenta; Pix, MED, Procon y Banco Central do Brasil están en las frases prohibidas de plantilla y el prompt dice que no aplican | ningún escenario con verificador propio mide que el agente no las presente como aplicables |
| Cola humana | el traspaso en portugués lleva `idioma = pt` y cola destino `pt` | la definición de Clientes cuenta 7 especialistas de fraude con portugués y 1 con turno de noche; la demostración tiene una sola cola de operador |

El modo en portugués se rotula en la interfaz como "atendimento em português para clientes da região": es atención en ese idioma para clientes de México, Colombia y Argentina, no un servicio para cuentas brasileñas. Quien lo evalúe debe leerlo así. Ningún dato sintético de Brasil se agregó para disimular el límite.

Lo que falta para cerrar esta brecha de verdad: un revisor nativo de las 41 plantillas, conversaciones reales (o una semilla humana) en portugués, y una medición de equidad por idioma con tamaño de grupo, como pide R-DAT-50.
