# Investigación 1: qué ha hecho la industria y qué salió mal

**Pregunta:** ¿quién ya construyó atención al cliente bancaria con IA, qué midió, qué le funcionó y
qué le costó caro? Y, en particular para LATAM, ¿qué problema de servicio pesa más?

**Hallazgo central:** los casos exitosos comparten tres rasgos: **flujo acotado, evaluación como
infraestructura y humano disponible**. Los fracasos públicos comparten el contrario: métrica de
costo sola (contención, volumen desviado) sin medir si el problema se resolvió.

> **Nota del 26 de septiembre de 2026, tras la [auditoría del dataset](13_Auditoria_del_dataset.md):** en el dataset, `contact_reason` es una copia de `reason_category` (seis categorías gruesas) y no distingue las transacciones no reconocidas; el patrón de los reguladores sí aparece en `complaints.subcategory`, donde "Cargo no reconocido" es el 18% de las quejas.

---

## 1. Los casos de referencia

### Nubank: el más cercano al reto y el mejor documentado

Es el caso que hay que leer completo. Brasil, México y Colombia, portugués y español con variantes
regionales, 100 millones de usuarios. Publicó dos artículos técnicos en 2026:

**"Building Customer Support AI Agents at 100M-User Scale: An Evaluation-Driven Framework"**
(KDD 2026, [arXiv 2606.08867](https://arxiv.org/abs/2606.08867)).

- **Contexto modular y versionado**, no un prompt monolítico: *instrucciones* (rol, restricciones,
  cumplimiento), *rutinas* (los procedimientos de los agentes humanos traducidos a pasos),
  *macros* (plantillas), *especificaciones de herramientas* y *memoria de trabajo*. Cada pieza con
  versión semántica.
- **Jueces LLM validados como cualquier clasificador**: anotación con consenso de tres personas,
  acuerdo entre jueces medido con kappa de Cohen (el prompt inicial daba κ = 0,00; optimizado con
  GEPA de DSPy subió a 0,745 a 0,95 según el par de modelos), umbral de κ > 0,80. Un prompt de juez
  escrito a mano **quedó por debajo de la clase mayoritaria** en una tarea desbalanceada.
- **Lo offline predice lo online**: diez variantes muestran relación positiva entre reducir la
  tasa de fallas offline y subir el NPS transaccional en producción.
- **Resultados en A/B** en cinco flujos (entrega de tarjeta, deuda, cupo, gestión de tarjeta,
  explicación de productos): en entrega de tarjeta, **+37 pp de tNPS y +29 pp de autoservicio**.
  Aun así, **el tNPS de la IA quedó entre 1 y 24 pp por debajo del de los humanos** en todos los
  flujos: lo reportan con honestidad.
- **Principios de herramientas**: la orquestación determinista va **en código, no en el prompt**;
  salidas de herramienta mínimas; **todas las acciones idempotentes** para reintentar con
  seguridad; las descripciones de herramientas se tratan como prompt.
- **Escalamiento por confianza**: se transfiere fuera de rutina, con datos insuficientes o con
  baja confianza, **conservando el contexto**.
- **Privacidad**: datos seudonimizados, control de acceso por rol, contratos que prohíben al
  proveedor del modelo entrenar con los datos.

**"Screen Before You Serve: Simulation for Production CX Agents at 140M Scale"**
([arXiv 2609.30137](https://arxiv.org/html/2609.30137v1)), con Guardrails AI.

- Clientes **simulados por un LLM con personas** (tono, perfil, tipo de problema), en portugués
  informal con errores de tipeo, y **herramientas simuladas en la frontera** (mock de las llamadas).
- La simulación **no es realista** (conversaciones de 111 palabras de mediana frente a 19 reales)
  pero **ordena bien las versiones**: r = 0,74 con las puntuaciones de producción, y eligió el
  ganador real en el 97% de los remuestreos.
- Ciclo de iteración **4,8 veces más rápido** (de 21 a 4,4 días por versión).
- Cambiar a un modelo abierto (Qwen3.5-122B) subió 8,8 pp el autoservicio y bajó 25% la latencia
  p95 sin pérdida significativa de NPS.

Otros datos de Nubank ([ZenML](https://www.zenml.io/llmops-database/building-an-ai-private-banker-with-agentic-systems-for-customer-service-and-financial-operations),
[OpenAI](https://openai.com/index/nubank/)): 8,5 millones de contactos al mes con **60% resuelto
por LLM en primer contacto**; agente de transferencias con precisión > 99,5% y confirmaciones de
contraseña antes de mover dinero; un juez LLM que en seis iteraciones pasó de 51% a 80% de F1,
**igual al acuerdo humano**, y se eligió la versión que priorizaba detectar errores sobre la
exactitud global. Pila: LangGraph, LangChain, LangSmith para trazas.

**Lo que se lleva el equipo:** la estructura de contexto, la validación de jueces con κ, la
simulación con herramientas mockeadas y la honestidad de reportar la brecha contra humanos. Es
casi exactamente lo que pide el criterio 5 del enunciado.

### Bank of America, Erica: el caso de la paciencia

[Erica](https://newsroom.bankofamerica.com/content/newsroom/press-releases/2025/08/a-decade-of-ai-innovation--bofa-s-virtual-assistant-erica-surpas.html)
lleva desde 2018: más de 3.000 millones de interacciones, unos 58 millones al mes. Nació como
asistente de **intenciones cerradas** (NLU clásico, no generativo) y solo en 2026 metió IA
generativa, y **del lado del empleado**: *EricaAssist* para 18.000 agentes, que
[reduce casi un minuto por llamada](https://newsroom.bankofamerica.com/content/newsroom/press-releases/2026/07/bank-of-america-enhances-ericaassist-with-generative-ai-to-help-.html).

**La lección:** el banco más grande de IA conversacional **no deja al LLM generativo hablar solo
con el cliente** en lo transaccional; lo pone a asistir al humano. El enunciado pide justificar
dónde la IA es apropiada y dónde la lógica determinista es preferible: Erica es el argumento.

### Klarna: el caso de advertencia

En febrero de 2024 anunció que su asistente
[manejaba dos tercios de los chats](https://www.usefini.com/blog/klarna-automates-two-thirds-of-customer-service-with-ai-assistant),
2,3 millones en el primer mes, resolución en menos de 2 minutos, equivalente a 700 agentes. En mayo
de 2025 el CEO dijo ["fuimos demasiado lejos… nos enfocamos demasiado en el costo; el resultado
fue menor calidad"](https://www.customerexperiencedive.com/news/klarna-reinvests-human-talent-customer-service-AI-chatbot/747586/)
y volvió a contratar humanos, **garantizando siempre la opción de hablar con una persona**. La IA
sigue haciendo dos tercios del volumen, ahora como capa de volumen y no como el servicio entero.

**La lección:** *contención no es resolución*. El enunciado lo dice textual ("Containment alone
does not demonstrate that the problem was solved") y Klarna es el ejemplo.

### Commonwealth Bank: la métrica equivocada, con consecuencias

CBA eliminó 45 puestos al lanzar un *voice-bot* que según el banco bajaba 2.000 llamadas por
semana. El sindicato mostró que **los volúmenes subían**, que había horas extra y líderes contestando
llamadas. En agosto de 2025 el banco
[reversó los despidos y admitió un "error"](https://www.abc.net.au/news/2025-08-21/cba-backtracks-on-ai-job-cuts-as-chatbot-lifts-call-volumes/105679492).

**La lección:** medir el efecto de extremo a extremo, incluidos los **recontactos**: un caso
"contenido" que vuelve por otro canal no se resolvió.

### Air Canada: la responsabilidad es de la empresa

Su chatbot inventó una política de tarifas por duelo. El tribunal de Columbia Británica
[rechazó el argumento de que el chatbot era "una entidad separada"](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/)
y condenó a la aerolínea por **tergiversación negligente**.

**La lección para un banco:** toda afirmación sobre política, tarifas o elegibilidad debe salir
**de una fuente verificada**, no del modelo. Es la exigencia del enunciado de "anclar las
respuestas" y de que el modelo **no invente reglas de elegibilidad**.

### Otros

- **Lloyds**: [asistente financiero agéntico](https://www.lloydsbankinggroup.com/media/press-releases/2025/lloyds-banking-group-2025/lloyds-banking-group-unveils-uks-first-ai-powered-financial-assistant.html),
  unos £50 millones de valor en 2025 con más de 50 casos de uso.
- **ING**: [chatbot generativo en siete semanas con McKinsey](https://ctomagazine.com/ing-ai-chatbot-building-smarter-and-faster-banking-support/);
  su conclusión es que desplegar IA conversacional en banca es tanto un problema de gobierno como de
  tecnología.
- **Bancolombia**: *Question Solver* sobre documentos de referencia en WhatsApp, Teams y web
  ([reporte anual, SEC 6-K](https://www.sec.gov/Archives/edgar/data/1071371/000107137125000062/ex991-annualreportofbancol.htm)).

---

## 2. Lo que dicen los clientes y los reguladores

- **Gartner (2025)**: [predice que en 2029 la IA agéntica resolverá sola el 80% de los problemas
  comunes](https://www.gartner.com/en/newsroom/press-releases/2025-03-05-gartner-predicts-agentic-ai-will-autonomously-resolve-80-percent-of-common-customer-service-issues-without-human-intervention-by-20290).
  Pero sus propias encuestas: [64% de clientes preferiría que no se usara IA en servicio](https://www.gartner.com/en/newsroom/press-releases/2024-07-09-gartner-survey-finds-64-percent-of-customers-would-prefer-that-companies-didnt-use-ai-for-customer-service)
  y [87% dice que es esencial poder llegar a un humano](https://www.gartner.com/en/newsroom/press-releases/2026-08-04-gartner-survey-finds-87-percent-of-customers-say-companies-using-genai-for-customer-service-must-provide-access-to-a-human-agent0).
- **CFPB (EE. UU., 2023)**: [informe sobre chatbots en finanzas de consumo](https://www.consumerfinance.gov/data-research/research-reports/chatbots-in-consumer-finance/chatbots-in-consumer-finance/).
  Los diez bancos más grandes los usan; las quejas describen **disputas que no se pueden resolver,
  información inexacta, bucles sin salida y ausencia de humano**. El riesgo regulatorio concreto:
  que el chatbot impida ejercer un derecho (disputar un cargo, por ejemplo).

---

## 3. Qué duele en LATAM: los datos de los reguladores

**En los tres países del dataset, la primera causa de queja es la misma: transacciones no
reconocidas.**

| País | Regulador | Dato |
|---|---|---|
| **Colombia** | Superfinanciera | 2,7 millones de quejas contra bancos en 2025; **transacciones no reconocidas, 39,8%**; transacciones mal aplicadas, ~11%; fallas de canales digitales, 7,8% ([El Colombiano](https://www.elcolombiano.com/amp/negocios/bancos-con-mas-quejas-en-colombia-2025-EB33896570), [Semana](https://www.semana.com/pais/articulo/cuales-son-las-quejas-mas-comunes-contra-los-bancos-en-colombia-y-como-reportar-una-queja/280318/)) |
| **México** | CONDUSEF | 147.357 quejas contra banca comercial en 2025; fuera de cobranza, las dos primeras son **consumos no reconocidos (29.761)** y **transferencias no reconocidas (13.631)**; las quejas por cobranza subieron 21% ([La Jornada](https://www.jornada.com.mx/noticia/2026/02/17/economia/crecieron-21-las-quejas-en-contra-de-los-despachos-de-cobranza-en-2025-condusef), [Top 10 CONDUSEF](https://www.condusef.gob.mx/documentos/estadistica/estad2025/TOP-10-2025-1Trim.pdf)) |
| **Brasil** (para el portugués) | Banco Central | lideran irregularidades en **tarjeta de crédito**: cobros indebidos, **compras no reconocidas o duplicadas**; el fraude con Pix fue el primer motivo de litigio en 2025; existe el MED, mecanismo especial de devolución de Pix ([Finsiders](https://finsidersbrasil.com.br/estudos-e-relatorios/bancos-e-fintechs-acumulam-maior-parte-das-reclamacoes-ao-bc/)) |

**Implicación para elegir el flujo:** la **recepción de disputas por transacciones no reconocidas**
está respaldada por datos reales de los tres países, toca fraude (hay `is_fraud` y `fraud_score`
en `transactions`), exige autenticación fuerte, tiene casos claros de escalamiento humano y es
exactamente uno de los ejemplos del enunciado. Hay que verificar en el dataset que
`contact_reason` y `complaints.category` muestren el mismo patrón antes de decidir.

---

## 4. Conclusiones para el diseño

1. **Un flujo, con profundidad.** Todos los casos exitosos arrancan acotados (Nubank va flujo por
   flujo con A/B). El enunciado lo premia explícitamente.
2. **Contención sola es una métrica peligrosa.** Klarna y CBA. Medir resolución verificada,
   recontacto y calidad del escalamiento.
3. **El humano siempre disponible**, con el contexto ya armado. Es lo que piden los clientes (87%),
   lo que corrigió Klarna y lo que exige el enunciado en el traspaso.
4. **Las afirmaciones de política salen de fuentes, no del modelo.** Air Canada.
5. **La evaluación es la infraestructura, no el cierre.** Nubank: jueces validados con κ,
   simulación con personas y herramientas mockeadas, comparación offline que predice lo online.
6. **La lógica determinista en código.** Nubank y Erica coinciden: el LLM para entender y
   redactar; las reglas, permisos y acciones fuera de él.
7. **Reportar la brecha contra humanos con honestidad.** Nubank lo hace y no le resta
   credibilidad; al contrario.

## Fuentes principales

- Nubank, [arXiv 2606.08867](https://arxiv.org/abs/2606.08867) y [arXiv 2609.30137](https://arxiv.org/html/2609.30137v1)
- [Bank of America, Erica](https://newsroom.bankofamerica.com/content/newsroom/press-releases/2026/03/bofa-ai-and-digital-innovations-fuel-30-billion-client-interacti.html)
- [Klarna, CX Dive](https://www.customerexperiencedive.com/news/klarna-reinvests-human-talent-customer-service-AI-chatbot/747586/)
- [Commonwealth Bank, ABC](https://www.abc.net.au/news/2025-08-21/cba-backtracks-on-ai-job-cuts-as-chatbot-lifts-call-volumes/105679492)
- [Moffatt v. Air Canada, ABA](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/)
- [CFPB, Chatbots in consumer finance](https://files.consumerfinance.gov/f/documents/cfpb_chatbot-issue-spotlight_2023-06.pdf)
