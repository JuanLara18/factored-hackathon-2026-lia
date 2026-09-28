# Investigación 10: gobernanza de IA, gateways y filtros (Apigee, Model Armor)

**Pregunta:** ¿qué aporta una capa de **gateway de IA** (Apigee con Model Armor, o equivalentes)
entre la aplicación y los modelos? ¿Qué tan bien funcionan los filtros de inyección? ¿Y qué
marcos de gobernanza reconoce un banco?

**Hallazgo central:** el gateway es valioso **como punto único de gobierno**: cuotas, costos,
enrutamiento de modelos, redacción de datos personales en la frontera, auditoría centralizada. Como
**defensa principal contra la inyección de prompts es débil**: los detectores se evaden hasta en
un 100% con técnicas conocidas. El diseño correcto es **defensa en profundidad**: el gateway
filtra y gobierna; la arquitectura (investigaciones 2, 3 y 8) es la que garantiza.

---

## 1. Apigee como gateway de IA

Apigee, la plataforma de gestión de APIs de Google Cloud, añadió políticas específicas para LLM
([capacidades](https://docs.cloud.google.com/apigee/docs/api-platform/get-started/ai-capabilities)):

| Política | Qué hace | Para qué sirve aquí |
|---|---|---|
| **LLMTokenQuota** | cuota de tokens por producto de API y periodo (minuto a mes) | **presupuesto de costo** por canal o por cliente; responde a OWASP LLM10 ([tutorial](https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-ai-token-policies)) |
| **PromptTokenLimit** | limita picos de tokens en el prompt | protección contra ráfagas y abuso ([referencia](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/prompt-token-limit-policy)) |
| **SanitizeUserPrompt** | manda el prompt a **Model Armor** antes del modelo | filtro de entrada ([referencia](https://docs.cloud.google.com/apigee/docs/api-platform/reference/policies/sanitize-user-prompt-policy)) |
| **SanitizeModelResponse** | manda la respuesta a Model Armor antes del cliente | **filtro de salida**: datos sensibles, URLs maliciosas |
| **Caché semántica** | responde preguntas repetidas o reformuladas desde caché (Vertex AI Vector Search) | ahorro de latencia y costo en preguntas frecuentes |
| **Enrutamiento de modelos** | alias ("rápido", "preciso") hacia modelos concretos | cambiar de modelo sin tocar la aplicación |
| Presupuesto de gasto y analítica | costo acumulado, monitoreo y auditoría de cada solicitud | **reporte de costo por caso** que pide el enunciado |

Apigee también puede aplicar políticas al tráfico de **herramientas MCP** de un agente, y el
**Agent Development Kit (ADK)** de Google se integra con el gateway de Apigee
([ADK](https://adk.dev/agents/models/apigee/)). Hay un ejemplo completo de configuración
([apigee-x-ai-gateway](https://github.com/rajeevramani/apigee-x-ai-gateway)).

**Equivalentes** si no se usa Google Cloud: Azure API Management con capacidades de
[gateway de IA](https://learn.microsoft.com/en-us/azure/api-management/genai-gateway-capabilities),
[Apache APISIX](https://apisix.apache.org/ai-gateway/), Kong AI Gateway, y de código abierto y
ligero, **LiteLLM Proxy** (cuotas, enrutamiento, registro de costos, y se le conectan filtros como
Presidio o el propio Model Armor). Comparativa: [Zuplo](https://zuplo.com/learning-center/best-api-gateways-ai-llm-workloads-2026).

### Una advertencia sobre la caché semántica en banca

La caché semántica responde con **la respuesta de otra pregunta parecida**. Si se cachean respuestas
**personalizadas** ("tu saldo es…", "tu reclamo está en…"), la caché puede **devolverle a un
cliente datos de otro**. Regla: **solo se cachean respuestas genéricas** (qué es un contracargo,
plazos de ley), con la llave de caché aislada por tipo de contenido, y **nunca** nada que haya pasado
por una herramienta con datos del cliente. Es un error sutil que conviene mencionar en el reporte.

## 2. Model Armor

Servicio de Google Cloud, **independiente del modelo**, que revisa prompts y respuestas en tiempo
real ([producto](https://cloud.google.com/security/products/model-armor),
[notas de versión](https://docs.cloud.google.com/model-armor/release-notes)):

- detección de **inyección de prompts y *jailbreak***;
- **protección de datos sensibles**, integrada con Sensitive Data Protection (el DLP de Google):
  números de tarjeta, identificadores;
- detección de **URLs maliciosas** (phishing);
- filtros de IA responsable (odio, acoso, contenido peligroso) con umbrales de confianza;
- revisión de texto dentro de PDFs;
- **configuraciones mínimas obligatorias** (*floor settings*) a nivel de organización, también
  para servidores MCP administrados por Google (en vista previa).

**Límite documentado:** el filtro de inyección y *jailbreak* analiza hasta **512 tokens**; en
prompts largos hay que fragmentar o filtrar en la aplicación
([Sascha Heyer](https://medium.com/google-cloud/google-cloud-model-armor-6242dbae90b8)). Se puede
usar sin Apigee (API directa) o desde otros gateways
([TrueFoundry](https://www.truefoundry.com/docs/ai-gateway/google-model-armor)).

## 3. ¿Qué tan bien detectan la inyección estos filtros?

| Estudio | Resultado |
|---|---|
| [*Bypassing LLM Guardrails*](https://arxiv.org/abs/2504.11168) (2025) | seis sistemas, entre ellos **Azure Prompt Shield** y **Meta Prompt Guard**: con inyección de caracteres y técnicas adversariales, **hasta 100% de evasión** conservando el ataque |
| [PromptShield](https://pith.science/paper/2501.15145) | un detector ajustado sobre Llama-3.1-8B: 94,8% de detección con 1% de falsos positivos, pero **47,5% con 0,05%**; el mejor anterior, 12,8% y 1,5% |
| PINT (Lakera) | benchmark de 4.314 entradas con tabla para Lakera, Bedrock, Azure, **Model Armor**, Prompt Guard; **el conjunto es privado** y lo corre el propio Lakera, así que las comparaciones no son independientes |
| [*Prompt Injection Detection is Regime-Dependent*](https://arxiv.org/pdf/2605.26999) | el desempeño depende del régimen de despliegue |

**Lectura:** en un banco con millones de mensajes, lo que importa es la detección **a tasas de
falsos positivos muy bajas** (cada falso positivo es un cliente legítimo bloqueado), y ahí **todos
caen mucho**. Un filtro es útil para **detener lo obvio y dejar registro**, no para garantizar.

**Recomendación para el reto:** poner Model Armor (o un equivalente) en la frontera **y medir su
aporte** con los casos adversariales del conjunto de evaluación: cuántos detecta, cuántos falsos
positivos da sobre casos legítimos, y **cuántos de los que no detecta igual son contenidos por la
arquitectura**. Esa tabla demuestra defensa en profundidad con números, que es mucho más
convincente que afirmar que "usamos un guardarraíl".

## 4. Gobernanza en sector financiero

**Lo que dice un trabajo de práctica en finanzas reguladas**
([*Agent Security Meets Regulatory Reality*](https://arxiv.org/abs/2606.29142), 2026, un sistema KYC
en producción): asegurar agentes bajo regulación **"es menos sobre clases nuevas de ataque que sobre
hacer reales la auditabilidad, la autorización de mínimo privilegio y la aplicación de políticas en
la frontera"**; los *frameworks* dejan eso al ingeniero de turno. Cuatro patrones que funcionaron:
propagar un **identificador de caso** por todo el flujo, **RAG anclado para auditoría**, un **proxy
de redacción en la frontera de inferencia** (quitar datos personales antes de llamar al modelo) y
coreografía de cumplimiento entre agentes. Reportan también resultados negativos, entre ellos
**una población de solicitantes legítimos que el sistema automático no puede atender bien**, lo que
conecta con la equidad (investigación 3).

**Marcos que un banco reconoce:**

| Marco | Qué es | Uso en el reto |
|---|---|---|
| **NIST AI RMF 1.0** y el **perfil de IA generativa, NIST AI 600-1** (julio de 2024) | cuatro funciones (gobernar, mapear, medir, gestionar); 600-1 define **12 riesgos** propios de la IA generativa | mapear los riesgos del sistema a sus categorías |
| **ISO/IEC 42001** (2023) | sistema de gestión de IA certificable: controles del ciclo de vida, evaluación de impacto | referencia de gobierno organizacional |
| **Gestión de riesgo de modelos** | en EE. UU., la guía interagencial **SR 11-7** fue sustituida el 17 de abril de 2026 por la **SR 26-2** ([OCC](https://www.occ.gov/news-issuances/bulletins/2026/bulletin-2026-13.html)), que deja la IA generativa y agéntica **fuera de su alcance** | el puntaje de riesgo es un modelo clásico sujeto a validación, inventario y monitoreo; para el agente de lenguaje hay que proponer el marco (investigación 12) |
| EU AI Act | la calificación de crédito es de **alto riesgo**; la atención al cliente, en general, obligación de **transparencia** (decir que es una IA) | referencia; si el flujo fuera de crédito cambia mucho |

([comparación de marcos](https://www.eccouncil.org/cybersecurity-exchange/responsible-ai-governance/eu-ai-act-nist-ai-rmf-and-iso-iec-42001-a-plain-english-comparison/),
[unificación de taxonomías](https://arxiv.org/pdf/2608.07515))

**Artefactos de gobierno que se pueden entregar en una hackatón:**
1. **Ficha del modelo** (*model card*) de cada componente: uso previsto, datos, métricas, límites.
2. **Registro de riesgos** mapeado a NIST AI 600-1 y OWASP, con su control y su evidencia.
3. **Inventario de versiones**: modelo, prompt, política, datos, por corrida.
4. **Política de retención** y de redacción de datos.
5. **Aviso al cliente** de que habla con una IA, con la opción de humano (lo que pide el 87% en la
   encuesta de Gartner).

## 5. Cómo encaja en la arquitectura

```
Cliente ─► [Gateway de IA]  ─────────────────────────────►  [Modelos]
            │ cuotas, límites de ráfaga, enrutamiento          ▲
            │ Model Armor en entrada y salida                  │
            │ redacción de datos personales                    │
            │ caché semántica solo para contenido genérico     │
            │ costo y trazas por solicitud                     │
            ▼                                                  │
      [Aplicación: comprensión ─► motor de flujo ─► herramientas tipadas ─► redacción]
                      (lo que garantiza: investigaciones 2, 3 y 8)
```

**Honestidad con el alcance:** montar Apigee de verdad exige un proyecto de Google Cloud con Apigee
aprovisionado, que puede no estar disponible en diez días. Opciones, de más a menos fiel:
**Apigee real**; **LiteLLM Proxy con Model Armor por API**; o un **gateway mínimo propio** que
implemente las mismas políticas (cuota, límite, filtro, redacción, costo) documentado como
**sustituto** de Apigee con el mapeo política por política. El enunciado acepta servicios
simulados si se documentan su contrato y sus límites.

## Fuentes principales

- [Apigee, capacidades de IA](https://docs.cloud.google.com/apigee/docs/api-platform/get-started/ai-capabilities) y [políticas de tokens](https://docs.cloud.google.com/apigee/docs/api-platform/tutorials/using-ai-token-policies)
- [Model Armor](https://cloud.google.com/security/products/model-armor) y [su integración con Apigee](https://docs.cloud.google.com/model-armor/model-armor-apigee-integration)
- [Bypassing LLM Guardrails](https://arxiv.org/abs/2504.11168)
- [Agent Security Meets Regulatory Reality](https://arxiv.org/abs/2606.29142)
- [NIST AI RMF](https://docs.modulos.ai/frameworks/nist-ai-rmf)
