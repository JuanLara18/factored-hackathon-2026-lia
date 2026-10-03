# Clasificador del motivo de contacto, reporte 2026-10-03

Criterio 4 del enunciado: evaluar un componente aprendido frente a una línea base, con etiquetas válidas, sin fuga y con métricas, umbrales y particiones justificados. Reproducible con `uv run python -m latam_ia.experimentos.motivo`. Datos: `latam_bank.plata_call_center_interactions` (686.296 contactos, 2023-06-17 a 2026-06-17), solo español, sin PII en este reporte.

## Resumen

- Con las señales del cierre de la llamada, el modelo (árboles de gradiente, calibrado) logra macro-F1 **0.399** [0.396, 0.402] contra 0.343 [0.340, 0.346] de las reglas B1 y 0.086 de la clase mayoritaria (Transaccional). Diferencia con B1 [0.053, 0.059].
- Con solo lo que se sabe al abrir el contacto (tipo, canal, segmento, país, hora, antigüedad) el modelo **no supera a la mayoritaria**: macro-F1 0.086 [0.086, 0.087]. Por eso el motivo no sirve para enrutar antes de atender; sirve para sugerir el código de cierre.
- A umbral 0.81 (elegido en validación con costo de error 5 y revisión 1) el modelo automatiza 13.1% de los casos con exactitud 85.0%; costo medio 0.967 contra 1.000 de revisar todo y 2.226 de automatizar todo: con costo 5 a 1 el ahorro es marginal, así que el valor está en la pista cuando el error es caro, no en automatizar.
- Texto: no existe texto del cliente en los datos (ver auditoría), así que TF-IDF y el clasificador Gemini no son aplicables; se gastaron 0 de 300 llamadas al modelo. Fraude: se descartó con evidencia (sección final).

## 1. Elección del componente y por qué no es texto

El enunciado pide etiquetas válidas. Se inspeccionaron las tablas de plata antes de elegir:

- Quejas (`plata_complaints`) y transcripciones (`plata_call_transcripts`) no traen texto libre. Los únicos campos de texto en ellas son `audio_quality`, `case_type`, `category`, `currency`, `detected_accent`, `detected_intents`, `detected_keywords`, `detected_language`, `main_topics`, `priority`, `reception_channel`, `status`, `subcategory`, `transcription_model`, todos categóricos. `detected_keywords` solo contiene las fichas `banco`, `cuenta`, `nan`, `servicio` sin relación con el motivo.
- `main_topics` de la transcripción coincide con el motivo en 171,321 de 171,321 contactos (100%): es una copia de la etiqueta y no se usa como rasgo.
- Se eligió el motivo de contacto (`contact_reason`, seis clases; `reason_category` es idéntica) porque es la etiqueta registrada con más volumen y la que la comprensión del agente necesita. Las señales estructuradas son lo único disponible; no se inventó texto.

## 2. Auditoría de etiquetas

Balance en entrenamiento: Comercial 8.0%, Producto 22.0%, Queja 17.0%, Retención 3.0%, Transaccional 35.0%, Técnico 15.0%. Se usa macro-F1 por el desbalance y porque las clases raras (Retención) cuestan igual que las comunes.

Muestra de 50 casos (8 por clase, semilla fija) revisada con una rúbrica determinista: el contacto es consistente si su duración y su sentimiento caen en el rango P5 a P95 de su propia clase y, para Transaccional, el sentimiento detectado es Neutral. Resultado: **43 de 50** consistentes (82.9% en 20.000 casos). La rúbrica mide coherencia interna, no verdad externa: por construcción un contacto limpio pasa con probabilidad cercana a 0,9 por cada rango, así que ~83% es lo esperado y no evidencia de ruido; no hay segunda fuente independiente del motivo en los datos. Como señal complementaria, 0.00% de la prueba recibe p ≥ 0,9 en otra clase (el modelo casi nunca llega a esa confianza, así que esta señal tampoco detecta ruido).

Campos con fuga que se excluyen: `reason_category` y `main_topics` (copias de la etiqueta), `detected_sentiment` (derivado de `sentiment_score`), `has_transcript` y `has_recording` (posteriores), `agent_id` (identidad del agente) e identificadores de producto. Faltante de `duration_seconds`: 14.0%, estructural (chat, correo y video sin duración): Chat 100%, Email 100%, Inbound Call 0%, Outbound Call 0%, Video 0%. Se imputa con la mediana más un indicador de faltante.

## 3. Partición y fuga

| Parte | Rango de `process_date` | Contactos |
|---|---|---|
| Entrenamiento | 2023-06-17 a 2025-06-30 (< 2025-07-01) | 465,008 |
| Validación | 2025-07-01 a 2025-12-31 | 115,803 |
| Prueba | 2026-01-01 a 2026-06-17 (≥ 2026-01-01) | 105,485 |

