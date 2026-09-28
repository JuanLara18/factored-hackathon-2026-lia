# Investigación 18 (VP Gobierno): validar un agente sin norma, política como código, amenazas y plazos por país

**Cara:** VP Gobierno, con sus cuatro gerencias ([04 de diseño](../Diseno/04_Organizacion_y_roles.md)).
**Preguntas:** si SR 26-2 deja la IA generativa fuera, ¿con qué marco valida la segunda línea
nuestro agente? ¿Cómo se escribe la política como código? ¿Con qué método se modela la amenaza?
¿Qué plazos exige cada país, verificados? ¿Cómo se mide la equidad?

**Hallazgo central:** hay un marco académico compatible con SR 26-2 que **nuestro diseño ya
satisface casi por construcción** (ningún poder autónomo sobre decisiones, anclaje en política
aprobada, rol acotado, supervisión humana factible). Donde el trabajo es real es en la **política por
país**: las fuentes se contradicen en plazos (México) y conviven regímenes distintos para el mismo
reclamo (Argentina). La política no se puede escribir desde notas de prensa; necesita el texto
primario.


> **Nota del 26 de septiembre de 2026, tras la [revisión del enunciado](../Diseno/05_Cobertura_del_enunciado.md):** el "puntaje de riesgo" de la tabla de la sección 1 deja de ser un trabajador aprendido (D-14): `fraud_score` entra a la política como regla determinista, con una zona gris revisada por humano. Su nivel de riesgo se mantiene alto porque decide contener o escalar.

---

## 1. Riesgo de modelo: validar el agente

