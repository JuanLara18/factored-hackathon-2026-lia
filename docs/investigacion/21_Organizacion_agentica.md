# Investigación 21: lo que faltaba para pulir la organización

**Pregunta:** con la voz en el alcance y el desarrollo a la vista, ¿qué le falta a la organización v1
de LATAM Bank ([04 de diseño](../Diseno/04_Organizacion_y_roles.md))? ¿Cómo se organizan en 2026 las
empresas que trabajan con agentes, qué roles nuevos existen y dónde vive la operación de fraude?

**Hallazgo central:** la v1 estaba organizada por **capacidades** (vicepresidencias) pero no tenía la
unidad que **entrega un resultado**. Las organizaciones agénticas de 2026 se arman con **equipos
pequeños orientados a un resultado de punta a punta**, con personas "por encima del circuito" que
supervisan agentes. Faltaban además cuatro funciones concretas: la operación humana de fraude y
disputas (el destino del traspaso), la voz como especialidad, la ingeniería de evaluación y la oficina
que ordena la entrega.

---

## 1. La organización agéntica

McKinsey describe el paradigma que sigue a la adopción de IA
([agentic organization](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era),
[seguimiento de 2026](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/ai-is-everywhere-the-agentic-organization-isnt-yet)):

- **Equipos agénticos orientados a resultados** como bloque básico: pocas personas multidisciplinarias
  que son dueñas de flujos de IA y los supervisan para entregar un resultado de negocio de punta a
  punta (producto, tecnología, datos, operación).
- **Personas "por encima del circuito"** para dirigir y supervisar, y **dentro del circuito** solo donde
  el contacto humano importa.
- Tres roles humanos: **supervisores en forma de M** (generalistas que orquestan agentes y la fuerza
  laboral híbrida), **expertos en forma de T** (especialistas que rediseñan flujos, atienden excepciones
  y cuidan la calidad) y **primera línea aumentada** (menos tiempo en sistemas, más con personas).
- Los gerentes pasan de optimizar el desempeño individual a **diseñar sistemas**: poner guardarraíles a
  los agentes e intervenir donde el juicio humano importa.

## 2. Roles nativos de IA en 2026

| Rol | Qué hace | Evidencia |
|---|---|---|
| **Ingeniero de evaluación** | construye y corre las evaluaciones que prueban que el agente no falla en producción; es lo que separa una demo de un despliegue | [landed](https://www.landed.jobs/articles/ai-native-jobs-2026-field-guide) |
| **Operación de agentes** (*AgentOps*) | despliega, monitorea, gobierna y optimiza agentes en producción, como DevOps para software y MLOps para modelos | [Second Talent](https://www.secondtalent.com/occupations/ai-agent-operations-engineer/) |
| **Ingeniero desplegado en campo** | se sienta con el negocio semanas, entrega algo que funciona y después se productiza; las vacantes crecieron 729% entre abril de 2025 y abril de 2026 | [Wikipedia](https://en.wikipedia.org/wiki/Forward_Deployed_Engineer), [Substack](https://aishwaryasrinivasan.substack.com/p/the-hottest-role-in-2026-forward) |
| **Gerente de producto de IA** | define el problema, los resultados y los compromisos | [landed](https://www.landed.jobs/articles/ai-native-jobs-2026-field-guide) |
| **Diseñador conversacional** | diseña las conversaciones del agente virtual y la asistencia al agente humano | investigación 12 |

## 3. Dónde vive la operación de fraude y disputas

- La primera línea de defensa contra el fraude son las **unidades operativas**, que por su contacto
  directo con clientes y transacciones detectan antes el riesgo; la segunda línea (riesgo y
  cumplimiento) supervisa y la tercera audita
  ([FinCrime Intelligence](https://fincrimeintelligence.com/glossary/first-line-of-defense/),
  [Unit21](https://www.unit21.ai/fraud-aml-dictionary/three-lines-of-defense)).
- La OCC pide un sistema de gestión del riesgo de fraude con **políticas, procesos, personal y
  controles** proporcionales al banco, con respuesta al fraude y revisiones
  ([OCC 2019-37](https://www.occ.gov/news-issuances/bulletins/2019/bulletin-2019-37.html)).
- En la operación de contracargos conviven el servicio al cliente (primera respuesta), el especialista en
  contracargos (evidencia y respuesta), el analista de fraude (patrones) y un responsable del programa
  ([Chargeflow](https://www.chargeflow.io/chargebacks-101/chargeback-fraud-management)).

**Para LATAM Bank:** la operación humana de fraude y disputas es **primera línea** y pertenece a la VP
Clientes. Es el destino del traspaso, tiene colas por idioma y turno (solo 7 especialistas en fraude
hablan portugués; investigación 13) y sus correcciones son etiquetas.

## 4. Equipo rojo

- El AI Act de la UE exige pruebas adversariales para IA de alto riesgo desde el 2 de agosto de 2026, y
  los reguladores financieros esperan evaluación adversarial documentada; el G7 pide pruebas externas
  independientes ([Tredence](https://www.tredence.com/blog/ai-red-teaming-2026-guide-to-ai-security),
  [IAPP](https://iapp.org/news/a/emerging-trends-in-regulating-generative-ai-how-red-teaming-is-shaping-the-landscape)).
- Práctica común: "días de equipo rojo" en los que un equipo interno juega a atacante mientras el equipo
  que construye detecta y corrige.

**Para LATAM Bank:** el equipo rojo es una función explícita de la gerencia de Seguridad (Gobierno), con
ataques de texto **y de voz** (instrucciones dichas, voz sintética, audio con ruido), y su resultado entra
al conjunto de estrés.

## 5. Lo que cambia en la organización

| Falta en la v1 | Cómo se incorpora en la v2 |
|---|---|
| Unidad que entrega el resultado | **Misión "cargo no reconocido"**: equipo agéntico transversal con dueña de resultado (VP Clientes); las VP pasan a ser capacidades que aportan a la misión |
| Destino del traspaso | **Operaciones de fraude y disputas** en la VP Clientes |
| Voz | diseño de voz en Clientes, modelos de habla en IA, tiempo real y telefonía en Tecnología |
| Ingeniería de evaluación | en la VP IA (arnés, simulador de usuarios de texto y voz); Gobierno sigue siendo dueño del retenido y de la corrida final |
| Operación de agentes | *AgentOps* en la VP IA, con la observabilidad de Tecnología |
| Equipo rojo | función explícita en Seguridad (Gobierno) |
| Orden de la entrega | **Oficina de Entrega** en la Presidencia: backlog, cadencia, integración del reporte y la demo |
| Roles humanos | Presidencia como supervisor en forma de M; especialistas de fraude como expertos en forma de T; agentes humanos como primera línea aumentada |

## Fuentes principales

- [McKinsey, la organización agéntica](https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era)
- [Roles nativos de IA, landed](https://www.landed.jobs/articles/ai-native-jobs-2026-field-guide)
- [Operación de agentes, Second Talent](https://www.secondtalent.com/occupations/ai-agent-operations-engineer/)
- [OCC 2019-37, gestión del riesgo de fraude](https://www.occ.gov/news-issuances/bulletins/2019/bulletin-2019-37.html)
- [Equipo rojo en 2026, Tredence](https://www.tredence.com/blog/ai-red-teaming-2026-guide-to-ai-security)
