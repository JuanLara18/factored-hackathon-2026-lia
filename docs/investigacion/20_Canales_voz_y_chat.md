# Investigación 20: voz y chat en estado del arte (2026)

**Pregunta:** la presidencia decidió atender por **chat y por voz**, ambos en estado del arte. ¿Qué es
estado del arte en cada canal en 2026, cómo se hace sin romper los principios (el modelo entiende y
redacta, el código decide), qué riesgos nuevos trae la voz y cómo se evalúa?

**Hallazgo central:** la práctica de 2026 para voz en sectores regulados separa un **frontend
conversacional** (turnos, interrupciones, reconocimiento y síntesis en streaming) de un **backend que
razona y decide**. Es exactamente nuestra arquitectura: el motor de flujo es el backend y la voz es otra
superficie del mismo núcleo, como el chat. Los modelos de voz nativos (de audio a audio) avanzan muy
rápido y son más naturales, pero la cascada sigue siendo la opción por defecto donde importan la
auditoría y las herramientas. Lo más fuerte que podemos hacer es **construir la cascada y medirla
contra un frontend nativo** sobre las mismas tareas.

---

## 1. Voz: las dos arquitecturas

| Arquitectura | Cómo funciona | Latencia típica hasta el primer audio | Fortalezas | Debilidades |
|---|---|---|---|---|
| **Cascada** | reconocimiento de voz en streaming, luego LLM, luego síntesis en streaming | 600 a 1.200 ms (100 a 300 reconocimiento, 200 a 600 LLM, 75 a 300 síntesis, 50 a 200 red) | trazas por etapa, cada falla se atribuye a su componente, se cambia un proveedor sin tocar el resto, herramientas maduras | latencia acumulada; la prosodia se pierde en el texto intermedio |
| **Nativa (audio a audio)** | un solo modelo recibe y emite audio | 300 a 500 ms | la más natural y rápida | caja negra para depurar, dependencia de un proveedor, llamadas a herramientas con casos borde (argumentos parciales al interrumpir, reintentos a mitad de turno) |