Partición temporal porque el modelo se usará sobre contactos futuros; el cálculo de calibración y umbral usa solo validación y la prueba se evalúa una vez. No hay identificador de cliente ni de agente entre los rasgos, de modo que no hay memorización de personas. 95.4% de los clientes de prueba ya aparecen en entrenamiento; como prueba de sensibilidad, en los 4,796 contactos de clientes nunca vistos el macro-F1 es 0.404 (general 0.399). Los IC son bootstrap por cliente (pesos Poisson, 1000 réplicas, semilla 202616737) porque los contactos de un cliente están correlacionados.

## 4. Modelos, representaciones y líneas base

- **Mayoritaria**: siempre predice Transaccional.
- **B1 reglas**: tabla de decisión fija sobre duración (bandas por medianas de entrenamiento) y cierre (sin resolver y con seguimiento, duración mayor a 310 s, es Queja); sin duración cae en la mayoritaria. Escrita con estadísticas de entrenamiento, antes de ver validación o prueba.
- **Aprendidos**: regresión logística multinomial y árboles de gradiente (HistGradientBoosting, profundidad 4, 150 iteraciones). Representación: numéricas con imputación por mediana, indicador de faltante y estandarización; categóricas en one-hot (categorías con menos de 50 casos se agrupan). Se justifican porque los rasgos son tabulares y de baja dimensión; el árbol captura el corte por bandas y el modelo lineal sirve de control de que la ganancia no es solo capacidad.
- **Dos conjuntos de rasgos**: `contacto` (disponibles al abrir) y `llamada` (añade duración, sentimiento, resuelto, seguimiento, escalado, conocidos al cerrar).
- **Calibración**: escalado de temperatura ajustado en validación. Temperatura 1.00 (el modelo ya salía calibrado); ECE 0.0068 a 0.0068 y Brier 0.5718 a 0.5718 en prueba.
- **Selección**: macro-F1 en validación. contacto/logistica 0.086; contacto/arboles 0.086; llamada/logistica 0.317; llamada/arboles 0.397. Campeón de `llamada`: árboles de gradiente.

## 5. Resultados en prueba

| Sistema | Macro-F1 | IC 95% | Exactitud | IC 95% |
|---|---|---|---|---|
| Mayoritaria | 0.086 | [0.086, 0.087] | 0.349 | [0.346, 0.352] |
| B1 reglas | 0.343 | [0.340, 0.346] | 0.446 | [0.443, 0.449] |
| Aprendido, conjunto `contacto` (regresión logística) | 0.086 | [0.086, 0.087] | 0.349 | [0.346, 0.352] |
| **Aprendido, conjunto `llamada` (árboles de gradiente)** | **0.399** | [0.396, 0.402] | 0.555 | [0.552, 0.558] |

Diferencias de macro-F1 con IC: campeón menos B1 [0.053, 0.059]; campeón menos mayoritaria [0.310, 0.315]; `contacto` menos mayoritaria [0.000, 0.000].

**Por clase, campeón (`llamada`, sin abstención)**

| Motivo | Precisión | Cobertura (recall) | F1 | Casos |
|---|---|---|---|---|
| Comercial | 0.500 | 0.309 | 0.382 | 8,440 |
| Producto | 0.475 | 0.437 | 0.455 | 23,370 |
| Queja | 0.438 | 0.575 | 0.497 | 17,846 |
| Retención | 0.000 | 0.000 | 0.000 | 3,173 |
| Transaccional | 0.689 | 0.862 | 0.766 | 36,839 |
| Técnico | 0.396 | 0.231 | 0.292 | 15,817 |

**Por clase, B1 reglas**

| Motivo | Precisión | Cobertura (recall) | F1 | Casos |
|---|---|---|---|---|
| Comercial | 0.416 | 0.323 | 0.363 | 8,440 |
| Producto | 0.364 | 0.289 | 0.322 | 23,370 |
| Queja | 0.429 | 0.468 | 0.448 | 17,846 |
| Retención | 0.078 | 0.087 | 0.082 | 3,173 |
| Transaccional | 0.563 | 0.708 | 0.627 | 36,839 |
| Técnico | 0.261 | 0.182 | 0.214 | 15,817 |

**Matriz de confusión del campeón** (filas: real; columnas: predicho)

| | Comercial | Producto | Queja | Retención | Transaccional | Técnico |
|---|---|---|---|---|---|---|
| Comercial | 2,605 | 923 | 3,243 | 0 | 549 | 1,120 |
| Producto | 8 | 10,223 | 1,623 | 0 | 10,005 | 1,511 |
| Queja | 1,456 | 2,380 | 10,263 | 1 | 1,350 | 2,396 |
| Retención | 516 | 436 | 1,467 | 0 | 215 | 539 |
| Transaccional | 294 | 3,076 | 1,683 | 0 | 31,770 | 16 |
| Técnico | 326 | 4,493 | 5,147 | 0 | 2,192 | 3,659 |

## 6. Umbral de abstención

