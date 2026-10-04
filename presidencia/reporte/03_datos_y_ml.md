# Criterio 4: datos y aprendizaje automático

**Cara:** Presidencia con Datos e IA. **Fecha:** 4 de octubre de 2026. Volver al [reporte final](00_reporte_final.md). Todo el dataset es sintético; las cifras describen este conjunto y no a un banco real.

## 1. Ingeniería de datos

### 1.1 Capas

Dataset `latam_bank` en BigQuery (proyecto `latam-bank-hackaton-2026`), con la capa como prefijo de tabla, según [datos/README](../../datos/README.md) y [ESTADO](../ESTADO.md):

| Capa | Tablas | Contenido |
|---|---|---|
| `bronce_` | 13 | crudo, todo texto; cuadra con los CSV del organizador |
| `plata_` | 14 | tipado (`SAFE_CAST`), deduplicado por llave, PII seudonimizada, país ISO |
| `oro_` | 8 | siete tablas o vistas operacionales para el agente, sin PII, y una línea base de reclamos |
| `platino_` | 8 | manifiesto, calidad, conversiones fallidas, huérfanos, respaldo, inventario |

7,2 GB lógicos en 45 objetos. La carga del bucket al bronce queda fuera de alcance por D-30 (proceso externo); el trabajo empieza en `bronce_<archivo>`.

### 1.2 Contratos

Ocho contratos ODCS en [datos/contratos/](../../datos/contratos/), uno por tabla de oro operacional. Una prueba compara las columnas vivas con el contrato (control del 30 sep: sin deriva, [ESTADO](../ESTADO.md)). El contrato de bronce (tablas, llaves, columnas requeridas, partición) está en `src/latam_datos/contrato.py` y se resume en [datos/README](../../datos/README.md). Los dominios canónicos (12) viven en `datos/dominios/dominios_canonicos.csv` y una prueba genérica `dominio_canonico` vigila cada columna de oro.

### 1.3 Reglas de calidad

Reglas Q-BRZ sobre bronce (`just validar`, resultado en `platino_reporte_calidad_corrida`): días sin filas (01), tabla y columnas requeridas (03), llave vacía o fecha ilegible (05), volumen diario atípico por mediana y MAD (06), tabla vacía (11), llaves repetidas (12), vacíos sobre 0,5% (13), duplicados de fila (14) y huérfanos (15). Seis reglas de la definición original se descartaron porque hablaban de archivos y lotes que ya no se ven. dbt corre 56 pruebas en verde (llaves, relaciones, dominios, fixture). Control del 30 sep: 5 avisos y 0 bloqueantes ([ESTADO](../ESTADO.md)).

Hallazgos reales que condicionan el diseño ([LIMITACIONES](../../datos/LIMITACIONES.md)):

| Hallazgo | Magnitud | Tratamiento |
|---|---|---|
| `transactions.amount_usd` vacío | 2.537.456 de 4.425.008 (57,3%); 2.437.979 son USD nativos y 99.477 locales | plata recalcula con la tasa del día y marca `amount_usd_origen`; la recomputación difiere 1,0% en promedio |
| `digital_events.customer_id` vacío | 3.745.446 de 15.620.994 (24,0%) | se conserva nulo; se atribuye por sesión |
| `complaints.affected_product_id` vacío | 22.525 de 67.095 (33,6%) | nulo permitido, sin imputar |
| `origin_interaction_id` de quejas | vacío en 100% ([01_problema](01_problema.md) sección 5) | el cargo lo identifica el cliente, no se precarga |
| `campaign_sends` sin los 14 primeros días | 2023-06-17 a 2023-06-30 | ausencia estructural, declarada |
| Respaldo del organizador incompleto | `transactions` llega a 2024-09-25 (453 de 1.097 archivos) | no se carga; se compara y se reporta |

### 1.4 Linaje y manifiesto

`just manifiesto` escribe un registro por archivo (ruta, bytes, sha256, filas, tabla destino) y una huella por tabla encadenada `sha256(huella previa + registro)`. `just verificar-cadena` recomputa la cadena y sale con 1 si se editó un manifiesto viejo: cadena íntegra con 13 registros y 13 de 13 tablas con filas coincidentes ([datos/README](../../datos/README.md); [ESTADO](../ESTADO.md)). El cargador escribe a `bronce_<t>_nuevo`, compara conteos con los CSV y solo entonces reemplaza la tabla. El grafo de dbt da el linaje entre capas (D-21). Cada cifra del [01_problema](01_problema.md) se regenera con `uv run python -m latam_datos.analisis` y se guarda en `figuras/cifras.json`.

