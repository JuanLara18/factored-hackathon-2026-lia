# Cobertura del enunciado (revisión del 26 de septiembre de 2026)

**Propósito:** asegurar que no se nos escape nada de lo que pide el reto. Se releyó el enunciado
frase por frase, junto con el resumen y el diccionario del dataset, y se contrastó con todo lo escrito
(principios, interacciones, plan, datos por capas, organización, decisiones e investigaciones 1 a 19).
Lo que se podía verificar con datos se verificó en el bucket el mismo día (sección 3).

**Cómo leerlo:** la sección 1 resume lo que se nos estaba escapando, ordenado por impacto; la 2 es la
matriz completa; la 3, la evidencia nueva; la 4, las preguntas para los organizadores; la 5, qué se
cambió en los demás documentos.

---

## 1. Lo que se nos estaba escapando

### Críticos (cambian el plan)

1. **El componente aprendido planeado no puede ganar.** Fuera de `fraud_score`, `is_fraud` no tiene
   ninguna señal: un modelo entrenado en enero y probado en febrero da AUC 0,504 y PR AUC igual a la
   prevalencia. Y `fraud_score` es una **fuga de la etiqueta**: ninguna transacción legítima pasa de
   30, así que `fraud_score > 30` identifica fraude con precisión 1,0 (recuperación 0,57). D-09 queda
   sin piso; se propone D-14 (sección 5).
2. **Datos del organizador en modelos externos y en repositorios públicos.** El enunciado prohíbe
   incluir *"private customer records, credentials, or restricted data in public submissions or
   external model requests"*. Aunque el dataset es sintético, su acceso está restringido a los
   participantes. Nuestro diseño manda hechos del cliente (enmascarados) a un LLM y pensaba sembrar
   casos de evaluación con filas reales. Hay que **preguntar** qué está permitido y, mientras tanto,
   diseñar para el caso restrictivo (D-15).
3. **"Measure whether your approach improves service quality and operational efficiency"** exige
   resultados definidos y una línea base **construida con los datos**. Teníamos métricas del sistema,
   pero no los **resultados para el cliente y el negocio** ni la línea base operativa del proceso de
   reclamos, que el dataset sí permite calcular (sección 3.2).
4. **El canal.** El 84,8% de las interacciones del dataset son telefónicas, y el dataset está
   construido alrededor de la voz (grabaciones, transcripciones con cuatro motores de reconocimiento de
   voz, detección de acento). Nuestro diseño es de chat. No es un error, pero **hay que justificarlo
   con los datos** o mostrar voz (pregunta para la presidencia).
5. **La mezcla de casos decide la métrica.** La resolución automática segura se reporta *"over all
   in-scope test cases"*: si el retenido es mitad adversarial, la tasa no representa nada. Hacen falta
   **dos conjuntos retenidos**: uno representativo de la demanda y uno de estrés (D-16).

### Importantes (faltaban en el diseño)

6. **Restricciones operativas** (criterio 1): el dataset las trae y no las habíamos mirado. Solo 129
   de 1.200 agentes hablan portugués; solo 7 de ellos son especialistas en fraude, y **uno solo** de
   esos está en turno de noche o rotativo. La demanda es plana en las 24 horas (un tercio de los
   contactos ocurre entre 00:00 y 07:59) y solo el 15% de los agentes trabaja de noche. El traspaso
   urgente en portugués a las 3 de la mañana es un cuello de botella real del banco.
7. **Análisis de errores** (*"error analysis"*, pedido explícito para soluciones preentrenadas): no
   estaba planeado como entregable.
8. **Límites de capacidad y escalabilidad** (*"explain capacity limits"*, *"scalability"*): sin prueba
   de carga ni análisis de cuellos de botella (límites de tasa del LLM; DuckDB admite un solo escritor
   y no sirve como base operativa de casos y sesiones).
9. **Explicabilidad**: teníamos explicación para el auditor (trazas), no para el **cliente** ni para el
   **agente humano** (por qué se escaló, por qué ese plazo, por qué esa ruta).
10. **Atributos protegidos** (*"authorized customer segments"*): el dataset trae género, fecha de
    nacimiento, estado civil y educación; el 31% de los clientes tiene 65 años o más. Hay que decidir
    qué atributos se usan para decidir (ninguno protegido) y cuáles se usan solo para auditar equidad.