Costo supuesto: automatizar mal un código cuesta 5 unidades y mandar a revisión humana 1. Con probabilidades calibradas el corte teórico es 1 - 1/5 = 0.80; se eligió **0.81** minimizando el costo en validación (rejilla 0,30 a 0,99). Se aplica a la prueba sin reajustar.

| Umbral | Cobertura automática | Exactitud en lo automático | Costo medio |
|---|---|---|---|
| 0.50 | 57.5% | 67.6% | 1.356 |
| 0.60 | 34.3% | 76.1% | 1.067 |
| 0.70 | 24.5% | 80.5% | 0.993 |
| 0.80 | 14.6% | 84.6% | 0.966 |
| 0.90 | 0.0% | n/a | 1.000 |
| 0.95 | 0.0% | n/a | 1.000 |
| 0.81 (elegido) | 13.1% | 85.0% | 0.967 |

En el umbral elegido: cobertura [0.129, 0.133], exactitud automática [0.844, 0.856], costo [0.963, 0.971] (IC por cliente). Para el conjunto `contacto` el umbral elegido es 0.37 con cobertura 0.0%: el modelo casi siempre se abstiene, que es el comportamiento correcto cuando no hay señal.

## 7. Análisis de errores

Las clases Comercial, Queja, Retención y Técnico tienen el mismo sentimiento (misma distribución); solo se separan por duración y por cierre, y esas distribuciones se solapan, de ahí la confusión entre ellas. Transaccional y Producto son más fáciles: sentimiento acotado a ±0,3 y cierre resuelto. Ejemplos de errores con confianza sobre el umbral (filas enmascaradas, sin identificadores ni fechas):

| Tipo | Duración (s) | Sentimiento | Resuelto | Seguimiento | Real | Predicho | p |
|---|---|---|---|---|---|---|---|
| Inbound Call | 46 | -0.23 | 1 | 0 | Comercial | Transaccional | 0.82 |
| Outbound Call | 55 | -0.08 | 1 | 0 | Comercial | Transaccional | 0.81 |
| Outbound Call | 59 | +0.04 | 1 | 0 | Comercial | Transaccional | 0.85 |
| Inbound Call | 63 | -0.07 | 1 | 0 | Comercial | Transaccional | 0.86 |
| Inbound Call | 74 | +0.20 | 1 | 0 | Comercial | Transaccional | 0.86 |
| Inbound Call | 74 | +0.12 | 1 | 0 | Comercial | Transaccional | 0.86 |

Retención (3% de los casos) nunca se predice: sus rasgos se solapan con Comercial y Queja y el modelo prefiere no acertar en una clase tan pequeña; es la brecha principal y se corregiría con más señal, no con pesos de clase, que descalibrarían la probabilidad. Según la exploración descriptiva, lo que separa las clases es la duración, el sentimiento y el cierre; ninguno es texto. Idioma: los datos están solo en español (`detected_language` = es), por lo que no se mide transferencia a portugués ni a transcripciones multilingües (IA-2.3 queda abierto).

## 8. Límites y uso permitido

- Los datos son sintéticos: duración, sentimiento y cierre se generaron a partir del motivo, de modo que el resultado mide qué tan bien se recupera esa estructura y no una capacidad real de entender clientes. La cifra no debe extrapolarse a producción.
- El conjunto `llamada` usa información posterior al contacto: sirve para sugerir el código de cierre y como pista para el paso de comprensión cuando esas señales ya existen en el caso; no para enrutar antes de atender. El conjunto `contacto` no tiene señal.
- La pista nunca actúa: `SugerenciaMotivo.accion_permitida` es siempre falso y por debajo del umbral el caso sigue el camino humano.
- No se midió equidad por segmento ni país porque las etiquetas no dependen del segmento (diferencia máxima de proporción entre clases 0.009 en entrenamiento); queda como pendiente si el motivo llega a decidir algo con efecto.

## 9. Candidato descartado: fraude (IA-10.1)

`plata_transactions.is_fraud` tiene 4,316 positivos en 4,425,008 transacciones (0,10%). No se entrena ahí por dos hallazgos: (1) `fraud_score` está contaminado por la etiqueta: 2,373 de 2,373 transacciones con puntaje mayor a 30 son fraude (100%), el máximo del puntaje en no fraude es 30 (media 15.0) contra media 49.5 en fraude, y 885,157 puntajes son nulos; compararse contra él daría una línea base inválida. (2) La tasa de fraude por canal varía solo entre 0.0948% y 0.1079%, y no varía de forma apreciable por tipo, hora, moneda ni país en la exploración, de modo que los rasgos de la transacción no aportan señal. Cualquier modelo de fraude sobre estos datos solo reproduciría la fuga del puntaje.

## 10. Reproducción y artefactos

Semilla 202616737. Modelo y caché en `ia/artefactos/` (fuera de git). Ficha del modelo: `modelcard_motivo_2026-10-03.md`. Integración: `latam_ia.comprension.motivo.sugerir_motivo`.
