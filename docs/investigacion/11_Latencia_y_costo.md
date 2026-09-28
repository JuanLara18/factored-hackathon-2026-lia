# Investigación 11: latencia y costo

**Pregunta:** el enunciado pide latencia **p50 y p95 de extremo a extremo** y **costo por caso y
por resolución exitosa**, y hacer explícitos los *trade-offs* entre autonomía, exactitud, latencia,
costo y supervisión humana. ¿Qué números son realistas, de dónde viene la latencia en un agente, y
qué palancas hay?

**Hallazgo central:** en un agente la latencia **se compone** y el p95 **se amplifica**: cada paso
tiene su cola, y la suma de colas es mucho peor que la suma de medianas. Las palancas que más
mueven la aguja no son "un modelo más rápido" sino **hacer menos llamadas al LLM**: un
clasificador pequeño donde basta (12 ms contra 2 s), lógica determinista donde basta (cero
llamadas), caché de prompt para lo repetido, y enrutamiento a modelos pequeños con escalamiento a
los grandes.

---

## 1. Qué se percibe como lento

Los umbrales clásicos de Nielsen siguen siendo la referencia: **0,1 s** se siente instantáneo, **1 s**
mantiene el hilo del pensamiento, **10 s** es el límite de la atención. En chat, el *streaming* (ver
aparecer el texto) y un indicador de "escribiendo" hacen tolerable una respuesta de 2 a 4 s; en voz
el turno de conversación natural está por debajo de ~1 s, mucho más exigente. En mensajería
asíncrona (WhatsApp) la latencia importa menos que la **exactitud** y la **continuidad** de la sesión.

**Implicación:** el presupuesto depende del canal. Para chat, un objetivo razonable es **p50 < 2 s y
p95 < 5 s por turno**, con *streaming*. Hay que declararlo como supuesto.

## 2. Cuánto tardan los modelos (2026)

