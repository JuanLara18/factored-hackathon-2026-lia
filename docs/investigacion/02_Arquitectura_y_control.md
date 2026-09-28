# Investigación 2: arquitectura, autonomía y traspaso a humanos

**Pregunta:** ¿cómo se reparte el trabajo entre el modelo de lenguaje, la lógica determinista y el
humano? El enunciado pide exactamente eso: *"Justify where AI is appropriate, where deterministic
logic is preferable"*, *"Enforce permissions and policy outside model-generated prose"* y un
traspaso con *"request, verified facts, actions taken, supporting evidence, and unresolved
questions"*.

**Hallazgo central:** la literatura seria y la industria convergen en el mismo patrón: **el LLM
entiende y redacta; el código decide y actúa**. La autonomía total de un agente es el extremo de un
espectro, y para banca casi nadie lo recomienda.

---

## 1. El espectro de autonomía

Anthropic, en [*Building Effective Agents*](https://www.anthropic.com/research/building-effective-agents),
separa **flujos de trabajo** (el LLM y las herramientas se orquestan por rutas de código
predefinidas) de **agentes** (el LLM decide su propio proceso y qué herramientas usar). Sus
patrones de flujo, de menor a mayor autonomía: llamada única con recuperación, **encadenamiento**,
**enrutamiento**, paralelización, orquestador y trabajadores, evaluador y optimizador. Su consejo:
empezar por lo más simple y subir solo si hace falta, porque cada paso de autonomía cambia
predictibilidad por flexibilidad.

| Nivel | Qué decide el LLM | Qué decide el código | Ejemplo |
|---|---|---|---|
| 0. Clasificador | la intención | todo lo demás | NLU clásico, Erica original |
| 1. **Lenguaje separado de la lógica** | intención, entidades, redacción | **el flujo, las reglas, las acciones** | **Rasa CALM**, Nubank |
| 2. Agente con herramientas acotadas | qué herramienta llamar y cuándo | permisos por llamada, validación, confirmación | demo de OpenAI, τ-bench |
| 3. Agente autónomo | todo | casi nada | no recomendado en banca |

**Rasa CALM** ([documentación](https://rasa.com/docs/learn/concepts/calm/)) es la formulación más
limpia del nivel 1: el LLM traduce lo que dice el cliente a **comandos** ("iniciar el flujo de
disputa", "fijar monto = 350.000"), y un motor determinista ejecuta **flujos versionados** paso
a paso. *"El LLM mantiene la conversación fluida pero no adivina la lógica de negocio."* Es
auditable por construcción: cada acción sale de un paso del flujo, no del texto del modelo.

**Nubank** ([arXiv 2606.08867](https://arxiv.org/abs/2606.08867)) llega a lo mismo desde el lado
agéntico: *rutinas* que traducen los procedimientos humanos, orquestación determinista **en código,
no en el prompt**, herramientas idempotentes, y "reservar el razonamiento del LLM para decisiones
que de verdad lo requieren".

**La demo de OpenAI** ([openai-cs-agents-demo](https://github.com/openai/openai-cs-agents-demo))
usa un **agente de triaje** que enruta a especialistas (reservas, asientos, estado, cancelación,
FAQ) y dos **guardarraíles de entrada**: relevancia (fuera de dominio) y *jailbreak*. Sirve de
esqueleto, pero sus guardarraíles son otros LLM clasificando, no autorización real.

## 2. Por qué no dejar que el agente decida solo

Tres resultados de investigación que justifican la separación con números:

- **Los LLM se pierden en conversaciones de varios turnos.** [Laban et al., ICLR 2026](https://arxiv.org/abs/2505.06120):
  15 modelos punteros, 200.000 conversaciones simuladas, **caída media de 39%** al pasar de una
  instrucción completa a una que se aclara por turnos. La causa no es falta de capacidad sino
  **pérdida de confiabilidad**: el modelo responde antes de tener toda la información, asume, y
  cuando se equivoca no se recupera. **Implicación directa:** el estado de la conversación
  (qué datos faltan, qué ya se confirmó) debe vivir en una estructura explícita, no en el
  historial del chat, y el sistema debe **preguntar antes de actuar** cuando falten datos.
- **Los agentes de CRM no saben guardar secretos.** [CRMArena-Pro, Salesforce](https://arxiv.org/abs/2505.18878):
  ~58% de éxito en un turno y **35% en varios turnos**; **confidencialidad casi nula** de forma
  nativa, y cuando se les instruye para protegerla, baja el desempeño en la tarea. **Implicación:**
  la protección de datos no puede depender de que el modelo "se acuerde"; los datos que no debe
  ver no deben llegarle.
- **Los *frameworks* de agentes no autorizan, solo exponen herramientas.** [*Capability Gates Are
  Not Authorization*, 2026](https://arxiv.org/abs/2606.28679): LangChain y LangGraph, LlamaIndex y
  el Stripe Agent Toolkit **fallan por defecto** la prueba de autorización: dar acceso a una
  herramienta no equivale a autorizar cada llamada con sus argumentos concretos. Su control
  (ScopeGate) valida **por llamada**: alcance, autorización, límites de monto, idempotencia y
  **negación por defecto**. Con eso: 0 de 29 intentos no autorizados pasaron.

## 3. Identidad y permisos: el problema del "delegado confundido"

El enunciado: *"a national ID or customer number alone does not prove identity"* y *"enforce
access to each customer's records and action permissions in the service or tool layer"*.

El patrón que describe la literatura de 2026
([guía de Arcade](https://dev.to/arcade/how-to-manage-multi-user-ai-agent-authentication-and-authorization-in-2026-oauth-21-oidc-and-2943),
[Obsidian](https://www.obsidiansecurity.com/academy/ai-agent-credential-management)):

- **OIDC autentica al humano; OAuth autoriza al agente** a actuar en su nombre. Mezclarlos crea
  tokens reutilizables y demasiado amplios.
- Cada llamada lleva **tres identidades**: la del agente, la del cliente autenticado y la de la
  tarea, con **alcance, audiencia y expiración cortos**.
- **Las credenciales nunca entran a la ventana de contexto** del modelo.
- **El agente no elige de quién son los datos.** El `customer_id` sale de la sesión autenticada, no
  de un argumento que el modelo escribe. Si el cliente dice "muéstrame la cuenta de mi esposa", la
  herramienta ni siquiera acepta ese parámetro.

**Para el prototipo:** un servicio de identidad simulado que emite una sesión de prueba con
expiración (el enunciado pide probar **sesiones expiradas**), y una capa de herramientas que lee el
cliente **de la sesión** y rechaza todo lo demás. Autenticación reforzada (*step-up*, un OTP
simulado) antes de acciones sensibles como bloquear una tarjeta o radicar una disputa.

## 4. Qué pide confirmación y qué se abstiene

El enunciado pide definir tres conjuntos: **qué responde el sistema solo**, **qué acciones
requieren confirmación** y **cuándo se abstiene o transfiere**. Una tabla de política explícita,
en código, es el artefacto que lo demuestra:

| Tipo de solicitud | Ejemplo | Tratamiento |
|---|---|---|
| Información general | horarios, qué es un contracargo | responde con fuente (política o FAQ recuperada) |
| Consulta de datos propios | últimos movimientos, estado de un reclamo | responde tras autenticación, **solo con datos verificados de la herramienta** |
| Acción reversible de bajo riesgo | bloqueo temporal de tarjeta | **confirmación explícita** del cliente, luego acción, luego verificación del resultado |
| Acción con efecto financiero | radicar una disputa por un monto | autenticación reforzada, confirmación, acción idempotente |
| Fuera de alcance o ambiguo tras aclarar | pedir un crédito en un flujo de disputas | **abstenerse** y explicar qué sí puede hacer |
| Alto riesgo o sensible | fraude en curso, amenaza, cliente vulnerable, montos altos | **transferir** con contexto |

**"Reportar solo acciones cuyo resultado el sistema verificó"**: después de cada acción, el sistema
consulta el estado (el reclamo existe, la tarjeta está bloqueada) y solo entonces lo dice. Si la
herramienta falla, lo dice como falla, nunca "listo".

## 5. El traspaso a humano

Lo que coincide entre la industria ([Haptik](https://www.haptik.ai/blog/warm-transfer-escalation-design-between-ai-human-agents),
[Cresta](https://cresta.com/guides/ai-to-human-agent-handoff-best-practices),
[Replicant](https://www.replicant.com/blog/when-to-hand-off-to-a-human-how-to-set-effective-ai-escalation-rules))
y el enunciado:

**Disparadores en tres capas:**
1. **Por regla:** el cliente pide un humano, la intención no se captura tras N intentos, palabras de
   alto riesgo.
2. **Por sentimiento:** frustración creciente.
3. **Por política:** cumplimiento, montos, tipos de caso que la norma reserva a personas.

Más uno del lado del modelo: **baja confianza** (Nubank).

**Paquete de traspaso**, el formato que pide el enunciado:

| Campo | Contenido | Origen |
|---|---|---|
| Solicitud | la intención y el pedido del cliente en sus palabras | conversación |
| **Hechos verificados** | identidad, producto, transacción, montos | **herramientas**, marcados como verificados |
| Acciones realizadas | qué se hizo y su resultado verificado | registro de ejecución |
| Evidencia | las fuentes y registros que respaldan cada hecho | trazas |
| Preguntas abiertas | lo que falta decidir o aclarar | estado del flujo |
| Motivo del traspaso | qué disparador y por qué | política |

La recomendación más útil: **separar visualmente lo confirmado de lo interpretado por la IA**, para
que el agente humano no confíe a ciegas en un resumen incierto.

**Cómo medir el traspaso** (además de lo que pide el enunciado sobre transferencias faltantes e
innecesarias): **tasa de repetición** (cuántas veces el cliente repite lo que ya dijo), tiempo hasta
resolución después del traspaso, y la satisfacción de los transferidos frente a los no transferidos.
Un sistema que escala el 40% con traspasos completos puede ser mejor que uno que escala el 20% en
frío.

## 6. La arquitectura que sale de todo esto

```
Cliente (ES/PT)
   │
   ▼
[Canal] ──► [Sesión e identidad simuladas]  ← expiración, step-up
   │
   ▼
[Comprensión: LLM]  → intención, entidades, idioma, necesidad de aclarar
   │                   (salida estructurada, nunca acciones)
   ▼
[Motor de flujo determinista]  ← estado explícito, tabla de política
   │         │            │
   │         │            └──► [Traspaso a humano con paquete]
   │         ▼
   │   [Capa de herramientas]  ← autorización por llamada, customer_id de la sesión,
   │                             idempotencia, reintentos acotados, verificación
   ▼
[Redacción: LLM]  → respuesta anclada solo en hechos verificados y fuentes
   │
   ▼
[Trazas y registro de ejecución]  ← la explicación auditable, no el razonamiento del modelo
```

**Dónde entra lo aprendido** (el enunciado exige al menos un componente evaluado contra una línea
base): el clasificador de intención o de motivo de contacto, el predictor de escalamiento o el
recuperador de políticas. Se desarrolla en la investigación 5.

## 7. Decisiones que quedan abiertas

1. **Nivel 1 o nivel 2** de autonomía. El nivel 1 (CALM) es más fácil de defender; el 2 muestra más
   "IA". Posible punto medio: flujo determinista para la ruta principal y agente con herramientas
   de solo lectura para preguntas abiertas.
2. **Framework:** LangGraph (estados e interrupciones para confirmación humana), Rasa CALM (flujos
   nativos), OpenAI Agents SDK (handoffs y guardarraíles) o código propio. Todos necesitan la capa
   de autorización por llamada encima.
3. **Un agente o varios.** El enunciado dice que múltiples agentes no dan puntos; con un solo flujo,
   uno basta.

## Fuentes principales

- [Anthropic, Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Rasa CALM](https://rasa.com/docs/learn/concepts/calm/)
- [OpenAI, customer service agents demo](https://github.com/openai/openai-cs-agents-demo) y [guía práctica de agentes](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
- [Laban et al., LLMs Get Lost In Multi-Turn Conversation](https://arxiv.org/abs/2505.06120)
- [Huang et al., CRMArena-Pro](https://arxiv.org/abs/2505.18878)
- [Capability Gates Are Not Authorization](https://arxiv.org/abs/2606.28679)
- [Nubank, arXiv 2606.08867](https://arxiv.org/abs/2606.08867)
