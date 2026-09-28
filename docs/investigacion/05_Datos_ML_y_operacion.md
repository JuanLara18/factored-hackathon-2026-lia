# Investigación 5: datos, el componente aprendido y la operación

**Pregunta:** ¿cómo se construye la parte de ingeniería de datos y de ML que el enunciado califica a
todos los equipos (*"Every team is assessed on data engineering and AI/ML rigor"*), y cómo se
demuestra una ruta creíble a producción?

El enunciado pide cuatro cosas concretas:
- **preparación repetible** con **contratos, chequeos de calidad, linaje y política de frescura**;
- **al menos un componente aprendido** evaluado contra una línea base, **sin fuga**, con
  representaciones, métricas, umbrales y particiones justificados;
- **trazas, reintentos acotados, caída segura, instalación reproducible**;
- si los datos son estáticos, **demostrar la corrección de las actualizaciones** con un *fixture*
  de prueba etiquetado.

**Hallazgo central:** el mayor riesgo técnico no está en el modelo sino en **el dataset
sintético**. Antes de elegir el componente aprendido hay que comprobar que las etiquetas tienen
señal real y que el texto no es una plantilla de la etiqueta. Si no se hace, se reporta una
exactitud del 99% que no significa nada.

> **Nota del 26 de septiembre de 2026, tras la [auditoría del dataset](13_Auditoria_del_dataset.md):** la trampa de la sección 1 se confirmó: el texto no predice la categoría (V de Cramér 0,011), `main_topics` es la etiqueta misma y `was_escalated` es ruido (AUC 0,51). El componente aprendido principal pasa a ser el riesgo de la transacción disputada, con `fraud_score` (AUC 0,87) como línea base (D-09).

---

## 1. El riesgo número uno: datos sintéticos

El dataset es **completamente sintético**, y las transcripciones ya traen columnas derivadas
(`detected_intents`, `main_topics`, `detected_keywords`) y la interacción trae `contact_reason`.
Tres trampas documentadas:

