# Investigación 15 (VP Inteligencia Artificial): agentes como fuerza laboral, riesgo de transacción y datos de conversación

**Cara:** VP Inteligencia Artificial ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)).
**Preguntas:** ¿qué significa en la práctica tratar a los agentes como fuerza laboral (identidad,
permisos, supervisión, hoja de vida)? ¿Cómo se construye y se valida el puntaje de riesgo de la
transacción disputada (D-09)? ¿Cuándo son válidas las conversaciones generadas por el equipo para
entrenar y evaluar?

**Hallazgo central:** las tres preguntas tienen respuesta estándar en 2026, y en las tres el riesgo
es el mismo: **creerle a algo que se generó a sí mismo**. Un agente con permisos amplios, un modelo
que reaprende `fraud_score` o un conjunto de prueba escrito por el mismo LLM que se evalúa producen
buenos números sin significado. La defensa es identidad acotada, ablación contra la línea base y
separación entre quien genera y quien juzga.


> **Nota del 26 de septiembre de 2026, tras la [revisión del enunciado](../Diseno/05_Cobertura_del_enunciado.md):** la sección 2 queda sin piso: fuera de `fraud_score`, `is_fraud` no tiene señal (AUC 0,504 con partición temporal) y `fraud_score > 30` es fraude con precisión 1,0, una fuga de la etiqueta. El componente aprendido pasa a ser la comprensión de la recepción (D-14) y el puntaje de riesgo se reporta como experimento con resultado negativo ([05 de diseño](../Diseno/05_Cobertura_del_enunciado.md), sección 3.3).

---

## 1. Agentes como fuerza laboral

### Identidad y permisos

