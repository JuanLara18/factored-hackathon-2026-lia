# Plan de trabajo (borrador 2)

**Nota del 26 de septiembre de 2026:** las fases y compuertas de este documento siguen vigentes; el
backlog por cara, la ruta crítica, el calendario y el orden de recorte están en
[07_Hoja_de_ruta.md](07_Hoja_de_ruta.md), y la arquitectura y la tecnología decidida en
[06_Arquitectura.md](06_Arquitectura.md). Con la decisión de dos canales (D-17), F3 construye el
núcleo y el chat, y la nueva **F3v** agrega la voz sobre el mismo núcleo.

**Reglas del plan:** se rige por [00_Principios.md](00_Principios.md). Cada fase tiene entregables
y una **compuerta de salida**: no se pasa a la siguiente sin cumplirla. Si el tiempo aprieta se
recorta **alcance** (escenarios, idiomas, pulido), nunca una compuerta ni un principio. Las
decisiones van al [registro](Decisiones.md).

**Horizonte:** diez días desde el arranque oficial (fechas por confirmar). Los días se cuentan
relativos: **D0** es la preparación antes del arranque, **D1 a D10** los días de la competencia.

**Orden que no se altera:** evidencia → especificación → construcción → endurecimiento →
evaluación → entrega. La evaluación se diseña al principio y se corre al final.


> **Nota del 27 de septiembre de 2026 (Auditoría, H-AUD-22):** la sección F5 dice S1 a S9 y Apigee con Model Armor; vigentes son S1 a S10 y V1 a V11, y el gateway de D-28 (LiteLLM con Presidio y Model Armor).

---

## Vista general

| Fase | Días | Qué produce | Compuerta de salida | Principios que verifica |
|---|---|---|---|---|
| **F0 Preparación** | D0 | reglas confirmadas, repositorio, datos locales, entorno | se levanta el entorno con un comando | P11, P13 |
| **F1 Evidencia** | D1 a D2 | EDA, auditoría del dataset sintético, flujo elegido | decisión de flujo **firme** con datos | P8, P10 |
| **F2 Especificación** | D2 a D3 | política versionada, contratos de datos, conjuntos de evaluación, líneas base | **retenido congelado** y línea base medida | P1, P2, P9 |
| **F3 Núcleo y chat** | D3 a D4 | pipeline de datos, servicios simulados, dominio tipado, motor de flujo, comprensión, redacción, traspaso, trazas, chat con AG-UI | camino normal (N1 a N6) de punta a punta en ES por chat | P4, P5, P6, P7, P13 |
| **F3v Voz** | D5 | superficie de voz en cascada sobre el mismo núcleo (D-18) | los mismos casos por voz en ES, dentro del presupuesto de latencia | P4, P6, P13 |
| **F4 Componente aprendido** | D4 a D6 (paralelo) | comprensión de la recepción (D-14) contra líneas base; experimento de riesgo reportado | reporte del componente sin fuga, con análisis de errores | P9, P10 |
| **F5 Endurecimiento** | D6 a D8 | fallas, adversariales, gateway y filtros, portugués, pruebas de propiedades | todos los escenarios del catálogo corren en desarrollo | P5, P6, P11, P12 |
| **F6 Evaluación** | D8 a D9 | corridas sobre el retenido, reportes | criterios de salida evaluados (cumplidos o reportados como no cumplidos) | P1, P2, P3, P12 |
| **F7 Entrega** | D9 a D10 | demo ES/PT, reporte, video o presentación, ruta a producción | entrega enviada | P3, P13 |

**Holgura:** medio día en D5 y medio en D9. Si no se usan, van a F5.

---

## F0 · Preparación (D0)

**Objetivo:** que el D1 se dedique a los datos, no a instalar cosas.

- [ ] Enviar a los organizadores las ocho preguntas de [05](05_Cobertura_del_enunciado.md),
      sección 4 (fechas, equipo, datos en modelos externos, repositorio público, términos de uso,
      entregas incrementales, recursos externos, créditos). Hasta tener respuesta rige D-15.
- [ ] Crear el repositorio fuera del Drive (D-03) con `.gitignore` para `data/`, `.env` y
      credenciales. Verificar que la llave de AWS **no** entre a git.
- [ ] Configurar AWS CLI con la llave de solo lectura (en `~/.aws/credentials`, nunca en el
      repositorio) y listar el bucket.
