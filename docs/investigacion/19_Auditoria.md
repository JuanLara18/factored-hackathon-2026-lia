# Investigación 19 (Auditoría): qué evidencia acepta un auditor de IA y estado de las fuentes

**Cara:** Auditoría, tercera línea ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)).
**Preguntas:** ¿con qué marco audita la tercera línea un sistema de IA? ¿Qué cuenta como evidencia de
lo que hizo un agente? ¿Cómo debe ser la matriz de trazabilidad con el enunciado? ¿Qué tan confiables
son las fuentes que citamos?

**Hallazgo central:** el auditor no audita el modelo, audita **la cadena de evidencia**: que cada
afirmación del reporte se pueda reconstruir desde trazas, actas y datos versionados. La literatura de
2026 dice que no hay un esquema de trazas unificado para agentes y que las trazas completas mejoran
mucho la atribución de fallas; eso convierte nuestro registro de ejecución en el artefacto central de
la auditoría.

---

## 1. El marco del auditor

- El **marco de auditoría de IA del IIA**, actualizado en 2024 para alinearse con el NIST AI RMF y
  cubrir modelos de lenguaje, se organiza sobre el **modelo de tres líneas** (gobierno, gestión,
  auditoría interna) y cubre alineación estratégica, ética, gobierno de datos, recursos técnicos,
  terceros y monitoreo; trae una **lista de verificación** para empezar
  ([IIA](https://www.theiia.org/en/content/tools/professional/2023/the-iias-updated-ai-auditing-framework/),
  [PDF](https://www.theiia.org/globalassets/site/content/tools/professional/aiframework-sept-2024-update2.pdf)).
- Las **Normas Globales de Auditoría Interna** de 2024 rigen desde el 9 de enero de 2025
  ([Plante Moran](https://www.plantemoran.com/explore-our-thinking/insight/2024/10/iia-global-internal-audit-standards-update)).

**Uso:** la lista del IIA, adaptada, es el guion del subagente de Auditoría en la compuerta F7.

## 2. Qué es evidencia en un sistema de agentes

- No existe un **esquema de trazas unificado** para agentes: cada marco registra cosas distintas
  (prompts, respuestas, llamadas a herramientas, documentos recuperados, memoria, errores). Con
  trazas completas, la atribución de fallas por paso sube de **17% a 30%** frente a solo ver la salida
  final; la procedencia fina permite verificar afirmaciones, localizar fallas y hacer cumplir
  políticas, a cambio de almacenamiento y complejidad
  ([arXiv 2606.04990](https://arxiv.org/html/2606.04990)).
- Hay propuestas de **registros a prueba de manipulación** (encadenar huellas de cada evento) para
  agentes de largo recorrido ([arXiv 2609.01931](https://arxiv.org/pdf/2609.01931)); la parte útil
  para nosotros es el **encadenamiento de huellas**, no el anclaje en cadena de bloques.
- El enunciado ya lo dice: el razonamiento oculto del modelo **no** es evidencia de auditoría; lo son
  fuentes, reglas de política y registros de ejecución.

**Esquema de evidencia de LATAM Bank:**

| Evidencia | Dónde vive | Qué prueba |
|---|---|---|
| Traza por conversación (OpenTelemetry) con estados, herramientas, argumentos, resultados, regla aplicada | platino | qué hizo el sistema y por qué |
| Huella encadenada de las trazas de evaluación | platino | que no se editaron después |
| Actas de comités con desafíos | `Diseno/Actas/` | que hubo revisión independiente |
| Huella del retenido registrada antes de construir | acta de F2 | que no se ajustó sobre el retenido |
| Manifiesto de datos y linaje | platino | de dónde sale cada cifra |
| Versiones de modelo, prompt, política y código por corrida | platino | reproducibilidad |

## 3. La matriz de trazabilidad

Formato propuesto (una fila por exigencia del enunciado), extensión de la sección 8 de
[01](../Diseno/01_Interacciones_y_criterios.md):

| Columna | Contenido |
|---|---|
| Exigencia | cita textual del enunciado |
| Cara dueña | según la sección 6 de [04](../Diseno/04_Organizacion_y_roles.md) |
| Escenarios | IDs del catálogo |
| Métrica | definición oficial versionada (investigación 16) |
| Evidencia | artefacto y ubicación |
| Consulta | la consulta sobre platino que produce la cifra |
| Estado | cumplido, parcial, no cumplido (con motivo) |

Una exigencia sin consulta ni artefacto se marca **no cumplida**, aunque el sistema "lo haga".

## 4. Estado de las fuentes citadas

Primera pasada de verificación (26 de septiembre de 2026), sobre las fuentes que sostienen
decisiones:

| Fuente | Se usa para | Resultado |
|---|---|---|
| Nubank, [arXiv 2606.08867](https://arxiv.org/html/2606.08867) | método de evaluación; brecha contra humanos | **verificada**. Tabla 3: la IA queda entre −1,1 y −23,6 pp de tNPS frente a humanos (tarjeta −10; deuda −23,6; cupo −7,1; gestión de tarjeta −1,1; explicación de productos −6,2). Coincide con "1 a 24 pp" de la investigación 1 |
| FraudBench, [arXiv 2608.18136](https://arxiv.org/abs/2608.18136) | casos adversariales | **verificada**, con precisión: 150 escenarios, 107 públicos y 43 retenidos; seguridad ante ataques entre 49% y 65% según el agente; 698 documentos de política |
| *Capability Gates Are Not Authorization*, [arXiv 2606.28679](https://arxiv.org/abs/2606.28679) | autorización por llamada | **verificada**: LangChain y LangGraph, LlamaIndex y Stripe Agent Toolkit sin compuerta por defecto; ScopeGate con 0 de 48 evasiones estáticas y 0 de 29 intentos no autorizados |
| SR 26-2 | marco regulatorio de riesgo de modelo | **verificada** en el boletín de la OCC; corrigió la investigación 12 |
| Plazos de México | política | **en conflicto** (investigación 18) |
| UNE de CONDUSEF y responsable de atención al usuario del BCRA | organización | **verificadas** en fuentes oficiales o secundarias (investigación 18) |
| Resto de referencias de arXiv de 2026 en las investigaciones 1 a 11 | contexto | **pendientes**; se revisan antes de F7, priorizando las que sostienen una decisión |

**Regla:** una cifra que llega al reporte final necesita fuente verificada; las no verificadas se
quitan o se marcan.

## 5. Artefactos de Auditoría

1. Lista de verificación adaptada del IIA para F7.
2. Matriz de trazabilidad con consulta por fila.
3. Prueba de reproducibilidad en máquina limpia, con su registro.
4. Tabla de estado de fuentes, completa antes de entregar.
5. Dictamen final: aprobado, aprobado con salvedades o devuelto.

## Fuentes principales

- [IIA, marco de auditoría de IA](https://www.theiia.org/en/content/tools/professional/2023/the-iias-updated-ai-auditing-framework/)
- [From Agent Traces to Trust, arXiv 2606.04990](https://arxiv.org/html/2606.04990)
- [Agent Flight Recorder, arXiv 2609.01931](https://arxiv.org/pdf/2609.01931)
- [Normas Globales de Auditoría Interna, Plante Moran](https://www.plantemoran.com/explore-our-thinking/insight/2024/10/iia-global-internal-audit-standards-update)
