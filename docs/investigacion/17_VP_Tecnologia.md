# Investigación 17 (VP Tecnología): marco del agente, conversaciones durables, identidad de prueba y dominios BIAN

**Cara:** VP Tecnología ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)). **Preguntas:** ¿usar
un marco de agentes (LangGraph, PydanticAI, ADK) o un motor propio? ¿Cómo se retoma una conversación
horas después sin perder estado ni duplicar acciones? ¿Cómo se simula una identidad confiable con
expiración y autenticación reforzada? ¿Hace falta MCP? ¿Cómo se nombran los servicios?

**Hallazgo central:** nuestro diseño ya decidió que **los trabajadores de lenguaje no llaman
herramientas** (P4). Eso simplifica la elección: no necesitamos un marco de agentes autónomos sino
**un motor de flujo propio, tipado y persistente**, con un cliente de LLM tipado para comprensión y
redacción. Lo que sí hace falta traer de afuera es **durabilidad** (retomar tras horas) e **identidad
de prueba con reloj controlable**.

---

## 1. Marco del agente

| Marco | Fortaleza | Encaje con nuestro diseño |
|---|---|---|
| **LangGraph** | máquinas de estado con nodos y aristas, ejecución durable, interrupciones para aprobación humana; usado en producción por Klarna ([Uvik](https://uvik.net/blog/agentic-ai-frameworks/), [Langfuse](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)) | bueno para el flujo, pero su despacho por defecto ejecuta llamadas no autorizadas (investigación 2, *Capability Gates*); añade una abstracción que no usamos |
| **PydanticAI** | tipos de punta a punta, salidas validadas, inyección de dependencias tipada, MCP nativo, **durabilidad** integrada con Temporal, DBOS y Prefect ([Pydantic](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/)) | encaja con la seguridad por tipos (investigación 8) para comprensión y redacción |
| **Google ADK** | multimodal, nativo de Google Cloud, protocolo A2A | útil si se usa Apigee y Vertex; no es nuestro caso por defecto |

**Recomendación (a registrar como ADR):** motor de flujo **propio** en Python (máquina de estados
tipada de [01](../Diseno/01_Interacciones_y_criterios.md)) más **PydanticAI** solo como cliente
tipado de los trabajadores de lenguaje. Se gana control total de la autorización y trazas
limpias; se pierde el ecosistema de LangGraph, que no necesitamos. Si el tiempo aprieta, la
alternativa es LangGraph con nuestra capa de herramientas tipada debajo.

## 2. Conversaciones durables

- La ejecución durable guarda el estado del flujo en una base y, si el proceso cae o el cliente
  vuelve días después, **retoma desde el último paso completado**. DBOS corre como librería dentro
  del proceso y persiste en Postgres; Temporal es un servidor aparte y permite "esperar una semana"
  como si fuera una llamada bloqueante ([DBOS con PydanticAI](https://ai.pydantic.dev/durable_execution/dbos/),
  [Temporal](https://temporal.io/blog/build-durable-ai-agents-pydantic-ai-and-temporal),
  [Reactify](https://www.reactify-solutions.com/articles/durable-ai-agents-2026)).
- Toda herramienta que crea algo necesita **llave de idempotencia**: reintentar o retomar no debe
  radicar dos veces.

**Para nosotros:** el estado de la conversación ya es explícito (P4). La versión mínima es
**persistirlo en una tabla** después de cada transición con su llave de idempotencia, y retomar
leyendo el último estado. DBOS es la mejora natural si se quiere mostrar durabilidad con una librería
reconocida; Temporal es demasiada infraestructura para diez días. Los escenarios D5 (sesión expira) y
D6 (vuelve horas después, la ventana de 24 horas de WhatsApp, investigación 14) son la prueba.

## 3. Identidad de prueba confiable

El enunciado exige autenticación con una sesión de prueba confiable, no con un número de documento.
Opciones:

| Opción | Qué da | Costo |
|---|---|---|
| **Servicio propio** en el proceso: JWT firmados con `exp` y nivel de autenticación (`acr`), OTP simulado | control total, **reloj inyectable** para probar expiración | poco código; se documenta como simulado |
| `mock-oauth2-server` (NAV), `oauth2-mock-server` (AXA), `mockoidc` | servidores OIDC de prueba con reclamos `acr`, expiración configurable y, en `mockoidc`, **tiempo mutable** ([NAV](https://github.com/navikt/mock-oauth2-server), [AXA](https://github.com/axa-group/oauth2-mock-server), [mockoidc](https://github.com/oauth2-proxy/mockoidc)) | un contenedor más; más realista |
| Keycloak | proveedor completo | pesado para la hackatón |

La **autenticación reforzada** tiene estándar: **RFC 9470** (*OAuth 2.0 Step Up Authentication
Challenge*): el recurso rechaza con el nivel `acr` requerido y el cliente reautentica
([Authlete](https://www.authlete.com/developers/stepup_authn/)).

**Recomendación:** servicio propio con la forma de RFC 9470 (niveles `acr`: consulta y acción) y
**reloj inyectable** para pruebas; documentar que en producción se reemplaza por el proveedor de
identidad del banco. Si sobra tiempo, `mock-oauth2-server` en `docker compose` para mostrar el flujo
OIDC real.

## 4. ¿MCP o llamadas directas?

- MCP brilla cuando muchas herramientas se comparten entre aplicaciones y se gobiernan aparte; para
  pocas herramientas dentro de una aplicación, la llamada directa es más simple y rápida
  ([Prefect](https://www.prefect.io/resources/mcp-vs-function-calling),
  [Descope](https://www.descope.com/blog/post/mcp-vs-function-calling)).
- MCP trae riesgos propios (**envenenamiento de herramientas**, instrucciones ocultas en las
  descripciones) y guía de seguridad específica, incluida una de la NSA de junio de 2026
  ([MCP](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices),
  [NSA](https://media.defense.gov/2026/Jun/02/2003943289/-1/-1/0/CSI_MCP_SECURITY.PDF),
  [SoK](https://arxiv.org/pdf/2512.08290)).

**Decisión sugerida:** **sin MCP** en el camino crítico. Nuestros trabajadores de lenguaje no tienen
herramientas y el motor llama a los servicios directamente. Se menciona MCP en la ruta a producción
(exponer los servicios a otros agentes del banco con autorización OAuth).

## 5. Dominios BIAN para los servicios simulados

- **BIAN 13.0** (junio de 2025) publica APIs semánticas en OpenAPI 3 con anotaciones de dominio, en
  un repositorio público ([notas de versión](https://bian.org/wp-content/uploads/2025/06/BIAN-v13.0-Release-Notes-v0.3.pdf),
  [bian-official/public](https://github.com/bian-official/public)).
- Dominios candidatos: *Party Authentication* (identidad), *Current Account* y los de tarjeta
  (lectura), *Card Case* y *Customer Case Management* (radicar y consultar casos), *Fraud Diagnosis*
  (puntaje), *Payment Order* (transferencias, solo lectura). Los nombres exactos se confirman contra
  el repositorio de BIAN en F3.

**Uso:** los nombres y los verbos de nuestras herramientas siguen los de BIAN (por ejemplo,
*initiate* y *retrieve* sobre *Card Case*). Muestra que el prototipo se conecta a un banco real
cambiando adaptadores.

## 6. Instalación reproducible

`uv` con dependencias bloqueadas, `justfile` con `setup`, `data`, `test`, `eval`, `demo`; versiones de
modelos y prompts fijadas; semillas; `docker compose` solo para lo opcional (identidad OIDC, Marquez).
La prueba de Auditoría es clonar en una máquina limpia y correr `just setup demo`.

## 7. Artefactos de la VP Tecnología

1. ADR del marco (motor propio más PydanticAI) y ADR de "sin MCP en el camino crítico".
2. Servicio de identidad simulado con `acr`, expiración y reloj inyectable.
3. Servicios simulados con nombres BIAN y contratos documentados.
4. Persistencia del estado con llaves de idempotencia (y DBOS si hay tiempo).
5. Trazas OpenTelemetry por conversación.

## 8. Preguntas abiertas

- ¿Qué proveedor de LLM permiten las reglas? Condiciona gateway, latencia y costo.
- ¿La interfaz de la demo simula WhatsApp (ventana de 24 horas, plantillas) o es un chat genérico?

## Fuentes principales

- [Comparación de marcos, Uvik](https://uvik.net/blog/agentic-ai-frameworks/) y [Langfuse](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)
- [PydanticAI, ejecución durable](https://pydantic.dev/docs/ai/capabilities/durable_execution/overview/) y [con DBOS](https://ai.pydantic.dev/durable_execution/dbos/)
- [RFC 9470, Authlete](https://www.authlete.com/developers/stepup_authn/) y [mock-oauth2-server](https://github.com/navikt/mock-oauth2-server)
- [MCP, buenas prácticas de seguridad](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) y [NSA](https://media.defense.gov/2026/Jun/02/2003943289/-1/-1/0/CSI_MCP_SECURITY.PDF)
- [BIAN 13.0](https://bian.org/wp-content/uploads/2025/06/BIAN-v13.0-Release-Notes-v0.3.pdf) y [APIs semánticas](https://github.com/bian-official/public)