- [ ] Bajar primero las tablas pequeñas y una muestra de las grandes; sincronizar las grandes en
      segundo plano.
- [ ] Entorno reproducible: `uv` con dependencias fijadas, `Makefile` o `justfile` con
      `setup`, `data`, `test`, `eval`, `demo`.
- [ ] Esqueleto de repositorio (ver al final).

**Compuerta:** otra persona (o una máquina limpia) clona, corre `setup` y abre una consulta sobre
una tabla.

## F1 · Evidencia (D1 a D2)

**Objetivo:** decidir el flujo con datos y saber qué se puede creer del dataset.

**Estado:** adelantado sobre una muestra ([investigación 13](../Investigacion/13_Auditoria_del_dataset.md)):
auditoría sintética, calidad y cobertura lingüística hechas; falta confirmarlas sobre el total con la
capa bronce ([03](03_Datos_por_capas.md)) y el EDA de negocio sobre plata.

1. **Ingesta y calidad** con DuckDB: conteos por tabla contra el diccionario, duplicados, nulos,
   huérfanos de llaves foráneas, particiones tardías. Primer borrador de contratos.
2. **Motivos de contacto:** volumen de `contact_reason` y `reason_category` por país, canal y mes;
   FCR, escalamiento, duración y espera por motivo; clasificación **valor o falla** (investigación 7).
3. **Disputas:** `complaints` por categoría, SLA incumplidos, reclamantes recurrentes; transacciones
   con `is_fraud`; comercios con muchas disputas de clientes distintos (punto de compromiso).
4. **Auditoría sintética** (P10): ¿el texto de las transcripciones es plantilla de la etiqueta?
   (TF-IDF más regresión logística y sus palabras de mayor peso); ¿`was_resolved`,
   `was_escalated` e `is_fraud` tienen señal?; ¿las columnas detectadas son la respuesta?
5. **Cobertura lingüística:** `detected_accent`, `detected_language`; confirmar ausencia de portugués.

**Entregables:** notebook o reporte de EDA con figuras; lista de limitaciones de los datos; D-02
pasa a **provisional o se reemplaza**.

**Compuerta:** el flujo elegido tiene respaldo cuantitativo en el dataset y se sabe qué etiquetas
sirven para el componente aprendido (y cuáles no).

## F2 · Especificación (D2 a D3)

**Objetivo:** dejar fijo contra qué se va a medir, antes de construir el sistema (P1).

1. **Política sintética versionada** (`policy/v1`): motivos y su categoría (10.x, 12.x, 13.x, no lo
   recuerda), evidencia requerida, plazos por país con su norma, umbral de monto, qué acciones
   requieren confirmación y qué autenticación, criterios de urgencia y de escalamiento. Etiquetada
   como **sintética**.
2. **Contratos de datos** en ODCS para las tablas que usa el flujo, con sus chequeos.
3. **Conjuntos de evaluación:**
   - casos semilla desde el dataset para cada escenario del catálogo;
   - casos adversariales escritos a mano;
   - casos en portugués;
   - etiqueta completa por caso (ruta esperada, estado final, acciones prohibidas, idioma,
     variante, segmento, versión de política);
   - división **desarrollo / retenido**; el retenido se guarda con su huella (hash) y queda
     congelado.
4. **Usuario simulado** con personas (tono, variante, paciencia) y herramientas mockeadas.
5. **Líneas base** corridas sobre los mismos casos: reglas y palabras clave; LLM de un solo prompt;
   y las métricas históricas del motivo como contexto de negocio.
6. **Umbrales**: se fijan los provisionales de D-07 con la línea base a la vista.

**Compuerta:** retenido congelado, línea base medida con los criterios del documento 01, umbrales
fijados y registrados.

## F3 · Núcleo (D3 a D6)

**Objetivo:** el camino normal funcionando de punta a punta, con la arquitectura correcta desde el
primer día (no se "agrega seguridad después").

Orden de construcción (cada pieza con sus pruebas):

1. **Pipeline de datos** incremental e idempotente, con contratos, deduplicación, ventana de llegada
   tardía, manifiesto por corrida y el *fixture* de actualización.
2. **Servicios simulados** con contrato documentado, nombrados como dominios BIAN: identidad
   (sesión con expiración, OTP simulado), cuentas y transacciones (lectura), tarjetas (bloqueo),
   casos (radicar, consultar), política.