### 1.5 Frescura y actualización

[POLITICA_ACTUALIZACION](../../datos/POLITICA_ACTUALIZACION.md): `AS_OF` es el mayor `process_date` de las tablas de hechos (hoy 2026-06-17) y se calcula, no se escribe. Una llegada con `process_date` hasta 3 días antes de `AS_OF` se aplica en la corrida siguiente; fuera de esa ventana se retiene para revisión manual. Una regeneración del organizador se detecta con `comparar-respaldo` y no se mezcla. El modo es por lotes porque la entrega es por archivo y día; no se justifica transmisión.

**Prueba de actualización.** El dataset es estático, así que la corrección se demuestra con un **fixture del equipo** claramente rotulado: `datos/fixtures/refresco.yml` con 10 casos FX-01 a FX-10 (duplicado, reentrega, llegada tardía, fallo de conversión, moneda inválida, huérfano, dueño ajeno, `amount_usd` recalculado, país, seudónimos) como pruebas unitarias de dbt (`just dbt-test-fixture`).

### 1.6 Privacidad en datos

La llave de seudonimización vive en `latam_seguridad.llave` (generada en BigQuery, fuera del repositorio). Documento, correo, teléfono y número de producto llegan a plata como `SHA-256(secreto || valor)`; nombres, dirección, fecha de nacimiento y texto libre no pasan. Género, estado civil, educación y banda de edad quedan en `plata_restringida_clientes`, solo para auditar equidad con celdas de 20 casos o más ([05_equidad](05_equidad.md) sección 1). La separación es por construcción: el IAM es de proyecto y el destino de producción son etiquetas de política y vistas autorizadas ([06_produccion](06_produccion.md)).

## 2. Clasificador del motivo de contacto

Reporte: [clasificador_2026-10-03](../../ia/evaluacion/reportes/clasificador_2026-10-03.md); ficha: [modelcard_motivo](../../ia/evaluacion/reportes/modelcard_motivo_2026-10-03.md). Datos: 686.296 contactos en español, 2023-06-17 a 2026-06-17.

| Aspecto | Decisión |
|---|---|
| Etiqueta | `contact_reason`, seis clases (Transaccional 35,0%, Producto 22,0%, Queja 17,0%, Técnico 15,0%, Comercial 8,0%, Retención 3,0%); no hay texto del cliente en los datos, así que TF-IDF y un clasificador Gemini no aplican (0 de 300 llamadas gastadas) |
| Calidad de la etiqueta | rúbrica determinista de coherencia interna: 43 de 50 consistentes (82,9% en 20.000 casos); es lo esperable por construcción y no demuestra ausencia de ruido, porque no hay una segunda fuente independiente |
| Partición | temporal: entrenamiento antes de 2025-07-01 (465.008), validación hasta 2025-12-31 (115.803), prueba desde 2026-01-01 (105.485); la calibración y el umbral usan solo validación y la prueba se evalúa una vez |
| Fuga evitada | fuera `reason_category` y `main_topics` (copias de la etiqueta), `detected_sentiment`, `has_transcript`, `has_recording`, `agent_id` e identificadores; prueba de sensibilidad en clientes nunca vistos: macro-F1 0,404 en 4.796 contactos contra 0,399 general |
| Representación | numéricas imputadas por mediana con indicador de faltante y estandarizadas; categóricas en one-hot; árboles de gradiente (profundidad 4, 150 iteraciones) y regresión logística como control |
| Líneas base | mayoritaria; B1, tabla de decisión escrita con estadísticas de entrenamiento antes de ver validación o prueba |
| Métrica y por qué | macro-F1, por el desbalance y porque Retención pesa igual que las comunes; IC por bootstrap de clientes (1000 réplicas, semilla 202616737) |
| Abstención | umbral 0,81 elegido en validación con costo de error 5 y de revisión 1 |

Resultados en prueba (IC 95%):

| Sistema | Macro-F1 | Exactitud |
|---|---|---|
| Mayoritaria | 0,086 [0,086; 0,087] | 0,349 |
| B1 reglas | 0,343 [0,340; 0,346] | 0,446 |
| Aprendido con rasgos al abrir el contacto | 0,086 [0,086; 0,087] | 0,349 |
| Aprendido con señales del cierre de la llamada | **0,399** [0,396; 0,402] | 0,555 |

Diferencia con B1: [0,053; 0,059]. A p ≥ 0,81 automatiza 13,1% de los casos con exactitud 85,0%; costo medio 0,967 contra 1,000 de revisar todo y 2,226 de automatizar todo.