SR 26-2 (abril de 2026) excluye la IA generativa y agéntica (investigación 12). El marco **GAICF**
([arXiv 2607.04103](https://arxiv.org/html/2607.04103v1)), diseñado para ser compatible con SR 26-2,
propone cuatro capas:

| Capa | Qué exige | Cómo la cumple LATAM Bank |
|---|---|---|
| 1. **Frontera del caso de uso**: cuatro condiciones o se prohíbe | sin autoridad autónoma sobre decisiones de crédito o cumplimiento; anclaje en políticas o modelos aprobados; rol acotado; supervisión humana factible. Solo se permiten "asistencia colaborativa" y "automatización aprobada por humano" | P4 (el código decide), política versionada, un solo flujo, humano en cualquier turno y escalamiento por política |
| 2. **Nivel de riesgo** | matriz de **cercanía a la decisión** contra **daño potencial al consumidor**: bajo, moderado, alto, crítico | ver tabla de abajo |
| 3. **Evidencia** | calidad, relevancia y suficiencia de las entradas | contratos de oro y hechos verificados con fuente |
| 4. **Evaluación y monitoreo** | exactitud, exactitud de citas, completitud, alucinación, trazabilidad; lo crítico con revisión humana antes de liberar | métricas de [01](../Diseno/01_Interacciones_y_criterios.md), retenido, trazas |

**Clasificación propuesta de nuestros trabajadores** (investigación 15):

| Trabajador | Cercanía a la decisión | Daño potencial | Nivel |
|---|---|---|---|
| Comprensión | media: elige la ruta, pero el motor valida | medio | moderado |
| Redacción | alta: es lo que lee el cliente | alto (plazos, montos) | **alto** |
| Puntaje de riesgo | alta: decide contener o escalar vía política | alto | **alto** |
| Juez de evaluación | baja: no toca al cliente | bajo | bajo |

**Evidencia que produce la segunda línea** (lista del marco): registro de la frontera, justificación
del nivel, trazas de evidencia, resultados de validación, reportes de monitoreo y registros de
aprobación humana. En nuestro repositorio son **las actas** del Comité de Confianza.

## 2. Política como código

- Dos motores dominan: **OPA con Rego** (dinámico, pensado para infraestructura) y **Cedar** (esquema
  estricto, pensado para autorización de aplicaciones, con **verificación formal** mediante SMT)
  ([Permit.io](https://www.permit.io/blog/opa-vs-cedar), [Oso](https://www.osohq.com/learn/opa-vs-cedar-vs-zanzibar)).
- AWS puso **Cedar** como motor de **AgentCore Policy** (marzo de 2026): intercepta **cada llamada de
  un agente a una herramienta** en el gateway y la autoriza contra la política
  ([Harness](https://www.harness.io/blog/policy-as-code-in-2026-opa-kyverno-cedar-and-what-s-next)).
- Un punto de decisión de política frente a cada herramienta da al agente la auditoría que la
  ingeniería de prompts no puede dar ([TianPan](https://tianpan.co/blog/2026/04/25/policy-as-code-agent-permissions-opa-rego)).

**Para nosotros hay dos políticas distintas, y conviene no mezclarlas:**

| Política | Qué decide | Forma recomendada |
|---|---|---|
| **De autorización** | ¿esta sesión puede ejecutar esta acción sobre este recurso? | tipos (investigación 8) como garantía estática; **opcional**: Cedar como punto de decisión en tiempo de ejecución que deja registro de cada decisión |
| **De negocio** | plazos por país, umbrales, qué ruta corresponde, qué requiere confirmación | **tabla versionada** (YAML) con la norma de cada regla, evaluada por el motor de flujo y probada con casos borde |

Cedar suma una segunda capa verificable y un registro de decisiones que Auditoría puede leer; se
adopta solo si no retrasa F3 (P9).

## 3. Modelo de amenazas

- **MAESTRO** (CSA, febrero de 2025) modela amenazas de sistemas agénticos en siete capas: modelos
  fundacionales, operaciones de datos, marcos de agentes, despliegue e infraestructura, evaluación y
  observabilidad, seguridad y cumplimiento, y ecosistema de agentes
  ([CSA](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro)).
- **OWASP** agéntico aporta la taxonomía ASI01 a ASI10 y una ruta de decisión para saber qué familias
  aplican ([arXiv 2504.19956](https://arxiv.org/html/2504.19956v2)).

**Artefacto:** una tabla por capa de MAESTRO con amenaza, control, escenario de prueba (S1 a S10 de
[01](../Diseno/01_Interacciones_y_criterios.md)) y código OWASP. Ejemplo de la capa de operaciones de
datos: el producto de otro cliente en una queja (S10), controlado por la coherencia de dueño en plata.

## 4. Plazos por país: lo verificado y lo contradictorio

| País | Regla | Fuente | Estado |
|---|---|---|---|
| Colombia | la entidad responde el reclamo en **15 días hábiles**; si no, el cliente acude al Defensor del Consumidor Financiero | Ley 1328 de 2009 (investigación 3) | verificar en el texto de la ley |
| México | reporte dentro de **90 días**; si se reporta en **48 horas**, abono provisional en **2 días hábiles**; dictamen en **45 días** (180 si es internacional); sin respuesta, procede a favor del cliente | [El Imparcial, agosto de 2026](https://www.elimparcial.com/dinero/2026/08/05/condusef-establece-que-los-bancos-deben-devolver-el-dinero-de-un-cargo-no-reconocido-en-dos-dias-habiles-si-el-reclamo-se-hace-en-48-horas-aunque-existe-un-plazo-de-90-dias-para-solicitar-la-aclaracion/), investigación 3 | **contradicción**: la investigación 3 dice 45 días **naturales**; esta fuente, 45 días **hábiles**. Resolver con el texto de la Ley para la Transparencia y Ordenamiento de los Servicios Financieros |
| México | las quejas que llegan por la **UNE** o por CONDUSEF se responden en **30 días hábiles** | [CONDUSEF](https://www.condusef.gob.mx/?p=contenido&idc=767&idcat=1) | la UNE existe y es obligatoria (verificado); plazo a confirmar en las reglas publicadas |
| Argentina | toda entidad designa un **responsable de atención al usuario**; da número de reclamo en **3 días hábiles** y resuelve en **10 días hábiles**, salvo excepciones | [BCRA, texto ordenado de Protección de los Usuarios](https://www.bcra.gob.ar/archivos/Pdfs/texord/t-pusf.pdf), [Infobae](https://www.infobae.com/economia/2023/03/17/como-presentar-un-reclamo-ante-un-banco-y-que-hacer-en-caso-de-no-obtener-respuesta/) | verificado en fuentes secundarias; el texto ordenado es la fuente primaria |
| Argentina | tarjeta de crédito: impugnar el resumen en **30 días**; acuse en **7 días hábiles**; corregir o explicar en **15** | régimen de tarjetas (investigación 3) | **convive** con el régimen general: la política debe elegir por producto |

**Regla para escribir `policy/v1`:** cada regla cita su **texto primario** (ley, circular, texto
ordenado) y su fecha de consulta; si solo hay fuente secundaria, la regla se marca como tal. Cuando
dos fuentes chocan, gana el texto primario y el choque se anota en el acta. La política se declara
**sintética** en el reporte aunque se inspire en normas reales.

## 5. Equidad

Ya investigado (investigación 3): los LLM tratan distinto las variantes del español, y el portugués es
una brecha de cobertura. Plan de medición para la gerencia de Protección al consumidor:

- todas las métricas de conversación por idioma, variante y segmento, con tamaño de grupo e
  intervalos de Wilson;
- un par de casos **idénticos salvo la variante** (L1) para aislar el efecto del dialecto;
- ninguna decisión del sistema usa el acento (P12), y se verifica en código;
- disparidad con intervalos que no se solapan se **investiga** y queda en acta.

## 6. Artefactos de la VP Gobierno

1. Ficha GAICF del sistema: frontera, nivel por trabajador, evidencia, plan de monitoreo.
2. `policy/v1` con norma y fecha de consulta por regla, y sus casos borde.
3. Modelo de amenazas por capa MAESTRO con controles y escenarios.
4. Conjunto retenido con huella, escrito por la gerencia de Riesgo.
5. Reporte de equidad.
6. Actas del Comité de Confianza.

## 7. Preguntas abiertas

- ¿Adoptar Cedar como punto de decisión o quedarse en tipos más tabla? Decide el Comité de
  Plataforma con Tecnología.
- ¿Qué plazo de México se usa mientras no se confirme el texto primario? Propuesta: el más
  **protector** para el cliente, declarado.

## Fuentes principales

- [GAICF, marco compatible con SR 26-2](https://arxiv.org/html/2607.04103v1)
- [OPA frente a Cedar, Permit.io](https://www.permit.io/blog/opa-vs-cedar) y [política como código en 2026, Harness](https://www.harness.io/blog/policy-as-code-in-2026-opa-kyverno-cedar-and-what-s-next)
- [MAESTRO, CSA](https://cloudsecurityalliance.org/blog/2025/02/06/agentic-ai-threat-modeling-framework-maestro)
- [BCRA, Protección de los Usuarios de Servicios Financieros](https://www.bcra.gob.ar/archivos/Pdfs/texord/t-pusf.pdf)
- [CONDUSEF, reglas de las UNE](https://www.condusef.gob.mx/?p=contenido&idc=767&idcat=1)
- [El Imparcial, plazos de cargos no reconocidos](https://www.elimparcial.com/dinero/2026/08/05/condusef-establece-que-los-bancos-deben-devolver-el-dinero-de-un-cargo-no-reconocido-en-dos-dias-habiles-si-el-reclamo-se-hace-en-48-horas-aunque-existe-un-plazo-de-90-dias-para-solicitar-la-aclaracion/)