3. **Modelo de dominio tipado:** `SesionAutenticada`, `CustomerId`, `Money`, `CargoPropio`,
   `Confirmacion`, `HechoVerificado`, `ReglaDePolitica`, `Interpretacion`, `PaqueteTraspaso`.
4. **Capa de herramientas** que exige esos tipos (P5), idempotente, con *timeout* y reintento
   acotado.
5. **Motor de flujo** con los estados del documento 01 y la tabla de política.
6. **Comprensión** con salida tipada (intención, entidades, aclaración, idioma).
7. **Redacción** que solo recibe hechos verificados y reglas (P6); *streaming* opcional (el enunciado
   no lo exige).
8. **Traspaso** con el paquete completo y la vista para el agente humano.
9. **Trazas** OpenTelemetry por conversación y registro de ejecución.

**Compuerta:** N1 a N6 pasan en español en el conjunto de desarrollo; verificación estática estricta
sin errores; la traza de cada caso muestra la secuencia de estados.

## F4 · Componente aprendido (D4 a D6, en paralelo)

1. **Comprensión de la recepción** (D-14): motivo, urgencia y entidades desde el mensaje del cliente,
   con conversaciones del equipo etiquetadas desde una ruta conocida y auditadas contra plantillas.
   Palabras clave y TF-IDF con regresión logística como base; embeddings multilingües o SetFit y LLM
   sin ajuste como comparados. Calibración, curva de riesgo y cobertura, ES → PT y **análisis de
   errores**.
2. **Experimento de riesgo de la transacción**, reportado como resultado: con partición temporal, con
   y sin `fraud_score`, confirmando sobre el total lo que mostró la muestra (sin señal fuera del
   puntaje). `fraud_score` entra a la política como regla determinista.
3. Solo si ganan con claridad, algo más sofisticado (P9).

**Compuerta:** reporte del componente con su línea base, sin fuga demostrada, integrado al flujo.

## F5 · Endurecimiento (D6 a D8)

1. Escenarios de ambigüedad, escalamiento, fuera de alcance, fallas y datos malos (A, E, F, D).
2. Escenarios de seguridad (S1 a S9) y **pruebas de propiedades** de los invariantes.
3. **Gateway**: Apigee con Model Armor si está disponible; si no, LiteLLM con Model Armor por API o
   un gateway mínimo documentado como sustituto (investigación 10). Cuotas, redacción de datos
   personales, costo por solicitud. Medir qué detecta el filtro y qué contiene la arquitectura.
4. **Portugués** y variantes (L1 a L4).
5. Presupuesto de latencia: medir por span y aplicar las palancas de la investigación 11.
6. **Prueba de capacidad:** usuarios simulados concurrentes contra el sistema completo; se reporta el
   punto donde el p95 sale del presupuesto y el cuello de botella (límites de tasa del LLM, base
   operativa, CPU). DuckDB queda en la ruta analítica; sesiones, estado y casos van a una base
   operativa (SQLite o Postgres).

**Compuerta:** todo el catálogo corre en desarrollo; los invariantes pasan con miles de ejemplos
generados.

## F6 · Evaluación (D8 a D9)

1. Congelar la versión candidata (modelo, prompts, política, código).
2. Correr el retenido con k repeticiones: sistema y líneas base.
3. Calcular todas las métricas del documento 01 con intervalos; McNemar contra la mejor línea base.
4. Validar el juez LLM sobre la muestra humana (si se usó).
5. Tabla de equidad por idioma, variante y segmento.
6. Evaluar los **criterios de salida**; lo que no se cumpla **se reporta**, no se esconde.

**Compuerta:** reporte de evaluación completo, con fallas.

## F7 · Entrega (D9 a D10)

1. **Demo** con los tres casos obligatorios (normal, ambiguo o no soportado, humano) en español y
   portugués, más un ataque contenido y una falla segura, **mostrando** la traza de una conversación,
   un reintento acotado y la caída segura (el enunciado pide demostrarlos).
2. **Reporte** con: el problema respaldado por datos, la arquitectura y sus decisiones, la
   evaluación (medido / simulado / proyectado), la seguridad, la equidad, el costo y la latencia, y
   **lo que falta para producción** con honestidad.
