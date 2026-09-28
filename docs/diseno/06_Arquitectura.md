# Arquitectura de la solución (v1)

**Propósito:** reunir en un solo lugar la arquitectura que salió de las investigaciones y del
[registro de decisiones](Decisiones.md), para desarrollar desde aquí. Cada componente dice qué hace,
quién es dueño ([organización v2](04_Organizacion_y_roles.md)), si es IA o lógica determinista y por
qué, y con qué se construye. El enunciado pide justificar *"where AI is appropriate, where deterministic
logic is preferable"*: la sección 3 es esa justificación.

---

## 1. Un núcleo, dos superficies

```
 Cliente por chat (web; semántica de WhatsApp)        Cliente por voz (navegador; teléfono opcional)
              │ eventos AG-UI                                        │ audio
              ▼                                                      ▼
   [Superficie de chat]                                 [Superficie de voz]
   componentes tipados, aprobaciones,                   cascada: VAD y detección de turno,
   degradación a botones y listas                       reconocimiento en streaming, síntesis
                                                        en streaming, interrupciones, rellenos,
                                                        DTMF   (experimento: frontend nativo)
              └──────────────────────┬──────────────────────────────────┘
                                     ▼  TurnoEntrante (texto, canal, idioma, confianza, DTMF)
                    [Gateway de IA]  cuotas, costo, filtros de entrada y salida, redacción de PII
                                     ▼
                    [Motor de flujo determinista]  ◄──► [Estado durable: Postgres, idempotencia]
                      │           │            │
          [Comprensión]     [Política v1]   [Herramientas tipadas] ──► [Servicios simulados BIAN]
          aprendida y       YAML con norma   SesionAutenticada,          │
          calibrada         y PDP con        Confirmacion,               ├─► oro operacional (DuckDB, AS_OF)
                            registro         verificación posterior      └─► [Identidad: acr, OTP, reloj]
                      │
          [Redacción]  desde HechoVerificado; plantillas para lo crítico
                      │
          [Traspaso]   paquete tipado ─► cola humana (idioma, turno, especialidad) ─► vista del experto
                                     │
                    [Trazas OpenTelemetry] ─► Phoenix ─► platino (resultados, métricas, linaje)
```

Ninguna superficie decide nada: traducen entre el cliente y el núcleo. Por eso un caso empezado en chat
se retoma por voz en el mismo estado (investigación 20, sección 6).

## 2. Componentes

| # | Componente | Qué hace | Dueño | Tecnología | Decisión |
|---|---|---|---|---|---|
| 1 | Superficie de chat | renderiza componentes, emite aprobaciones, simula ventana de 24 h y plantillas | Tecnología (Canales) | AG-UI (SDK de Python) y frontend web | D-19 |
| 2 | Superficie de voz | audio a texto y texto a audio, turnos, interrupciones, rellenos, DTMF | Tecnología (Canales) e IA (Voz) | Pipecat; proveedores de reconocimiento y síntesis elegidos por medición | D-18 |
| 3 | Frontend nativo de audio (experimento) | conversación de audio a audio que delega en el motor con una sola herramienta | IA (Voz) | gpt-realtime o Gemini Live | D-18 |
| 4 | Gateway de IA | cuotas, costo por solicitud, enrutamiento de modelos, filtros, redacción | Tecnología y Gobierno | LiteLLM; Presidio con reconocedores de CURP, CC y DNI; Model Armor si hay Google Cloud | D-20 |
| 5 | Motor de flujo | estados, transiciones tipadas, elige la ruta y la acción | Tecnología (Plataforma) | Python, Pydantic v2 | D-11 |
| 6 | Estado durable | conversación, sesión, casos, llaves de idempotencia, retoma entre canales | Tecnología (Plataforma) | Postgres (SQLite en pruebas) | D-20 |
| 7 | Comprensión | motivo, urgencia, entidades, fuera de alcance, idioma | IA (Comprensión) | clasificador aprendido (base TF-IDF; comparados embeddings o SetFit y LLM con PydanticAI) | D-14 |
| 8 | Política | plazos por país, umbrales, matriz de autonomía, confirmaciones, regla de riesgo | Gobierno define, Tecnología ejecuta | YAML versionado con norma y fecha; punto de decisión propio que registra cada decisión | D-13, D-20 |
| 9 | Capa de herramientas | autorización por tipos, idempotencia, *timeouts*, reintentos acotados, verificación posterior | Tecnología (Plataforma) | Python tipado, pyright estricto, Hypothesis | D-05 |
| 10 | Servicios simulados | cuentas y transacciones (lectura), tarjetas (bloqueo), casos (radicar, consultar), fraude (puntaje) con nombres BIAN | Tecnología (Plataforma) | FastAPI sobre oro operacional | D-11 |
| 11 | Identidad | sesión con niveles `acr`, OTP simulado, expiración, reloj inyectable | Tecnología (Plataforma) | JWT propio con la forma de RFC 9470 | D-20 |
| 12 | Ficha de la transacción | comercio, categoría, fecha y hora del evento, monto, moneda, estado, compras previas | Datos y Clientes | oro operacional más directorio de comercios del equipo, declarado | inv. 14 |
| 13 | Redacción | la respuesta al cliente | IA (Comprensión y redacción) | PydanticAI con entrada tipada; plantillas para lo crítico | P6 |
| 14 | Traspaso | paquete tipado (hechos, interpretaciones, conflictos, acciones, preguntas) y cola | Clientes y Tecnología | render desde el objeto | inv. 14 |
| 15 | Vista del experto | ver el paquete, actuar, corregir el motivo (etiqueta) | Clientes (Operaciones) | web | inv. 14 |
| 16 | Datos | ruta analítica bronce a platino; ruta operativa oro a servicios | Datos | DuckDB, dbt con DuckDB, Data Contract CLI, Parquet | D-08, D-21 |
| 17 | Evaluación | arnés, simuladores de texto y voz, juez validado, métricas oficiales | IA (arnés), Gobierno (contenido y corrida), Datos (métricas) | pytest, Hypothesis, simulador propio, síntesis por locale | D-16, D-18 |
| 18 | Observabilidad | trazas por turno y etapa, latencia, costo | Tecnología (SRE) | OpenTelemetry, Phoenix local | D-20 |