- **Tiempo al primer token** (TTFT): los modelos frontera están por debajo de 1 s en mediana; los
  pequeños y rápidos, ~0,35 s (por ejemplo Gemini 2.5 Flash-Lite, con el mejor cociente
  latencia-precio); proveedores con hardware propio (Groq, Cerebras) ~0,12 s con modelos abiertos
  ([AIMultiple](https://research.aimultiple.com/llm-latency-benchmark/),
  [Digital Applied](https://www.digitalapplied.com/blog/ai-model-latency-benchmarks-2026-ttft-throughput)).
- **La cola:** el **p95 es 1,6 a 3,2 veces el p50**, con un promedio de **2,1 veces**; algunos
  proveedores tienen p99 **3 a 5 veces** la mediana en horas pico; otros son más estables
  ([Kunal Ganglani](https://www.kunalganglani.com/blog/llm-api-latency-benchmarks-2026)). Las cifras
  cambian mes a mes: **medir con el modelo y la región que se vayan a usar**.
- **Región:** llamar desde Colombia a un endpoint en EE. UU. suma latencia de red; preferir
  regiones cercanas si el proveedor las ofrece.

## 3. Por qué el p95 de un agente es peor de lo que parece

Si un paso tiene 1% de probabilidad de ir lento, un flujo que depende de **10 pasos** tiene ~10% de
probabilidad de que alguno vaya lento. Un turno típico de agente encadena: comprensión (LLM),
herramienta de identidad, herramienta de transacciones, consulta de política, decisión, redacción
(LLM). **Cada cola suma al p95 final** ([TianPan](https://tianpan.co/blog/2026-05-07-llm-tail-latency-p99-heavy-tailed-distributions),
[ClickHouse](https://clickhouse.com/resources/engineering/tail-latency)).

**Reglas que salen de ahí:**
- **Cada llamada externa con un *timeout* menor que el presupuesto**, y un resultado degradado
  (respuesta genérica, traspaso) cuando se dispara.
- **No reintentar respuestas lentas**, solo fallas: reintentar lo lento convierte un problema de
  latencia en un colapso de capacidad
  ([TianPan](https://tianpan.co/blog/2026-05-02-tail-tolerant-retry-policy-llm-gateway-latency-cliff)).
- **Solicitudes con cobertura** (*hedged requests*: mandar un duplicado si el primero tarda) **solo
  para lecturas idempotentes** y con cuidado, porque multiplican la carga.
- **Paralelizar** lo que no depende entre sí (consultar transacciones y reclamos a la vez).
- **Medir por span**: con las trazas de OpenTelemetry (investigación 5) se ve qué paso se come el
  p95.

## 4. Las palancas, ordenadas por impacto

| Palanca | Efecto | Evidencia |
|---|---|---|
| **No llamar al LLM** donde basta la lógica | cero latencia y costo del modelo | la arquitectura de la investigación 2 |
| **Clasificador pequeño** para intención y enrutamiento | **12 ms** contra **2 s**, y más exacto (94,2% contra 85,3% en BANKING77) | [intent-router](https://github.com/smallestbusiness/intent-router) (investigación 5) |
| **Caché de prompt** (el prompt del sistema, la política y las herramientas se repiten en cada turno) | costo de lo cacheado ~**10%** del normal en Anthropic, 50% en OpenAI, 75% en Gemini implícito; latencia **40 a 85% menor** en prompts largos | [comparación](https://leanlm.ai/blog/prompt-caching), [FutureAGI](https://futureagi.com/blog/understanding-prompt-caching-for-faster-ai-responses/) |
| **Enrutamiento y cascadas** (modelo pequeño primero, grande solo si hace falta) | RouteLLM: **85% menos costo** manteniendo 95% de la calidad de GPT-4, mandando solo 14% al modelo grande; FrugalGPT hasta 98% | [encuesta de enrutamiento](https://arxiv.org/pdf/2603.04445) |
| **Salidas estructuradas compactas** | menos tokens de salida; BAML ~300 tokens menos de prompt | investigación 8 |
| ***Streaming*** de la redacción | baja la latencia **percibida**, no la real | |
| **Caché semántica** solo para contenido genérico | preguntas frecuentes sin llamar al modelo | investigación 10, con su advertencia |
| **Modelos abiertos en hardware rápido** | TTFT ~0,12 s | Nubank bajó **25% el p95** cambiando a un modelo abierto sin perder NPS (investigación 1) |

**Sobre las cascadas en banca:** un trabajo reciente advierte que el escalamiento debe considerar el
**daño**, no solo la confianza ([*Signed Rescue Routing*](https://arxiv.org/pdf/2609.07786)): una
respuesta barata pero incorrecta sobre un plazo legal cuesta más que la llamada al modelo grande.
Enrutar por **riesgo del tipo de solicitud** (tabla de política de la investigación 2), no solo por
confianza del modelo pequeño.

## 5. El costo por caso, como lo pide el enunciado

El enunciado pide costo **por caso intentado** y **por resolución automática exitosa**, con
supuestos explícitos y "no definido" si no hay resoluciones. Modelo de costo simple y honesto:

```
costo por caso = Σ (tokens de entrada no cacheados × precio
                   + tokens cacheados × precio de caché
                   + tokens de salida × precio de salida)   sobre todas las llamadas al LLM
               + herramientas y filtros (Model Armor, embeddings) por llamada
               + (si hay traspaso) costo del minuto humano × AHT del traspaso

costo por resolución exitosa = costo total de los casos intentados / número de resoluciones seguras
```

La segunda cifra es la que importa: un sistema barato por caso pero que resuelve poco es caro por
resolución. Y sumar el **costo humano** de los traspasos evita el error de Commonwealth Bank
(investigación 1): si el bot escala más, el costo total puede subir.

**Referencia de negocio** (investigación 7): un contacto humano cuesta US$7 a 14 por voz y US$3 a 7
por chat; un bot, US$0,03 a 0,15. Esa diferencia de dos órdenes explica la presión por contener,
y la métrica de resolución segura explica por qué no basta.

## 6. El *trade-off* explícito que pide el enunciado

| Decisión | Más autonomía / menos costo | Más control / más costo |
|---|---|---|
| Comprensión | clasificador pequeño | LLM grande |
| Aclaración | asumir la intención más probable | preguntar siempre que la confianza sea baja |
| Acciones | ejecutar tras confirmación | ejecutar solo con humano |
| Escalamiento | umbral alto (escala poco) | umbral bajo (escala mucho) |
| Verificación | confiar en la respuesta de la herramienta | releer el estado después de actuar |

La forma de presentarlo con datos: **una curva** de resolución segura contra costo (o contra tasa de
escalamiento) al mover el umbral, como la curva de riesgo y cobertura de la investigación 4, y
marcar el punto de operación elegido con su justificación.

## Fuentes principales

- [Benchmarks de latencia 2026](https://research.aimultiple.com/llm-latency-benchmark/) y [p95 frente a p50](https://www.kunalganglani.com/blog/llm-api-latency-benchmarks-2026)
- [Cola de latencia en LLM](https://tianpan.co/blog/2026-05-07-llm-tail-latency-p99-heavy-tailed-distributions) y [política de reintentos](https://tianpan.co/blog/2026-05-02-tail-tolerant-retry-policy-llm-gateway-latency-cliff)
- [Caché de prompt por proveedor](https://leanlm.ai/blog/prompt-caching)
- [Enrutamiento y cascadas, encuesta](https://arxiv.org/pdf/2603.04445) y [Signed Rescue Routing](https://arxiv.org/pdf/2609.07786)