3. README del repositorio que reproduce todo con un comando.
4. Revisión final contra la matriz de trazabilidad del documento 01.

---

## Frentes de trabajo

Los frentes son las vicepresidencias de LATAM Bank ([04_Organizacion_y_roles.md](04_Organizacion_y_roles.md)):
quién lidera y quién firma cada fase está en su sección 7. La regla se mantiene: la **evaluación** la
lleva Gobierno, no quien construye el núcleo (P1).

## Riesgos

| Riesgo | Señal | Mitigación |
|---|---|---|
| La capa de servicio del dataset es plantilla (**materializado** en la muestra) | investigación 13 | casos anclados en transacciones; componente aprendido D-09; se reporta como limitación |
| El motivo elegido no pesa en el dataset | EDA de F1 | en la muestra pesa (18% de las quejas); confirmar sobre el total |
| Descarga de 19 millones de filas lenta | F0 | empezar por muestras; las tablas grandes en segundo plano |
| Apigee no disponible | F0 | sustituto documentado (investigación 10) |
| No hay tiempo para todo el catálogo | F5 | recortar escenarios de menor riesgo, **nunca** los de seguridad ni R4 |
| Latencia fuera de presupuesto | F5 | menos llamadas al LLM, modelo pequeño, caché de prompt |
| Tentación de ajustar sobre el retenido | F5 y F6 | retenido con huella, lo corre el frente de evaluación |
| El juez LLM no concuerda con humanos | F6 | limitar el juez a lo no determinista; reportar κ |

## Tecnología propuesta (superada)

**Superada por las decisiones D-11 y D-17 a D-21 y por [06_Arquitectura.md](06_Arquitectura.md),
sección 2.** Se conserva la tabla original como registro.

| Pieza | Propuesta | Alternativa |
|---|---|---|
| Datos | DuckDB (+ dbt opcional), Pandera o Soda, contratos ODCS | Polars |
| Dominio y tipos | Pydantic v2, pyright o mypy estricto | |
| Agente | PydanticAI con motor de flujo propio | LangGraph, Google ADK |
| LLM | por decidir según reglas y créditos; uno pequeño y rápido para comprensión, uno mejor para redacción si hace falta | |
| Clasificador | scikit-learn, SetFit, embeddings multilingües | |
| Grafo | NetworkX o Kùzu embebido | Neo4j |
| Gateway y filtros | Apigee + Model Armor | LiteLLM + Model Armor o Presidio |
| Trazas | OpenTelemetry con Langfuse o Phoenix | Logfire |
| Pruebas | pytest, Hypothesis | |
| Demo | interfaz web simple de chat más vista de agente | Streamlit, Chainlit |

Se decide en F0 y F1 y se registra en [Decisiones.md](Decisiones.md).

## Esqueleto del repositorio (superado)

**Superado por [06_Arquitectura.md](06_Arquitectura.md), sección 8**, que agrega canales, subagentes y
evaluación de voz.

```
factored-hackathon-2026/
├── README.md              ← un comando para todo
├── pyproject.toml, uv.lock
├── justfile               ← setup, data, test, eval, demo
├── .claude/agents/        ← las caras de Gobierno y Auditoría como subagentes
├── contracts/             ← ODCS por tabla
├── dominios/              ← mapeos de valores crudos a canónicos, versionados
├── policy/v1/             ← política sintética versionada
├── data/                  ← fuera de git
├── src/
│   ├── pipeline/          ← ingesta, calidad, incremental, manifiesto
│   ├── domain/            ← tipos: sesión, dinero, hechos, confirmación, traspaso
│   ├── services/          ← identidad, cuentas, tarjetas, casos (simulados, dominios BIAN)
│   ├── tools/             ← capa de herramientas tipada
│   ├── flow/              ← motor de estados y tabla de política
│   ├── nlu/               ← comprensión y clasificador
│   ├── graph/             ← señal de punto de compromiso
│   ├── respond/           ← redacción anclada
│   ├── handoff/           ← paquete y vista del agente
│   └── gateway/           ← cuotas, filtros, redacción de datos personales
├── eval/
│   ├── cases/dev/  cases/holdout/ (congelado, con hash)
│   ├── simulator/         ← usuario simulado
│   ├── baselines/
│   ├── metrics/           ← las del documento 01
│   └── reports/
└── tests/                 ← unitarias y de propiedades
```