## 3. Dónde va la IA y dónde la lógica determinista

**Regla:** la IA está donde hay **lenguaje o audio**; la lógica determinista, donde hay **dinero,
derechos o permisos**.

| Tarea | Quién la hace | Por qué |
|---|---|---|
| Entender lo que dice el cliente (motivo, urgencia, entidades) | **IA** | lenguaje libre en cuatro variantes del español y en portugués, con modismos y errores de reconocimiento; ninguna regla lo cubre; la salida es tipada, calibrada y con umbral para aclarar |
| Reconocer y sintetizar voz; detectar el fin del turno | **IA** preentrenada | es percepción; se elige y se mide por acento |
| Redactar lo abierto (explicar, empatizar, registro regional) | **IA** | solo desde hechos verificados (P6) |
| Decidir la ruta, la acción y el escalamiento | **Determinista** | decisiones reguladas, auditables y repetibles (P4); el enunciado exige la política fuera del texto del modelo |
| Plazos, umbrales, qué requiere confirmación | **Determinista** | es norma; el modelo no inventa reglas (caso Air Canada, P6) |
| Autorizar cada llamada | **Determinista** por tipos | la seguridad no puede depender del modelo (P5) |
| Ubicar la transacción | **Determinista** | con una mediana de 2 transacciones por cliente en dos meses, los filtros bastan (revisión 05) |
| Riesgo de fraude de la transacción | **Determinista** (`fraud_score` > 30, zona gris con humano) | no hay señal aprendible fuera del puntaje; lo honesto es una regla con revisión humana |
| Montos, plazos, confirmaciones, lectura de vuelta | **Plantilla determinista** | el error de redacción aquí es un resultado materialmente incorrecto |
| Armar el traspaso | **Determinista** | se renderiza desde el estado tipado; menos información falsa que un resumen libre (investigación 14) |
| Juzgar la calidad de lo no verificable (tono, claridad) | **IA** validada | solo donde no hay verificación determinista, con κ contra humanos (investigación 4) |

## 4. Un turno por dentro

**Chat:**
1. El cliente escribe; la superficie envía un `TurnoEntrante`; el gateway filtra y redacta PII; el motor
   carga el estado.
2. Comprensión devuelve una `Interpretacion` tipada con confianza.
3. El motor aplica la política: si la confianza es baja, aclara; si hay urgencia, escala; si hace falta
   un dato, llama a una herramienta.
4. Cada herramienta devuelve `HechoVerificado` con fuente y hora; si la acción requiere confirmación, el
   motor emite un componente de aprobación con el monto leído de la base.
5. La redacción (o la plantilla) produce la `RespuestaTipada`; el filtro de salida la revisa por frases
   antes de enviarla en streaming.
6. El estado se persiste con su llave de idempotencia y la traza se cierra.

**Voz (mismo núcleo, diferencias):**
- El reconocimiento en streaming y la detección de turno producen el `TurnoEntrante` con la **confianza
  del reconocimiento**; confianza media en un dato crítico obliga a confirmación explícita.