- **NIST** lanzó en febrero de 2026 la **AI Agent Standards Initiative** (CAISI) para estandarizar
  cómo los agentes se autentican, se autorizan y colaboran; el NCCoE publicó el documento conceptual
  *Accelerating the Adoption of Software and AI Agent Identity and Authorization*, que combina MCP,
  NGAC, confianza cero (SP 800-207) e identidad federada
  ([WorkOS](https://workos.com/blog/nist-ai-agent-standards-initiative-explained),
  [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-nist-ai-agent-standards-initiative-2026040/),
  [NIST](https://www.nist.gov/blogs/cybersecurity-insights/back-future-why-agentic-ai-needs-strong-identity-foundation)).
- Las identidades no humanas ya superan a las humanas hasta 144 a 1 en las empresas.
- **Mínimo privilegio por invocación**: tokens de alcance estrecho para la tarea concreta; la
  primitiva estándar es **OAuth 2.0 Token Exchange (RFC 8693)**, con tokens de vida corta y audiencia
  fija ([Security Boulevard](https://securityboulevard.com/2026/05/ai-agent-identity-management-a-2026-ciso-playbook/)).
- La identidad puede ser por usuario, por agente o **por tarea**; la de tarea da el menor privilegio.

### Inventario y ciclo de vida

- Gartner (abril de 2026) pone el **inventario central de agentes** como el segundo de seis pasos
  contra la proliferación; el perfil agéntico del NIST AI RMF de la CSA (marzo de 2026) extiende el
  inventario de GV.1.6 a **qué autoridad tiene cada agente, qué herramientas usa, qué delegaciones y
  cuándo se revisa o revoca** ([Bigeye](https://www.bigeye.com/blog/what-is-an-agent-registry)).
- Contenido mínimo de un registro: modelo, prompts, herramientas, fuentes de recuperación, dueño,
  clasificación de riesgo y **firma de aprobación**; la baja revoca accesos y archiva la evidencia
  ([FutureAGI](https://futureagi.com/blog/ai-agent-compliance-governance-2026),
  [Collibra](https://www.collibra.com/blog/ai-lifecycle-governance-governing-models-and-agents-from-ideation-to-decommissioning)).
- Hay una propuesta académica de **registro, promoción y retiro guiados por evaluación**
  ([arXiv 2607.00345](https://arxiv.org/pdf/2607.00345)): un agente no sube de versión sin pasar su
  evaluación, que es exactamente nuestra compuerta del Comité de Confianza.

### Cómo se ve en LATAM Bank

Un archivo `agentes/registro.yaml` en el repositorio, una entrada por "trabajador":

| Trabajador | Qué hace | Herramientas | Supervisor | Evaluación que lo habilita |
|---|---|---|---|---|
| Comprensión | intención, entidades, idioma, necesidad de aclarar | ninguna | VP IA | F1 macro y calibración en desarrollo; retenido en F6 |
| Redacción | respuesta al cliente desde hechos verificados | ninguna | VP Clientes | anclaje y tono (juez validado) |
| Puntaje de riesgo | riesgo de la transacción disputada | lectura de oro de aprendizaje | VP IA, validado por Gobierno | PR AUC contra `fraud_score` |
| Juez de evaluación | califica lo no determinista | ninguna | VP Gobierno | κ contra la muestra humana |

La **identidad por tarea** ya está en el diseño: la `SesionAutenticada` es un permiso de vida corta
para un cliente y una conversación, y los trabajadores de lenguaje **no tienen herramientas**; el
motor de flujo es quien las llama (P4, P5). La hoja de vida de cada uno es su *model card* más su
historial de versiones y actas.

## 2. El puntaje de riesgo de la transacción disputada

### Lo que dice la práctica

- Con prevalencias por debajo del 1%, la exactitud engaña; la **PR AUC** es la métrica principal de
  ordenamiento, y el umbral se elige en validación desde la curva de precisión y recuperación, nunca
  en prueba ([Scientific Reports 2026](https://www.nature.com/articles/s41598-026-58285-5)).
- La **partición temporal** hacia adelante es la que refleja el despliegue; la tasa de fraude y los
  patrones cambian en el tiempo.
- Los árboles con *gradient boosting* (XGBoost, LightGBM, CatBoost) siguen siendo la línea base fuerte
  en datos tabulares; las características de grafo **seguras contra fuga** (calculadas solo con el
  pasado) mejoran la interpretabilidad en redes de transacciones
  ([arXiv 2603.06632](https://arxiv.org/pdf/2603.06632)).
- Umbral **sensible al costo**: el costo de un falso negativo (fraude no contenido) no es el de un
  falso positivo (cliente legítimo escalado); ambos se fijan como supuestos de la política.

### El riesgo específico de nuestro dataset

`fraud_score` discrimina bien `is_fraud` (AUC 0,87) y probablemente **lo produjo el mismo generador**
a partir de la etiqueta. Un modelo nuevo puede terminar **reaprendiendo `fraud_score`**. Diseño del
experimento para que el resultado signifique algo:

1. **Línea base:** `fraud_score` solo.
2. **Modelo sin `fraud_score`:** características de la transacción, del cliente y del comercio con
   corte temporal. Mide si hay señal **independiente** del puntaje.
3. **Modelo con `fraud_score` más características:** mide si se le **agrega** algo.
4. Métricas: PR AUC con intervalo por *bootstrap*, recuperación a tasa de falsos positivos fija,
   calibración (curva y ECE), por país y segmento.
5. **Resultado aceptable de antemano:** si 2 y 3 no superan a 1, se reporta así y el componente
   aprendido del sistema es 1 más reglas; P9 lo exige y el enunciado premia la honestidad.

Volumen esperado: 0,10% de 5 millones son unas 5.000 transacciones fraudulentas, suficientes para
una partición temporal con intervalos razonables.

### Cómo entra en la conversación

El puntaje **no decide**: alimenta la tabla de política que decide entre R3 (contener y radicar),
R4 (urgente) y R5 (escalar). Las bandas de riesgo las fija Gobierno con la curva a la vista.

## 3. Conversaciones generadas por el equipo

El dataset no trae conversaciones útiles (investigación 13), así que el clasificador de motivo
secundario y buena parte de la evaluación dependen de conversaciones **escritas o generadas por
nosotros**. Lo que dice la evidencia:

- Los usuarios sintéticos de un LLM **comprimen la varianza**, invierten signos de relaciones y
  cometen errores de 10 a 30 puntos en subgrupos; hay diagnósticos (desplazamiento de covariables
  contra de concepto) y correcciones con 50 a 300 casos reales de calibración
  ([arXiv 2609.13148](https://arxiv.org/abs/2609.13148)).
- Las consultas sintéticas son **más largas** que las reales (Nubank: 111 palabras de mediana contra
  19, investigación 1), y los LLM etiquetan con más **indulgencia** que los humanos en los casos
  borde ([arXiv 2506.10301](https://arxiv.org/html/2506.10301v1)).
- Si genera y juzga la misma familia de modelos, el juez favorece a su generador (*preference
  leakage*, investigación 5).

**Reglas para LATAM Bank:**

1. **Semilla humana primero:** el equipo escribe a mano un conjunto pequeño (por ejemplo, 60 a 100
   mensajes iniciales) cortos, con errores de tipeo y modismos de MX, CO, AR y PT. Es el ancla de
   estilo y el único material "real" que tenemos.
2. **La generación imita la semilla**, con restricciones de longitud y registro; se mide la
   distancia de distribución (longitud, vocabulario) entre semilla y generado y se reporta.
3. **La etiqueta la da la política, no el generador:** cada caso se genera **desde** una ruta y un
   estado de base conocidos, así la etiqueta es cierta por construcción.
4. **Generador, sistema y juez de familias distintas.**
5. **El retenido lo escribe Gobierno**, no la VP IA (P1), con una fracción escrita a mano.
6. Todo caso lleva la marca `origen: equipo` y el reporte lo dice.

## 4. Artefactos de la VP IA

1. `agentes/registro.yaml` con la hoja de vida de cada trabajador.
2. Reporte del puntaje de riesgo con las tres variantes y la decisión previa sobre qué cuenta como
   mejora.
3. Semilla humana de mensajes y generador de conversaciones con sus métricas de distancia.
4. Prompts versionados y *model cards*.

## 5. Preguntas abiertas

- ¿Costo de un falso negativo contra un falso positivo? Lo fija Gobierno.
- ¿El clasificador de motivo secundario entra al sistema o queda solo como experimento reportado?
- ¿Qué proveedor y familia de modelos para comprensión, redacción, generación y juez? Depende de las
  reglas de la hackatón sobre servicios externos (pendiente de F0).

## Fuentes principales

- [NIST AI Agent Standards Initiative, WorkOS](https://workos.com/blog/nist-ai-agent-standards-initiative-explained) y [NIST, identidad para IA agéntica](https://www.nist.gov/blogs/cybersecurity-insights/back-future-why-agentic-ai-needs-strong-identity-foundation)
- [Gestión de identidad de agentes, Security Boulevard](https://securityboulevard.com/2026/05/ai-agent-identity-management-a-2026-ciso-playbook/)
- [Registro de agentes, Bigeye](https://www.bigeye.com/blog/what-is-an-agent-registry) y [ciclo de vida guiado por evaluación](https://arxiv.org/pdf/2607.00345)
- [Deriva temporal en fraude, Scientific Reports 2026](https://www.nature.com/articles/s41598-026-58285-5)
- [Características de grafo seguras contra fuga](https://arxiv.org/pdf/2603.06632)
- [When Can You Trust Your Synthetic Users?](https://arxiv.org/abs/2609.13148) y [sesgo en datos sintéticos para evaluación](https://arxiv.org/html/2506.10301v1)