**Lectura.** (1) La ganancia sobre las reglas es estadísticamente clara pero modesta, y viene de señales conocidas solo al cierre (duración, sentimiento, resuelto, seguimiento): sirve para sugerir el código de cierre, **no para enrutar antes de atender**, porque con lo que se sabe al abrir el modelo no supera a la mayoritaria. (2) Retención nunca se predice (F1 0,000). (3) Los datos fueron generados desde la etiqueta, así que se mide qué tan bien se recupera esa estructura. (4) No hay portugués ni transcripciones: no se midió transferencia de idioma. (5) La pista nunca actúa (`accion_permitida` siempre falso). El valor operativo es marginal con costo 5 a 1, y se reporta así.

**Candidato descartado, fraude.** `fraud_score` está contaminado por la etiqueta (2.373 de 2.373 transacciones con puntaje mayor a 30 son fraude) y la tasa de fraude por canal solo varía de 0,0948% a 0,1079%; cualquier modelo reproduciría la fuga (clasificador, sección 9). Por eso `fraud_score` queda como regla de política y fuera de los datos del agente.

## 3. Riesgo de incumplir el plazo: resultado negativo

Reporte: [riesgo_plazo_2026-10-04](../../ia/evaluacion/reportes/riesgo_plazo_2026-10-04.md); ficha: [modelcard_riesgo_plazo](../../ia/evaluacion/reportes/modelcard_riesgo_plazo_2026-10-04.md). Pregunta: al radicar una disputa, ¿se puede anticipar que incumplirá el SLA o será escalada? Datos: 67.095 quejas.

- **Auditoría de la etiqueta.** `sla_breached` no responde a lo que debería medir: la primera respuesta tarda 38,0 h en incumplidos y 37,0 h en cumplidos (AUC 0,502), no se relaciona con `resolution_days` (AUC 0,491) y 19,6% de los 20.125 casos aún abiertos ya figuran incumplidos (20,1% en total). `Escalated` es un estado final censurado por la derecha: 100% de las escaladas no tiene primera respuesta.
- **Fuga evitada.** Solo rasgos conocidos al radicar (categoría, canal, país, producto, antigüedad, quejas previas estrictamente anteriores, transacciones de los 30 días previos); fuera estado, fechas posteriores, `priority` e `is_repeat_complainer`.
- **Partición temporal.** Entrenamiento hasta 2025-02-28 (38.125), validación hasta 2025-09-30 (12.905), prueba desde 2025-10-01 (16.065).
- **Resultado.** SLA incumplido, prevalencia 20,2%: AUC-PR de los árboles calibrados 0,205 [0,196; 0,215] contra 0,201 de la mayoritaria y 0,205 de la regla por subcategoría; AUC 0,504 [0,492; 0,514]. Escalada, prevalencia 5,1%: AUC-PR 0,050 [0,046; 0,055] contra 0,049; AUC 0,506. Con la etiqueta permutada el modelo rinde igual (0,205 y 0,050). Priorizar el 20% de mayor riesgo captura 20,4% de los incumplimientos, igual que el azar.
- **Decisión.** "No hay señal verificable más allá de las líneas base." La pista se entrega como infraestructura que **se abstiene siempre**; no se afirma ninguna ganancia. El resultado dice que este experimento no sostiene una mejora, no que no exista señal en un banco real.

## 4. Fugas y particiones: resumen

| Componente | Partición | Fuga considerada | Dónde |
|---|---|---|---|
| Motivo | temporal 2025-07-01 y 2026-01-01 | etiqueta copiada, derivados posteriores, identidad del agente | clasificador, secciones 2 y 3 |
| Riesgo de plazo | temporal 2025-03-01 y 2025-10-01 | estado y fechas posteriores, `priority`, repetidor | riesgo, secciones 2 y 3 |
| Evaluación del agente | desarrollo (31 escenarios) y retenido (32 casos nuevos, SHA-256 `f8bcb432…ccd91`) | ningún primer mensaje repetido, etiquetas de la política y no del comportamiento observado | [04_evaluacion](04_evaluacion.md) sección 3 |
| Agente | `fraud_score` e `is_fraud` fuera de las vistas de oro de transacciones | puntaje contaminado por la etiqueta | [datos/README](../../datos/README.md) |

El retenido de la evaluación está gastado: iterar el prompt con él exigiría uno nuevo ([04_evaluacion](04_evaluacion.md) sección 3).