11. **Batch contra tiempo real** (*"according to the supplied inputs and the workflow's latency and
    freshness needs"*): un cliente llama por un cargo de hace cinco minutos; el pipeline diario no lo
    ve. Hay que separar la **ruta operativa** (APIs del core, simuladas) de la **ruta analítica**
    (capas bronce a platino) y justificarlo.
12. **Ningún movimiento de dinero** (*"No ... movement of money is required or authorized"*): el abono
    provisional de México (N6) solo se **registra** como pendiente para el back office; nunca se
    ejecuta ni se promete como hecho.
13. **Trade-offs medidos**: los puntos de operación (conservador, balanceado, agresivo) se registran
    antes de correr el retenido y se reportan los tres.
14. **Portugués con rigor**: quién es el cliente que habla portugués (su cuenta está en MX, CO o AR, y
    le aplica la norma de ese país), quién valida las respuestas en portugués y cómo se reporta la
    calidad de esas etiquetas.
15. **Calidad de etiquetas con un equipo pequeño**: sin un segundo anotador humano no hay κ entre
    humanos; hay que declarar el protocolo real.

### Menores (se corrigen al pasar)

16. El resumen dice que las particiones *"may arrive late"* y los esquemas *"may evolve"*, y el bucket
    ya cambió una vez (1 de septiembre). Hay que **vigilarlo** durante el evento y procesar entregas
    reales si llegan.
17. Escenarios que los datos ofrecen y el catálogo no tenía: transacción pendiente, revertida o
    rechazada; tarjeta ya bloqueada; reclamo fuera de plazo; reclamo duplicado; cargo en otro país;
    cliente con cuenta cerrada o suspendida; "¿por qué me rechazaron la compra?" como solicitud no
    soportada.
18. El enunciado dice que *streaming* y tablero no son obligatorios: pasan a opcionales.
19. Un campo de "razonamiento" en las salidas estructuradas (investigación 8) es texto del modelo:
    sirve para depurar, **no** es evidencia de auditoría.
20. Falta un **inventario de insumos** con su clase (real, desidentificado, sintético, del equipo,
    externo público).
21. La demo debe **mostrar** trazas, reintentos acotados y caída segura, no solo describirlos.

## 2. Matriz frase por frase

Estado: **C** cubierto, **P** parcial, **F** falta, **R** en riesgo.

| # | Texto del enunciado | Dónde está | Estado | Acción |
|---|---|---|---|---|
| 1 | *working AI-first customer service system* | plan F3 | P | definir "AI-first" en el reporte: la IA atiende primero, entiende y explica; el código decide |
| 2 | *understand complex customer interactions* | 01, A1 a A4 y L1 a L4 | C | registro regional en la respuesta (voseo en AR) sin cambiar decisiones |
| 3 | *use data and tools securely* | P5, P11, inv. 8 y 17 | C | |
| 4 | *complete appropriate service workflows* | rutas R1 a R8 | C | |
| 5 | *involve human agents when needed* | R4, R5, traspaso | P | diseñar el traspaso con las restricciones de agentes (idioma, turno, especialidad) |
| 6 | *use the supplied data to explain why the problem matters* | inv. 13 | P | 18% de las quejas y línea base del proceso (3.2); datos de reguladores como contexto, etiquetados |
| 7 | *establish a baseline* | inv. 4, 01 §6 | P | añadir línea base operativa de reclamos y línea base "todo humano" simulada sobre el mismo retenido |
| 8 | *improves service quality and operational efficiency* | 01 §5 | P | árbol de resultados para cliente y negocio (sección 5) |
| 9 | *privacy, explainability, fairness, reliability, scalability* | P5, P11, P12 | P | explicabilidad para cliente y agente; prueba de capacidad |
| 10 | *explicit trade-offs across autonomy, accuracy, latency, cost, human oversight* | inv. 11 §6 | P | tres puntos de operación registrados antes del retenido |
| 11 | *where AI is appropriate, where deterministic logic is preferable* | P4, inv. 2 | P | tabla única por componente en el reporte |
| 12 | *evaluate for quality and safety* | 01, inv. 4 | C | |
| 13 | *production readiness and an honest account of the work required* | P2, P3 | P | sección "trabajo restante" en el reporte |
| 14 | *coherent workflow* | D-02 | C | pasar D-02 a provisional |
| 15 | *normal, ambiguous or unsupported, requiring human* | 01 | C | caso no soportado anclado en datos ("¿por qué me rechazaron?") |
| 16 | *Spanish and Portuguese* | L2, L3 | P | persona en portugués, norma aplicable, validación de las respuestas |
| 17 | *report limitations in the supplied data or language coverage* | inv. 13 | C | sumar los hallazgos de la sección 3 |
| 18 | *analyze contact reasons* | inv. 13 | P | declarar que `contact_reason` es grueso; motivo fino desde quejas |
| 19 | *relevant demand patterns* | 03 §3.2 | F | patrón semanal, horario plano, canales; en el EDA de plata |
| 20 | *data quality* | inv. 13, 03 | C | |
| 21 | *operational constraints* | nada | F | agentes, turnos, idiomas, plazos regulatorios, costo por canal, límites del LLM (3.1) |
| 22 | *prioritize the workflow* | D-02 | C | |
| 23 | *define the intended customer and business outcomes* | nada explícito | F | árbol de resultados (sección 5) |
| 24 | *maintain relevant conversational context* | 01 §4, D5, D6 | C | |
| 25 | *clarify ambiguity* | A1 a A4 | C | |
| 26 | *ground factual responses in permitted account, transaction, or policy information* | P6, inv. 8 | P | fijar la fuente de información de política: tabla versionada más preguntas frecuentes con fuente |
| 27 | *use tools when they serve the workflow* | inv. 17 | C | |
| 28 | *report only actions whose outcomes the system has verified* | P6 | C | escenario de tarjeta ya bloqueada |
| 29 | *which requests it can answer, which require confirmation, when to abstain or transfer* | inv. 2 §4 | P | matriz de autonomía como artefacto de `policy/v1` |
| 30 | *enforce permissions and policy outside model-generated prose* | P5, inv. 18 | C | |
| 31 | *request, verified facts, actions taken, supporting evidence, unresolved questions* | inv. 2 §5, inv. 14 | C | |
| 32 | *repeatable data preparation with contracts, quality checks, lineage, freshness policy* | 03, inv. 16 | C | |
| 33 | *evaluate at least one learned component against an appropriate baseline* | D-09 | **R** | D-14 |
| 34 | *valid labels or relevance judgments* | D-09 | **R** | protocolo de etiquetas de D-14 |
| 35 | *prevent leakage* | P10 | C | auditar nuestros datos generados con las mismas pruebas de plantilla de la inv. 13 |
| 36 | *justify representations, metrics, thresholds, and evaluation splits* | inv. 15 | P | sección obligatoria del reporte del componente |
| 37 | *evaluate on held-out cases* | 01 §6 | C | |
| 38 | *incorrect or missing data, expired sessions, unauthorized access, prompt injection, tool failures, multilingual ambiguity* | D, S y L del catálogo | C | |
| 39 | *report successful and unsafe outcomes, handoff behavior, latency, cost, sample sizes and limitations* | 01 §5 | C | |
| 40 | *demonstrate tracing, bounded retries, safe fallback, reproducible setup* | 02 F7 | P | guion de demo que los muestre |
| 41 | *explain capacity limits* | nada | F | prueba de carga con usuarios simulados concurrentes; cuellos de botella |
| 42 | *monitoring* | 04 §10, inv. 5 | P | plan con indicadores, umbrales de alerta y deriva |
| 43 | *access controls* | P5 | P | control de acceso también para la vista del agente humano y para operadores |
| 44 | *data retention* | 03 §8 | C | |
| 45 | *remaining deployment work* | principios | P | sección del reporte |
| 46 | *explanations based on sources, policy rules, and execution records; hidden chain-of-thought is not an audit artifact* | inv. 19 | C | nota sobre el campo de razonamiento (punto 19) |
| 47 | *streaming ... dashboard ... not mandatory* | plan F3 incluía *streaming* | P | opcionales |
| 48 | *component selection, relevance or intent labels, representations, leakage prevention, held-out evaluation, error analysis* | inv. 5 y 15 | P | análisis de errores y selección de componentes como entregables |
| 49 | *batch, incremental, or streaming according to inputs and latency and freshness needs* | 03 | P | ruta operativa contra ruta analítica |
| 50 | *if only static data is supplied, a clearly labeled test fixture* | 03 §5.4 | C | vigilancia del bucket por si llegan entregas reales |
| 51 | *organizer-approved data and permitted external resources* | nada | F | lista de recursos externos a confirmar (sección 4) |
| 52 | *identify which inputs are real, de-identified, synthetic, or team-generated* | disperso | P | inventario de insumos |
| 53 | *follow the published data-use terms* | nada | F | encontrar los términos |
| 54 | *no private records, credentials, or restricted data in public submissions or external model requests* | P11 | **R** | D-15 |
| 55 | *mock banking tools with documented contracts and limitations* | inv. 17 | C | |
| 56 | *trusted test session or identity service* | inv. 17 | C | |
| 57 | *enforce access in the service or tool layer* | P5 | C | |
| 58 | *no ... movement of money* | 01 N6 | P | abono provisional solo como registro para el back office |
| 59 | *explanations, uncertainty, and review paths for borderline cases* (párrafo de crédito, aplicable por analogía) | nada | P | zona gris de la regla de riesgo con revisión humana |
| 60 | *same held-out workload* | 01 §6 | C | |
| 61 | *number and mix of cases* | 01 §9 | P | dos conjuntos retenidos (D-16) |
| 62 | *label quality* | 01 §6 | P | protocolo según el tamaño real del equipo |
| 63 | *model and prompt versions, repeated-run variability* | inv. 15, 01 | C | |
| 64 | *include failures in the results* | P2 | C | |
| 65 | *judge rubric validated against human or deterministic judgments* | inv. 4 | C | |
| 66 | *safe automated resolution over all in-scope cases plus share attempted* | 01 §5.1 | C | |
| 67 | *containment ... escalation quality ... missed and unnecessary transfers* | 01 §5.1 | C | |
| 68 | *unsafe outcomes with counts and denominators* | 01 §5.1 | C | |
| 69 | *p50/p95, cost per attempted case and per successful resolution, "not defined"* | 01 §5.6 | C | |
| 70 | *by language and authorized customer segments* | P12 | P | definir segmentos autorizados y el uso de atributos protegidos |
| 71 | *offline, simulations, projected savings labeled separately* | P3 | C | |

**Del resumen y el diccionario del dataset:**

| Texto | Estado | Acción |
|---|---|---|
| *Late Arrivals: partitioned data may arrive late*; *Schema Evolution: schemas may evolve* | P | vigilar el bucket; el *fixture* cubre el caso estático |
| *All transactions include both local currency and USD conversion* | P | falso en la práctica (México en USD; `amount_usd` estructuralmente vacío); `daily_exchange_rates` trae 13.164 filas y 12 pares con MXN, no 3.000 |
| *Accent Detection ... dialect-aware customer service analysis*; *Accent-based routing optimization* | C | equidad por variante; nunca decidir por acento (P12) |
| *Referential integrity ... small percentage of orphaned records* | C | chequeos de existencia y de dueño |

## 3. Evidencia nueva (verificada hoy en el bucket)

Muestra: la de la investigación 13 más `service_agents`, `daily_exchange_rates` y `digital_events` de
enero de 2025 (443.948 eventos). El bucket no cambió desde el 1 de septiembre.

### 3.1 Restricciones operativas

| Hecho | Cifra | Implicación |
|---|---|---|
| Agentes que hablan portugués | 129 de 1.200 (10,8%); 115 activos | la cola en portugués es pequeña |
| Especialistas en fraude | 105; con portugués, **7** | el traspaso urgente en portugués depende de siete personas |
| Especialistas en fraude en turno de noche | 25; con portugués y turno de noche o rotativo, **1** | a las 3 a. m. casi no hay quien reciba un fraude en portugués: el traspaso debe prever cola con tiempo de espera declarado, contención inmediata (bloqueo) y aviso |
| Demanda por hora | plana en las 24 horas (artefacto sintético); 33% entre 00:00 y 07:59 | contra 15% de agentes de noche: la IA vale más de noche |
| Demanda por día | fines de semana a la mitad de los días hábiles | dimensionamiento |
| Canales | teléfono 84,8%; correo 4,1; app 3,8; chat web 3,4; WhatsApp 3,3; web 0,5 | justificar el canal (punto 4) |

### 3.2 Línea base del proceso de reclamos ("Cargo no reconocido", 866 casos de la muestra)

| Indicador | Valor |
|---|---|
| Horas hasta la asignación (mediana) | 13 |
| Horas hasta la primera respuesta (mediana y p90) | 38 y 57 |
| Días hasta la resolución (mediana, resueltos) | 17 |
| SLA incumplido | 20,6% |
| Reclamante recurrente en 90 días | 15,9% |
| Recibidos por call center | 50%; por el regulador, 1,2% |
| Prioridad crítica | 4,6% |
| Estado: resueltos | 19,3% |

**Cuidado al usarla:** los mismos indicadores son prácticamente iguales para las demás subcategorías
(el generador no las distingue), y `sla_breached` no se relaciona con `resolution_days` (media 15,6
días sin incumplimiento contra 14,9 con incumplimiento). Sirve como **nivel de referencia**, no para
afirmar que los cargos no reconocidos se atienden peor. El argumento de negocio que sí sostiene:
**38 horas hasta la primera respuesta** cuando en fraude con tarjeta y en transferencias inmediatas la
contención se mide en minutos (investigación 6).

**Satisfacción:** CSAT medio entre 2,43 (quejas) y 2,90 (transaccional) sobre 5, con puntajes
observados entre 1 y 4.

### 3.3 Señal para aprender

| Prueba | Resultado |
|---|---|
| `is_fraud` sin `fraud_score` (entrenado en enero, probado en febrero; tipo, canal, estado, comercio, país, segmento, producto, fuera del país, hora, monto, antigüedad) | AUC **0,504**; PR AUC 0,001, igual a la prevalencia |
| Tasa de fraude por canal, tipo y país | plana, entre 0,08% y 0,12% |
| `fraud_score` en transacciones legítimas | máximo **30,0** |
| `fraud_score > 30` como regla | precisión **1,0**, recuperación 0,57 |
| `fraud_score` nulo | 20% a 22% en ambas clases |
| `digital_events`: IP de un país distinto al del cliente | **0%** |
| `digital_events`: eventos en las 24 h previas a una transacción | menos del 1%, sin diferencia entre fraude y no fraude |
| `digital_events` sin cliente | 23,6% |

**Lectura:** la etiqueta de fraude es aleatoria salvo por un puntaje derivado de ella. No hay
componente aprendido honesto sobre `is_fraud`, y los eventos digitales no permiten modelar toma de
cuenta. Ambos son **hallazgos reportables** del criterio 4.

### 3.4 Comercios y transacciones por cliente

- Solo **24 comercios distintos**, con nombres genéricos ("Mercado Central", "Tienda Don José", "Uber").
- Mediana de **2 transacciones por cliente** en dos meses (p90: 4).
- Solo el 1,9% de los pares cliente y comercio se repite.

**Consecuencias:** ubicar la transacción que menciona el cliente es casi trivial con filtros (no
justifica un modelo aprendido); la "ficha de la transacción" (investigación 14) necesita un **directorio
de comercios del equipo** (razón social, descriptor, marca) para que exista la confusión realista; y
el escenario E3 (compras previas en el mismo comercio) es raro en los datos y se construye a propósito.

## 4. Preguntas para los organizadores

Bloqueantes para F0 y F2. Conviene enviarlas juntas.

1. ¿Fechas de inicio y entrega, formato de la entrega (repositorio, reporte, video, presentación) y
   criterios de calificación con sus pesos?
2. ¿Tamaño del equipo? ¿Se permite participar individualmente?
3. ¿Se permite enviar registros del dataset, aunque sean sintéticos, a APIs de modelos externos
   (OpenAI, Anthropic, Google)? ¿Con qué condiciones (enmascarado, retención cero)?
4. ¿El repositorio de la entrega debe ser público? ¿Puede contener muestras del dataset o solo código
   que las descargue?
5. ¿Dónde están publicados los términos de uso de datos?
6. ¿Habrá entregas incrementales durante el evento (particiones tardías, cambios de esquema)? ¿Qué es
   `data_backup_20260831/` y cuál es la versión oficial?
7. ¿Qué recursos externos están permitidos: modelos preentrenados abiertos, datasets públicos (por
   ejemplo, BANKING77), textos normativos públicos?
8. ¿Hay créditos de nube o de APIs de modelos?
9. ¿Se puede preparar código o infraestructura antes del inicio oficial, o todo debe construirse
   durante los diez días?
10. ¿Está permitido usar APIs de voz (reconocimiento, síntesis, modelos de audio a audio) y grabar
    voces de personas del equipo, con consentimiento, para evaluar?

## 5. Consecuencias y decisiones propuestas

### D-14 (propuesta): el componente aprendido es la comprensión de la recepción, no el riesgo

- **Componente:** clasificador de la recepción de disputas a partir del mensaje del cliente: **motivo**
  (fraude, error de procesamiento, disputa comercial, "no la reconozco pero es mía", no es disputa,
  fuera de alcance), **urgencia** (transferencia reciente, "me llamaron del banco") y **entidades**
  (monto, fecha relativa, comercio).
- **Línea base:** palabras clave; TF-IDF con regresión logística. **Comparados:** embeddings
  multilingües con clasificador o SetFit; LLM sin ajuste y con pocos ejemplos.
- **Etiquetas válidas:** conversaciones escritas y generadas por el equipo **desde una ruta y un estado
  conocidos** (investigación 15), con semilla humana, generador y juez de familias distintas, y una
  auditoría de plantilla sobre nuestros propios datos con las mismas pruebas de la investigación 13.
- **Métricas y umbrales:** F1 macro, calibración, curva de riesgo y cobertura para el umbral de
  "fuera de alcance" y de aclaración; transferencia de español a portugués; **análisis de errores**
  por clase, variante e idioma.
- **`fraud_score`** pasa a ser una **entrada determinista** de la política (dominio *Fraud Diagnosis*):
  mayor que 30, riesgo alto; resto, sin evidencia; con zona gris revisada por humano. Su fuga se
  reporta.
- **El experimento del puntaje de riesgo** se reporta como resultado negativo con partición temporal:
  demuestra rigor, no se esconde.

### D-15 (propuesta): los datos del organizador no salen

- Ninguna fila del dataset en el repositorio ni en el reporte; los casos de evaluación guardan
  **llaves** y se materializan localmente desde el bucket; los ejemplos del reporte van enmascarados.
- Al LLM externo solo llegan hechos mínimos, enmascarados, y solo si los organizadores lo permiten;
  **plan B**: un modelo abierto local para los trabajadores que tocan datos del cliente.

### D-16 (propuesta): dos conjuntos retenidos

- **Representativo:** mezcla de rutas estimada con supuestos declarados (la mayoría de los "no
  reconozco" son confusión; investigación 14), para las métricas de resolución y eficiencia.
- **Estrés:** fallas, ataques y casos borde, para las métricas de seguridad y caída segura.
- Cada métrica declara sobre qué conjunto se calcula.

### Árbol de resultados (para la VP Clientes y la VP Datos)

| Nivel | Resultado | Indicador | Línea base con datos |
|---|---|---|---|
| Cliente | contención rápida del fraude | minutos hasta el bloqueo en R3 y R4 | 38 h hasta la primera respuesta (reclamos) |
| Cliente | caso bien radicado al primer contacto | completitud y exactitud del caso | reclamos sin interacción de origen ni monto respaldado (limitación del dataset, declarada) |
| Cliente | entender cargos sin disputar | resolución segura en R1 | sin equivalente en los datos |
| Cliente | no repetir información | preguntas repetidas; completitud del traspaso | reclamante recurrente 15,9% |
| Negocio | cumplir plazos regulatorios | plazo correcto por país; casos fuera de plazo | SLA incumplido 20,6% |
| Negocio | menos minutos humanos por caso | minutos humanos por caso en el retenido | duración mediana 204 s por contacto transaccional; "todo humano" simulado |
| Negocio | menos escalamientos al regulador | proyección, etiquetada | 1,2% de reclamos llega por el regulador |

**Actualización del 26 de septiembre de 2026:** el punto 4 de la sección 1 quedó resuelto: la
presidencia decidió atender por chat y por voz sobre el mismo núcleo (D-17 y D-18). Las decisiones
D-14, D-15 y D-16 quedaron firmes (D-15 provisional solo en el uso de modelos externos).

## 6. Cambios aplicados hoy en otros documentos

- [01](01_Interacciones_y_criterios.md): escenarios nuevos (sección 1, punto 17), conjuntos
  representativo y de estrés, análisis de errores, puntos de operación y componente de D-14.
- [02](02_Plan.md): preguntas a organizadores en F0, F4 según D-14, prueba de capacidad en F5, demo que
  muestra trazas, reintentos y caída segura; *streaming* opcional.
- [03](03_Datos_por_capas.md): ruta operativa contra ruta analítica y vigilancia del bucket.
- [00](00_Principios.md): P11 cubre el repositorio público y las solicitudes externas.
- [Investigación 13](../Investigacion/13_Auditoria_del_dataset.md): segunda pasada con la sección 3.
- Investigaciones 14 y 15: notas fechadas.
- [Decisiones](../../presidencia/decisiones.md): D-14, D-15 y D-16 propuestas; D-09 en revisión.