1. **El texto puede ser una plantilla de la etiqueta.** Si el generador escribió la transcripción
   a partir de `contact_reason`, un clasificador aprende la plantilla y da una exactitud casi
   perfecta que no transfiere a clientes reales. La literatura sobre datos sintéticos advierte que
   pueden **producir artefactos plausibles sin preservar las relaciones reales**
   ([*Synthetic Data Can Mislead Evaluations*](https://arxiv.org/pdf/2501.11786)).
   **Prueba:** un TF-IDF con regresión logística; si da más de 98%, sospechar. Mirar las palabras de
   mayor peso: si son frases de plantilla, hay fuga.
2. **Las columnas "detectadas" son fuga si se usan como entrada.** `detected_intents` o
   `main_topics` pueden ser la respuesta. Usarlas como etiqueta débil está bien; como
   característica, no.
3. **Las relaciones entre tablas pueden ser ruido.** En muchos generadores sintéticos, `was_resolved`
   o `was_escalated` se sortean sin depender de nada. **Prueba:** ¿predice algo mejor que el azar
   (AUC ≈ 0,5)? Si no hay señal, ese no puede ser el componente aprendido.

**Preference leakage:** si un LLM genera los casos de prueba y un LLM de la **misma familia** los
juzga, el juez favorece el estilo de su generador
([arXiv 2502.01534](https://arxiv.org/html/2502.01534v3)). Generador y juez de familias distintas.

**Esta auditoría es en sí misma un resultado reportable**: el enunciado pide *"report limitations
in the supplied data"*. Un equipo que muestra que detectó y evitó una fuga suma puntos de rigor.

## 2. Preparación repetible: contratos, calidad, linaje, frescura

### Contratos de datos

El estándar abierto es **ODCS** (*Open Data Contract Standard*) de **Bitol**, proyecto de la Linux
Foundation, versión **3.1.0** ([anuncio](https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/),
[especificación](https://github.com/bitol-io/open-data-contract-standard/blob/main/docs/README.md)).
Un contrato es **un YAML por tabla** con esquema, semántica, **reglas de calidad**, dueños, **SLA**
y dónde vive el dato. La 3.1 añade **relaciones y llaves foráneas** entre esquemas y métricas con
nombre: `rowCount`, `nullValues`, `invalidValues`, `duplicateValues`, `missingValues`. Hay una CLI
([datacontract.com](https://docs.datacontract.com/open-data-contract-standard)) que **valida los
datos contra el contrato**.

**Encaje directo:** el diccionario de datos ya trae tipos, restricciones (PK, NOT NULL, UNIQUE,
FK) y dominios (los valores permitidos de `segment`, `status`, etc.). Pasarlo a ODCS es casi
mecánico y deja un artefacto que el jurado reconoce.

### Chequeos de calidad

| Herramienta | Estilo | Cuándo |
|---|---|---|
| **Pandera** | esquemas en Python sobre DataFrames | validación dentro del código de preparación |
| **Soda Core** | YAML declarativo con SQL | chequeos rápidos sobre tablas |
| **Great Expectations** | expectativas como código, con documentación generada | cuando se quiere un reporte legible |
| **dbt tests** | pruebas sobre modelos SQL | si la transformación es en dbt |

([comparación](https://pipecode.ai/blogs/data-quality-frameworks-great-expectations-vs-dbt-tests-vs-soda-core))

**Los problemas que el dataset trae a propósito** y su chequeo:

| Problema | Tasa | Chequeo y tratamiento |
|---|---|---|
| Duplicados | ~2% | unicidad de la PK; deduplicar con `ROW_NUMBER()` quedándose con el registro más reciente por `last_updated` |
| Nulos | ~5% | nulos solo en campos que el contrato permite; los demás, a cuarentena |
| **Llegadas tardías** | sí | ventana de corrección por `process_date` (reprocesar los últimos N días) |
| **Evolución de esquema** | sí | el contrato versionado detecta columnas nuevas o cambiadas; política explícita de qué hacer |
| Huérfanos de FK | pequeño % | integridad referencial como chequeo; registrar, no borrar en silencio |

### Procesamiento incremental e idempotente

Buenas prácticas coincidentes ([dbt en producción](https://www.datalane-data.blog/blog/dbt-incremental-models-in-production/),
[MotherDuck](https://motherduck.com/docs/key-tasks/loading-data-into-motherduck/loading-patterns/)):

- modelos **incrementales con llave única**, para que reejecutar sea seguro (**idempotencia**);
- **ventana de corrección** de 48 a 72 horas para hechos tardíos, ajustada con el percentil de
  retraso **observado**, no a ojo;
- particiones por fecha de evento o de carga, con corte explícito;
- si cambia el grano o el esquema de forma no aditiva, **refresco completo**.

**DuckDB con dbt** (o solo DuckDB con SQL) procesa decenas de millones de filas en un portátil y es
reproducible sin infraestructura.

**El fixture de actualización** que pide el enunciado: un lote pequeño y **etiquetado como prueba**
que simula una partición tardía, un duplicado y un cambio de esquema, con el resultado esperado de
la tabla después de aplicarlo. Una prueba automatizada verifica que el pipeline lo procesa bien y
que correrlo dos veces da lo mismo.

### Linaje y frescura

**OpenLineage** es el estándar abierto de linaje; **Marquez** es su implementación de referencia, e
integra con dbt, Airflow, Spark y Dagster ([OpenLineage](https://github.com/OpenLineage/OpenLineage),
[Marquez](https://marquezproject.ai/)). Para un prototipo basta con emitir eventos de linaje por
corrida o, más simple, **un manifiesto por corrida** (entradas con su huella, versión del código,
salidas, conteos) y el grafo que genera dbt.

**Política de frescura**: por tabla, cada cuánto se actualiza y cuánto retraso se tolera antes de
que el agente **no deba** usar ese dato (por ejemplo, un saldo de hace más de un día no se afirma
como saldo actual; se dice la fecha de corte).

## 3. El componente aprendido

El enunciado exige al menos uno, con línea base, y lo califica aunque la solución use modelos
preentrenados: *"demonstrate those competencies through component selection, relevance or intent
labels, representations, leakage prevention, held-out evaluation, and error analysis"*.

### Candidatos

| Componente | Etiqueta en el dataset | Línea base | Valor en el flujo |
|---|---|---|---|
| **Clasificador de intención o motivo** | `contact_reason`, `reason_category` | palabras clave; TF-IDF con regresión logística | enrutar al flujo correcto; detectar **fuera de alcance** |
| **Predictor de escalamiento** | `was_escalated`, `requires_followup` | tasa base; reglas | decidir el traspaso **temprano** |
| **Recuperador de políticas** | juicios de relevancia **a construir** | BM25 | anclar las respuestas en la política correcta |
| **Detector de riesgo en disputas** | `is_fraud`, `fraud_score`, `is_repeat_complainer` | `fraud_score` existente | señalar fraude de primera parte para revisión humana |

### El clasificador de intención: lo que dice la evidencia

- En **BANKING77** (77 intenciones bancarias), un **modelo pequeño ajustado** (LoRA sobre
  xlm-roberta-large) llegó a **94,2%** frente a **85,3%** de un LLM grande con *prompt*, y respondió
  en **12 ms frente a 2 s** ([intent-router](https://github.com/smallestbusiness/intent-router)).
  **TF-IDF con regresión logística quedó a 2,3 puntos del LLM ajustado, con 1/300 de la latencia**
  ([finetune-intent-lab](https://github.com/RahulRachhoya/finetune-intent-lab)). **SetFit** da ~91%
  con pocos ejemplos, en milisegundos y sin costo marginal.
- Un marco de decisión de 2026 ([arXiv 2608.20371](https://arxiv.org/pdf/2608.20371)): **NLU
  ajustado** si hay menos de ~50 intenciones, latencia estricta, presupuesto limitado o se necesita
  **detección confiable de fuera de alcance**; **LLM** si hay pocas etiquetas, muchas intenciones
  o se necesita **multilingüe**.
- Una evaluación de **41 modelos abiertos** en clasificación de intención sin ejemplos
  ([arXiv 2607.27421](https://arxiv.org/html/2607.27421v1)) sirve para escoger el LLM de
  comparación.

**Diseño sugerido:** comparar tres niveles sobre el mismo conjunto retenido: **TF-IDF con regresión
logística** (línea base), **embeddings multilingües con un clasificador** o SetFit, y **LLM sin
ajuste**. Reportar F1 macro, **calibración** (el umbral de fuera de alcance depende de ella), latencia
y costo. El multilingüe importa: entrenar con español y **probar en portugués** mide la
transferencia, que es justo la limitación de cobertura que pide reportar el enunciado.

**Particiones sin fuga:** partir **por cliente** (el mismo cliente no puede estar en entrenamiento y
prueba) y, mejor aún, **por tiempo** (entrenar con lo anterior a una fecha y probar con lo
posterior), porque así se usará en producción y porque el dataset tiene tres años con posible
deriva.

### El recuperador de políticas

El dataset **no trae documentos de política**. Hay que escribir un corpus sintético pequeño
(plazos por país, qué exige confirmación, requisitos de una disputa) y **construir juicios de
relevancia** (pregunta, documento correcto) para evaluar BM25 frente a embeddings frente a
híbrido, con recall@k y MRR. FraudBench mostró que la recuperación sola le cuesta **13 puntos** a un
agente bancario: medirla por separado es un aporte.

## 4. Operación: la ruta creíble a producción

### Trazas

Las **convenciones semánticas GenAI de OpenTelemetry** son ya el estándar común: spans
`invoke_agent`, `chat` (cada llamada al modelo) y `execute_tool` (cada herramienta), con tokens,
tiempos, entradas y salidas ([OpenTelemetry](https://opentelemetry.io/blog/2026/genai-observability/),
[MLflow](https://mlflow.org/docs/latest/genai/tracing/opentelemetry/genai-semconv/)).
**Langfuse, Arize Phoenix, OpenLLMetry y MLflow** las implementan, así que la elección de backend
es reversible.

El enunciado: *"hidden model chain-of-thought is not an audit artifact"*. **La explicación
auditable es el registro de ejecución**: qué herramienta se llamó, con qué argumentos, qué devolvió,
qué regla de política se aplicó y qué fuente respaldó cada afirmación.

### Reintentos acotados y caída segura

- Reintentos con **backoff exponencial y tope** (por ejemplo, 2 reintentos), solo para operaciones
  **idempotentes** (Nubank exige idempotencia en todas las acciones).
- **Llave de idempotencia** en toda acción que escribe (radicar la disputa dos veces no crea dos).
- **Timeouts** por herramienta y un **presupuesto** por conversación (tokens, llamadas, tiempo),
  que es la defensa contra el consumo sin límite de OWASP.
- **Caída segura**: si falla el modelo o una herramienta, se dice la verdad y se ofrece el
  traspaso, nunca se inventa un resultado.

### Reproducibilidad, capacidad y monitoreo

- **Instalación reproducible**: dependencias fijadas, contenedor, un comando para levantar todo,
  semillas fijas y **versiones de modelo, prompt y política** registradas por corrida.
- **Límites de capacidad**: medir cuántas conversaciones concurrentes aguanta y dónde está el cuello
  (normalmente la API del LLM y sus límites de tasa).
- **Monitoreo**: las métricas de la investigación 4 en vivo (resolución segura, escalamiento,
  inseguros, latencia, costo) más **deriva** de la distribución de intenciones y de la confianza
  del clasificador.

## 5. Primer análisis exploratorio que sale de aquí

Antes de decidir nada, en este orden:

1. **Motivos de contacto**: volumen de `contact_reason` y `reason_category`, por país, canal y
   mes; FCR, escalamiento, duración y espera por motivo. Confirmar si "transacciones no
   reconocidas" pesa en el dataset como pesa en los reguladores (investigación 1).
2. **Auditoría sintética**: ¿el texto de `call_transcripts` es plantilla de `contact_reason`? ¿Hay
   señal en `was_resolved` y `was_escalated`? ¿`is_fraud` se relaciona con algo?
3. **Calidad**: duplicados, nulos, huérfanos y llegadas tardías medidos por tabla, contra lo
   anunciado (2%, 5%).
4. **Cobertura lingüística**: distribución de `detected_accent` y `detected_language`; confirmar
   que no hay portugués.
5. **Quejas**: `complaints.category`, SLA incumplidos y reclamantes recurrentes, para el flujo de
   disputas.

## Fuentes principales

- [ODCS 3.1, Bitol](https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/)
- [OpenLineage](https://github.com/OpenLineage/OpenLineage) y [Marquez](https://marquezproject.ai/)
- [Comparación de herramientas de calidad](https://pipecode.ai/blogs/data-quality-frameworks-great-expectations-vs-dbt-tests-vs-soda-core)
- [dbt incremental con llegadas tardías](https://www.datalane-data.blog/blog/dbt-incremental-models-in-production/)
- [intent-router, BANKING77](https://github.com/smallestbusiness/intent-router) y [marco de decisión NLU frente a LLM](https://arxiv.org/pdf/2608.20371)
- [OpenTelemetry GenAI](https://opentelemetry.io/blog/2026/genai-observability/)
- [Synthetic Data Can Mislead Evaluations](https://arxiv.org/pdf/2501.11786) y [Preference Leakage](https://arxiv.org/html/2502.01534v3)