([FutureAGI](https://futureagi.com/blog/cascaded-voice-ai-vs-speech-to-speech-2026/),
[AssemblyAI](https://www.assemblyai.com/blog/speech-to-speech-for-voice-agents),
[Inworld](https://inworld.ai/resources/cascaded-vs-speech-to-speech-voice-architecture))

- La recomendación explícita para banca y salud en 2026 es **cascada**, con trazas por etapa y proveedor
  y modelo registrados por turno; con más de cinco herramientas y esquemas estrictos, la cascada es "el
  valor por defecto más seguro". Los equipos en producción **combinan** ambas según el caso de uso
  ([FutureAGI](https://futureagi.com/blog/cascaded-voice-ai-vs-speech-to-speech-2026/)).
- **Frontend y backend separados** ([arXiv 2609.19334](https://arxiv.org/abs/2609.19334)): el
  frontend maneja reconocimiento en streaming, turnos, interrupciones y síntesis, y **delega** en un
  backend de texto que identifica y ejecuta las herramientas; logra 92% a 97% de recuperación de
  llamadas a herramientas, rechaza 81,2% de las irrelevantes y supera a GPT-realtime-mini en EVA-Bench.
  Los autores lo presentan justamente como la forma de **auditar y controlar** las acciones sin perder
  naturalidad.

### Qué tan buenos son los agentes de voz

- **τ-voice** (Sierra, 2026): las mismas 278 tareas de τ-bench, ahora con voz en dúplex completo,
  personas con acentos, ruido ambiente y degradación telefónica (G.711, pérdida de tramas). El mejor
  agente de voz pasó de **30%** (gpt-realtime-1.0, agosto de 2025) a **67%** (grok-voice-think-fast-1.0,
  abril de 2026), por encima de los modelos de texto sin razonamiento (54%) y cerca del techo de texto
  con razonamiento (~85%): la voz conserva ya cerca del **79%** de la capacidad de texto
  ([Sierra](https://sierra.ai/blog/tau-voice-benchmarking-real-time-voice-agents-on-real-world-tasks),
  [arXiv 2603.13686](https://arxiv.org/abs/2603.13686)).
- **Full-Duplex-Bench-v3**: con audio humano real y disfluencias, GPT-Realtime lidera en éxito (0,600)
  y en evitar interrupciones indebidas (13,5%); la cascada de referencia es la más lenta
  ([arXiv 2604.04847](https://arxiv.org/abs/2604.04847)).
- **IHBench**: mide qué pasa **después** de una interrupción en flujos guiados por máquina de estados
  (retomar en el paso correcto, atender la interjección, no repetir lo ya dicho); los modelos cerrados
  ganan y no muestran brecha entre audio y texto ([arXiv 2606.19595](https://arxiv.org/abs/2606.19595)).

**Lectura:** el estado del arte de voz no es un modelo, es **una arquitectura medida**. La cascada nos
da control y auditoría; el frontend nativo nos da naturalidad; la evidencia para elegir se produce
midiendo ambos sobre las mismas tareas.

## 2. Los componentes de la cascada

### Reconocimiento de voz en streaming

- **AA-WER Streaming** (Artificial Analysis) es el primer benchmark independiente de reconocimiento en
  streaming para agentes; en su conjunto AgentTalk lidera **ElevenLabs Scribe v2 Realtime** (2,8% de
  error final), con Cartesia, ElevenLabs y Deepgram en la frontera de exactitud y latencia
  ([Artificial Analysis](https://artificialanalysis.ai/articles/new-streaming-speech-to-text-benchmark-aa-wer-streaming)).
- AssemblyAI reporta 6,99% de error para Universal-3.5 Pro Realtime frente a 15,58% de Deepgram Flux,
  9,76% de Scribe v2 y 9,04% de Chirp 3 (cifras del proveedor)
  ([AssemblyAI](https://www.assemblyai.com/blog/best-speech-to-speech-voice-agent-api)).
- **No hay cifras públicas por acento latinoamericano.** Nuestro dataset trae acentos mexicano,
  colombiano y argentino y cuatro motores de reconocimiento (Whisper v3, AWS Transcribe, Azure Speech,
  Google STT): el error por acento **lo tenemos que medir nosotros**, y es un resultado de equidad.

### Síntesis de voz

- Tiempo hasta el primer audio (benchmark de un proveedor): Gradium 155 ms, Cartesia Sonic-3 188 ms,
  ElevenLabs Turbo v2.5 264 ms, Flash v2.5 288 ms; Cartesia cubre más de 40 idiomas y ElevenLabs 32,
  ambos con español y portugués ([Gradium](https://gradium.ai/content/tts-latency-benchmark-2026),
  [Cartesia](https://www.cartesia.ai/vs/cartesia-vs-elevenlabs)).
- Se eligen voces por **locale** (es-MX, es-CO, es-AR, pt-BR) y se mide exactitud de pronunciación de
  montos, fechas y nombres de comercio (el error de síntesis también existe).

### Turnos, interrupciones y marcos

| Marco | Qué ofrece | Cuándo |
|---|---|---|
| **Pipecat** | tuberías de procesadores en Python, transporte a elección, **SmartTurn** (un clasificador que decide cuándo terminó de hablar el usuario; ~30% menos veces hablando encima frente a solo VAD) | prototipos y control fino en Python |
| **LiveKit Agents** | infraestructura WebRTC propia, telefonía, detección de turno adaptativa, MCP | producción con transporte y telefonía de un mismo proveedor |

([Soniox](https://soniox.com/wiki/voice-agent-frameworks),
[Evalgent](https://www.evalgent.com/blog/pipecat-vs-livekit),
[Reactify](https://www.reactify-solutions.com/articles/voice-ai-agents-production-2026))

**Detalle que decide la calidad tras una interrupción:** hay que registrar **lo que el agente alcanzó a
decir** (salida de síntesis) además de lo que el usuario dijo; si no, el historial no coincide con lo
que el cliente escuchó y las acciones se desalinean.

## 3. Seguridad propia de la voz

- **Suplantación con voz sintética:** en 2024 los intentos de fraude con *deepfake* crecieron más de
  1.300% y los ataques con voz sintética a bancos 149% (Pindrop, más de mil millones de llamadas); la
  estimación para 2026 es que 30% de las empresas ya no confiará en una verificación de identidad
  aislada: la respuesta es **por capas** ([CX Today](https://www.cxtoday.com/security-privacy-compliance/the-voice-trust-collapse-and-deepfake-voice-fraud/),
  [Pindrop](https://www.pindrop.com/research/report/voice-intelligence-security-report/)).
- **Confirmaciones:** tratar la salida del reconocimiento como **entrada no confiable**; leer de vuelta
  la instrucción completa y exigir asentimiento explícito antes de actuar; confirmación explícita
  cuando la confianza es media; **DTMF** (teclado) como alternativa para confirmar y para dígitos, que
  además es el método correcto para capturar datos de tarjeta
  ([Cekura](https://www.cekura.ai/blogs/voice-bot-testing-fintech),
  [FutureAGI](https://futureagi.com/blog/voice-ai-banking-financial-services-2026/)).
- **Inyección por voz:** una instrucción dicha ("olvida tus reglas") es el mismo ataque que por texto;
  la contención por arquitectura sigue siendo la defensa (investigación 3).

**Implicaciones:** la voz **no** es factor de autenticación en LATAM Bank; la autenticación reforzada va
por OTP en la app o por SMS simulado; las acciones se confirman con lectura de vuelta y "sí" explícito o
DTMF; la voz es dato personal (y biométrico si se usara para identificar), así que el audio crudo no se
guarda por defecto.

## 4. Evaluación de voz

Siguiendo a τ-voice e IHBench, y aprovechando lo que trae el dataset:

1. **Mismas tareas que el texto:** cada caso del retenido de texto se convierte en caso de voz, así se
   reporta la **retención** (éxito en voz sobre éxito en texto).
2. **Personas con acento:** síntesis de los turnos del cliente con voces es-MX, es-CO, es-AR y pt-BR.
3. **Condiciones reales:** ruido y degradación telefónica con la **distribución de calidad de audio del
   dataset** (en la muestra, 66% alta, 24% media, 5% baja).
4. **Interrupciones guionadas** en los momentos críticos (durante la lectura de la confirmación).
5. **Semilla humana de voz:** unas decenas de grabaciones reales del equipo y conocidos, con
   consentimiento, para calibrar cuánto se parece el resultado con voces sintéticas al de voces humanas
   (el reconocimiento suele acertar más con voz sintética).
6. **Métricas:** error de reconocimiento por acento, éxito de la tarea, resultados inseguros, latencia de
   voz a voz p50 y p95, recuperación tras interrupción, costo por minuto.

## 5. Chat: qué es estado del arte en 2026

- **AG-UI** (*Agent-User Interaction Protocol*): protocolo abierto de eventos entre el agente y la
  interfaz: texto en streaming, sincronización de estado, resultados de herramientas, componentes de
  interfaz y **aprobaciones con humano en el circuito**; soportado por PydanticAI, LangGraph, ADK y
  otros ([AG-UI](https://docs.ag-ui.com/introduction), [Microsoft](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/)).
  **A2UI** es la especificación complementaria de interfaz generativa.
- **Interfaz generativa:** el agente elige y llena componentes (tarjetas, opciones, formularios) en vez de
  solo escribir ([Zylos](https://zylos.ai/research/2026-05-28-agentic-ux-frontend-design-patterns-ai-agents/)).
- **Restricciones de WhatsApp** que el diseño debe respetar para ser portable: máximo 3 botones de
  respuesta de 20 caracteres, listas de hasta 10 filas, *Flows* para formularios, ventana de 24 horas y
  plantillas ([Infobip](https://www.infobip.com/blog/how-to-use-whatsapp-interactive-buttons),
  [Meta](https://developers.facebook.com/documentation/business-messaging/whatsapp/flows)).

**Para LATAM Bank:** componentes tipados que el motor emite (ficha de la transacción, lista de
transacciones posibles enmascaradas, botón de confirmación con el monto leído de la base, estado del
caso, aviso de traspaso) y que se **degradan** a botones y listas de WhatsApp. La confirmación es un
evento de aprobación, no un texto libre.

## 6. Un núcleo, dos superficies

- En 2026, omnicanal es un problema de **agente único**, no de enrutamiento: la voz es **otra superficie
  de entrada y salida del mismo núcleo**, y el estado del caso viaja entre canales para que el cliente no
  vuelva a explicar ([FutureAGI](https://futureagi.com/glossary/contact-center-omnichannel-customer-service/),
  [Voiceflow](https://www.voiceflow.com/blog/omnichannel-ai-customer-support)).

**Escenario que lo demuestra:** el cliente empieza por chat, se corta, llama por voz y el sistema retoma
en el mismo estado, sin repetir preguntas ni acciones (idempotencia).

## 7. Lo que se lleva el diseño

1. Voz y chat son **superficies** del mismo motor; ninguna decide nada.
2. **Voz principal en cascada** con turnos inteligentes, interrupciones registradas y respuestas
   deterministas para lo crítico (confirmaciones, montos, plazos).
3. **Frontend nativo de audio como experimento** medido contra la cascada en el mismo retenido de voz.
4. **Chat con AG-UI** y componentes tipados que se degradan a WhatsApp.
5. Seguridad de voz: sin biometría de voz, lectura de vuelta, DTMF, sin audio crudo guardado.
6. Evaluación de voz con personas por acento, ruido del dataset, interrupciones y semilla humana.

## Fuentes principales

- [Cascada frente a audio nativo, FutureAGI](https://futureagi.com/blog/cascaded-voice-ai-vs-speech-to-speech-2026/)
- [Frontend y backend para herramientas en voz, arXiv 2609.19334](https://arxiv.org/abs/2609.19334)
- [τ-voice, Sierra](https://sierra.ai/blog/tau-voice-benchmarking-real-time-voice-agents-on-real-world-tasks)
- [Full-Duplex-Bench-v3](https://arxiv.org/abs/2604.04847) y [IHBench](https://arxiv.org/abs/2606.19595)
- [AA-WER Streaming](https://artificialanalysis.ai/articles/new-streaming-speech-to-text-benchmark-aa-wer-streaming)
- [Latencia de síntesis, Gradium](https://gradium.ai/content/tts-latency-benchmark-2026)
- [Marcos de voz, Soniox](https://soniox.com/wiki/voice-agent-frameworks)
- [Fraude con voz sintética, CX Today](https://www.cxtoday.com/security-privacy-compliance/the-voice-trust-collapse-and-deepfake-voice-fraud/)
- [AG-UI](https://docs.ag-ui.com/introduction)
- [Botones y listas de WhatsApp, Infobip](https://www.infobip.com/blog/how-to-use-whatsapp-interactive-buttons)