- La respuesta se sintetiza por frases; mientras corre una herramienta, un **relleno honesto** ("estoy
  revisando sus movimientos") que nunca afirma una acción.
- Se registra lo que el agente **alcanzó a decir** antes de una interrupción.
- Las acciones se confirman con **lectura de vuelta** y "sí" explícito o **DTMF**; los dígitos van por
  DTMF.
- La autenticación reforzada va por OTP (app o SMS simulado); la voz nunca autentica.

## 5. Contratos entre componentes

Los tipos que se implementan primero, porque todo lo demás se conecta por ellos:

| Tipo | Lo produce | Lo consume |
|---|---|---|
| `TurnoEntrante` (canal, texto, idioma, confianza del reconocimiento, DTMF, referencia de sesión) | superficies | gateway y motor |
| `SesionAutenticada` (cliente, nivel `acr`, expiración) | identidad | herramientas |
| `Interpretacion` (motivo, urgencia, entidades, confianza) | comprensión | motor |
| `HechoVerificado[T]` (valor, fuente, hora) | herramientas | motor, redacción, traspaso |
| `ReglaDePolitica` (id, versión, norma, fecha de consulta) | política | motor, redacción, traspaso |
| `Decision` (ruta, acción, requiere confirmación, motivo) | motor | superficies, traza |
| `Confirmacion` (acción, monto, canal, evidencia de asentimiento) | superficies | herramientas |
| `AccionVerificada` (acción, resultado releído) | herramientas | motor, redacción |
| `RespuestaTipada` (bloques de texto, componentes, marcas para voz) | redacción y plantillas | superficies |
| `PaqueteTraspaso` (solicitud, hechos, interpretaciones, conflictos, acciones, preguntas, motivo, idioma, prioridad) | motor | cola humana y vista del experto |
| `EventoTraza` | todos | observabilidad y platino |

## 6. Presupuestos (provisionales, D-07)

| Qué | Objetivo |
|---|---|
| Chat, por turno | primer token < 1 s; p50 < 2 s; p95 < 5 s |
| Voz, de voz a voz, turno sin herramienta | p50 ≤ 1,0 s; p95 ≤ 2,0 s |
| Voz, turno con herramienta | relleno en ≤ 1,0 s; resultado dentro del presupuesto de la herramienta |
| Frontend nativo (experimento) | p50 ≤ 0,6 s |
| Costo por caso | tokens, minutos de reconocimiento, caracteres de síntesis, filtros y minutos humanos del traspaso |

## 7. Dónde vive cada control de seguridad

| Control | Dónde |
|---|---|
| Autorización por llamada | tipos en la capa de herramientas y punto de decisión con registro |
| Datos mínimos al modelo | servicios y gateway (redacción de PII, D-15) |
| Inyección (texto o voz) | comprensión sin herramientas; el motor decide; redacción con contexto minimizado |
| Suplantación por voz | la voz no autentica; OTP para acciones |
| Errores de reconocimiento en acciones | lectura de vuelta, confirmación explícita, DTMF |
| Fuga de PII en la salida | filtro de salida por frases |
| Secretos | fuera del repositorio y del contexto del modelo |
| Audio | no se guarda crudo por defecto; las grabaciones de evaluación con consentimiento |

## 8. Esqueleto del repositorio

```
factored-hackathon-2026/
├── README.md, pyproject.toml, uv.lock, justfile, docker-compose.yml (Postgres, Phoenix)
├── .claude/agents/        ← gobierno-riesgo-modelo, gobierno-seguridad, gobierno-cumplimiento,
│                            auditoria, voz-del-cliente
├── contracts/  dominios/  policy/v1/  agentes/registro.yaml
├── data/                  ← fuera de git
├── pipeline/              ← bronce, dbt (plata, oro, platino), vigilancia del bucket, fixture
├── src/latam_bank/
│   ├── domain/            ← los tipos de la sección 5
│   ├── engine/            ← motor, estados, política, punto de decisión
│   ├── nlu/               ← comprensión
│   ├── respond/           ← redacción y plantillas
│   ├── tools/  services/  ← herramientas tipadas; servicios BIAN e identidad
│   ├── handoff/  gateway/  observability/
│   └── channels/chat/  channels/voice/   ← AG-UI; Pipecat, DTMF, experimento nativo
├── web/                   ← chat, voz en navegador, vista del experto, panel de trazas
├── eval/                  ← arnés, simuladores de texto y voz, cases/dev, cases/holdout (Gobierno),
│                            cases/adversarial, reports
└── tests/                 ← unitarias, propiedades, fixture de actualización
```

## 9. Lo que queda fuera, y por qué

| Fuera | Por qué | Dónde se menciona |
|---|---|---|
| MCP en el camino crítico | los trabajadores de lenguaje no tienen herramientas (D-12) | ruta a producción |
| Cedar | tipos más punto de decisión propio bastan (D-20) | ruta a producción |
| Biometría de voz | la voz sintética la vuelve insegura como factor único | reporte de seguridad |
| WhatsApp y teléfono reales | la semántica se simula; el teléfono es opcional | ruta a producción |
| *Streaming* de datos y tablero | la fuente es diaria; el enunciado no los exige | ruta a producción |
| MetricFlow, OpenLineage | extras si sobra tiempo (D-21) | reporte de datos |
| GNN, GraphRAG | sin señal que lo justifique (P9) | limitaciones |
