# Investigación 4: cómo se evalúa un agente de atención

**Pregunta:** ¿cómo se demuestra, con números defendibles, que el sistema propuesto es mejor que la
línea base y que es seguro? El enunciado es muy específico: mismo conjunto retenido para línea base
y propuesta, **resolución automática segura** separada de **contención**, **calidad de
escalamiento**, **resultados inseguros con conteos y denominadores**, **latencia p50 y p95**,
**costo por caso y por resolución**, variabilidad entre corridas, jueces LLM **validados contra
humanos o reglas**, y comparación **por idioma y segmento**.

**Hallazgo central:** la evaluación de agentes tiene tres trampas bien documentadas, y el enunciado
parece escrito para castigarlas: **medir un solo intento** (esconde la inconsistencia), **confiar
en un juez LLM sin validarlo** y **confundir ambigüedad de la política con error del agente**.

> **Nota del 26 de septiembre de 2026, tras la [auditoría del dataset](13_Auditoria_del_dataset.md):** las transcripciones son plantillas sin relación con la categoría y las quejas no enlazan con transacciones, así que **no sirven como semillas** de casos (sección 5); `was_escalated` no tiene señal, así que la línea base de negocio (sección 7) se reporta con esa advertencia. Las semillas salen de transacciones y productos reales más conversaciones escritas por el equipo.


> **Nota del 27 de septiembre de 2026 (Auditoría, C-1):** en la sección 1, con pass^k ≈ p^k, un agente con 90% de éxito en k = 8 queda en **0,43** (0,9^8), no en 57%.

---

## 1. Los benchmarks de referencia

### τ-bench y τ²-bench (Sierra)

[τ-bench](https://github.com/sierra-research/tau-bench) es el estándar de agentes de atención:
dominios de **retail y aerolínea**, un **usuario simulado por LLM**, herramientas sobre una base de
datos, una **política en lenguaje natural**, y el éxito se mide **comparando el estado final de la
base de datos** con el esperado, no el texto.

**La métrica que hay que copiar: pass^k.** La probabilidad de que el agente acierte **en las k
corridas**, no en al menos una. Si el éxito por intento es $p$, pass^k ≈ $p^k$: un agente con 90% de
éxito baja a **57% de consistencia en k = 8**. Para un banco, la consistencia es lo que importa: el
mismo cliente con el mismo problema debería obtener el mismo resultado.

[τ²-bench](https://arxiv.org/pdf/2506.07982) añade **control dual**: el usuario también tiene
herramientas (como cuando un agente guía al cliente a reiniciar algo en su app). En el dominio de
telecomunicaciones el éxito cae **18 a 25 puntos** frente a actuar solo; GPT-4.1 pasa de 74% y 56%
en retail y aerolínea a **34%** ([tabla pública](https://artificialanalysis.ai/evaluations/tau2-bench)).

### FraudBench (agosto de 2026): el más cercano al reto

[*Stress-Testing Policy-Grounded Banking Agents Against Adaptive Fraud*](https://arxiv.org/html/2608.18136).
Un agente bancario con **17 herramientas** (verificación de identidad, bloqueo de tarjeta, cambio de
PIN, límites, transferencias, **radicación de disputas**, abonos, escalamiento) y **698 documentos de
política**. 107 tareas adversariales.

- **Verificación de identidad con dos de cuatro campos**, registrada.
- **Resolución segura** = no ejecutar acciones prohibidas, cumplir la disposición requerida
  (negar, escalar, preservar) y no filtrar datos. **Depende del historial**: una solicitud válida
  sola se vuelve insegura después de sondeos o intentos fallidos previos.
- **El escalamiento se califica también por el motivo**: un motivo equivocado confunde al humano
  que recibe.
- **Resultados**: el mejor modelo defiende **64,5%**; cuando además tiene que **recuperar** la
  política correcta, cae a **51%** (13 puntos solo por recuperación).
- **Lo más difícil**: mulas de dinero (1 o 2 de 9), cadenas adaptativas (4 a 9 de 17) y **fraude de
  primera parte**, cuando el propio cliente disputa algo que su historial contradice (2 a 7 de 9).
- **Lecciones textuales**: autenticación no es autorización; validez local no es seguridad global;
  **seguridad no es negarse**, hay que completar lo legítimo y bloquear el fraude, son dos ejes.

**Para el reto:** el diseño de sus tareas (objetivo, lo que sabe el atacante, estado de la base,
tácticas de presión) es una plantilla directa para los casos adversariales, y el **fraude de
primera parte** es un caso real del flujo de disputas que el dataset permite construir
(`is_fraud`, historial de reclamos, `is_repeat_complainer`).

### Otros

- [CRMArena-Pro](https://arxiv.org/abs/2505.18878): 58% un turno, **35% varios turnos**,
  confidencialidad casi nula.
- [Journey-Bench, *Beyond IVR*](https://arxiv.org/pdf/2601.00596): adherencia a procedimientos
  operativos (orden de pasos, validaciones, excepciones).
- [*Benchmarks Are Not Validation*](https://arxiv.org/html/2607.28840): lista de pruebas de
  aceptación para agentes financieros que coincide casi punto por punto con el enunciado: flujo
  normal, ambiguo, evidencia faltante o contradictoria, límites de permisos, prevención de acciones
  inseguras, escalamiento, **estabilidad entre corridas**, detección de bucles, límites de costo y
  latencia, recuperación de fallas de herramientas e inyección de prompts.

## 2. Trampa 1: la política ambigua disfrazada de error del agente

[*Policy Loopholes in Agent Evaluation*](https://arxiv.org/pdf/2609.14400) muestra que parte de
los errores medidos en benchmarks tipo τ-bench **son ambigüedad de la política**, no fallas del
agente: la misma acción es correcta o incorrecta según cómo se lea la regla. Recomendaciones:

- escribir la política con **casos borde explícitos**;
- que las etiquetas indiquen **la versión de la política** con que se hicieron;
- **marcar como ambiguos** los casos en que los anotadores discrepan, en lugar de forzar una
  etiqueta binaria.

**Para el reto:** la política sintética (plazos, montos, qué exige confirmación) se escribe
**antes** de etiquetar, versionada, y cada caso del conjunto de evaluación lleva la versión.

## 3. Trampa 2: el juez LLM sin validar

El enunciado: *"If you use a model to judge answers, document its rubric and validate a sample
against human or deterministic judgments."*

**Lo que dice la literatura:**
- Sesgos documentados: posición, **verbosidad**, autopreferencia (el juez favorece salidas de su
  misma familia) ([encuesta](https://www.sciencedirect.com/science/article/pii/S2666675825004564),
  [sesgo de posición, IJCNLP 2025](https://aclanthology.org/2025.ijcnlp-long.18/)).
- [*Reliability without Validity*](https://arxiv.org/html/2606.19544v1): un juez puede ser **muy
  consistente y aun así no medir lo que se quiere**. Consistencia no es validez.
- Bien calibrado, un juez llega a **más del 80% de acuerdo con humanos**, el mismo nivel que entre
  humanos; pero **hay que calibrarlo en cada tarea**.
- [*Trust or Escalate*, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf):
  el juez **se abstiene cuando no está seguro** y escala a un juez más fuerte o a un humano, con
  una **garantía estadística de acuerdo con humanos**. Es la misma idea de abstención aplicada al
  evaluador.

**Nubank lo hizo así** ([arXiv 2606.08867](https://arxiv.org/abs/2606.08867)): consenso de tres
anotadores, kappa de Cohen entre jueces con umbral de 0,80, optimización de la rúbrica con GEPA, y
eligieron el juez que **priorizaba detectar errores** sobre la exactitud global.

**Protocolo mínimo para el reto:**
1. **Lo que se puede verificar con reglas, se verifica con reglas**: estado final de la base (¿se
   radicó la disputa con el monto correcto?), acciones ejecutadas, datos filtrados (expresiones
   regulares sobre la respuesta), traspaso sí o no. Esto cubre la mayor parte de la evaluación sin
   juez.
2. El juez LLM solo para lo que no se puede verificar con reglas: tono, claridad, si la respuesta
   está **anclada** en los hechos verificados.
3. Rúbrica escrita y versionada.
4. **Muestra etiquetada por humanos** (por ejemplo, 50 a 100 casos, los dos del equipo), con acuerdo
   entre anotadores (κ) y acuerdo juez-humano (κ, precisión y recuperación para detectar fallas).
5. Juez de otra familia que el modelo evaluado, para evitar la autopreferencia.

## 4. Trampa 3: un solo intento

Los LLM no son deterministas. El enunciado pide *"repeated-run variability where relevant"*.

- Correr cada caso **k veces** (por ejemplo k = 3 a 5) y reportar **pass^k** además de la tasa media.
- Reportar **intervalos de confianza**: con 100 casos, una tasa de 90% tiene un intervalo de Wilson de
  aproximadamente [83%, 94%]. Con muestras pequeñas, **cero fallas observadas no significa riesgo
  cero** (lo dice el enunciado): la regla del tres da una cota superior de ≈ 3/n; con 50 casos
  seguros, el riesgo real puede llegar a ~6%.
- **Fijar versiones** de modelo, prompt y política en cada corrida.

## 5. El conjunto de evaluación

**Composición**, alineada con lo que pide el enunciado:

| Tipo de caso | Qué prueba | Resultado de referencia |
|---|---|---|
| Resolución normal | el flujo completo | estado final esperado |
| Ambiguo o no soportado | aclarar o abstenerse | pregunta de aclaración o negativa con alternativa |
| Requiere humano | el traspaso | traspaso con paquete completo y motivo correcto |
| Datos incorrectos o faltantes | no inventar | aclarar o escalar |
| Sesión expirada | reautenticación | sin repetir acciones |
| Acceso no autorizado | autorización | rechazo en la capa de herramientas |
| Inyección de prompts | contención | sin efecto |
| Falla de herramienta | reintento acotado y caída segura | falla honesta o traspaso |
| Ambigüedad multilingüe | ES, PT, mezcla | aclaración |
| Fraude de primera parte | coherencia con el historial | escalamiento con evidencia |

**De dónde salen los casos:**
- **Semillas reales del dataset**: transcripciones y reclamos de `call_transcripts` y `complaints`
  del motivo elegido, con el estado de base de datos real de ese cliente.
- **Usuario simulado** a partir de esas semillas, con personas (tono, variante, paciencia), al
  estilo de Nubank y τ-bench.
- **Casos adversariales escritos a mano**, al estilo de FraudBench.
- **Portugués**: traducción de casos más casos nativos; reportar que no hay datos reales en
  portugués.

**Separación estricta:** los casos de evaluación **no se usan** para ajustar prompts ni umbrales.
Un conjunto de desarrollo aparte para iterar; el retenido se corre al final.

## 6. Las métricas, tal como las define el enunciado

| Métrica | Definición operativa | Denominador |
|---|---|---|
| **Resolución automática segura** | caso elegible que llega al resultado correcto y conforme a la política sin humano | **todos los casos del alcance**; y además la fracción en que se intentó automatizar |
| **Contención** | el caso termina sin traspaso | todos; **se reporta pero no se celebra** |
| **Calidad de escalamiento** | los que debían escalar escalaron, con paquete útil y motivo correcto | casos que requieren escalamiento; **traspasos faltantes e innecesarios** por separado |
| **Resultados inseguros** | divulgación o acción no autorizada, o resultado materialmente incorrecto | todos, **con conteo y denominador** |
| **Eficiencia** | latencia p50 y p95 de extremo a extremo; costo por caso intentado y por resolución exitosa | con supuestos de costo explícitos; "no definido" si no hay resoluciones |
| **Equidad** | las anteriores por idioma, variante y segmento | con intervalos; señalar muestras pequeñas |

Y una del mundo real que conviene añadir aunque sea simulada: **tasa de repetición** en los
traspasos (investigación 2).

**Etiquetado honesto:** separar **mediciones offline**, **simulaciones** y **ahorros proyectados**. El
enunciado prohíbe presentar una comparación offline como mejora medida en producción.

## 7. La línea base

El enunciado exige comparar **línea base y propuesta sobre la misma carga retenida**. Opciones, de
más simple a más fuerte:

1. **Reglas o palabras clave**: el "Software 1.0" (enrutamiento por palabras clave y respuestas
   fijas). Fácil de construir y de superar.
2. **El proceso actual reconstruido del dataset**: tasa de resolución en primer contacto
   (`was_resolved`), escalamiento (`was_escalated`), duración y espera reales del motivo elegido.
   Es la línea base **de negocio**, no del sistema.
3. **Un LLM con un solo prompt, sin flujo ni herramientas controladas**: la línea base que muestra
   qué aporta la arquitectura.

Lo más convincente es reportar **las tres**: la primera y la tercera sobre los mismos casos
retenidos, y la segunda como contexto de negocio, sin mezclarla con las otras.

## 8. Abstención: evaluar cuándo el sistema sabe que no sabe

La abstención es una métrica en sí misma. El marco es la **predicción selectiva**: se sacrifica
cobertura (casos que el sistema intenta) a cambio de error (casos que resuelve mal)
([encuesta de abstención](https://www.researchgate.net/publication/393331033_Know_Your_Limits_A_Survey_of_Abstention_in_Large_Language_Models)).
La **curva de riesgo y cobertura** (error frente a fracción de casos intentados, al mover el umbral
de confianza) es la forma estándar de mostrarla, y permite **elegir el umbral de escalamiento con
datos**, que es justo lo que pide el enunciado sobre justificar umbrales. La **predicción conformal**
([abstención conformal](https://www.emergentmind.com/topics/conformal-abstention)) da garantías
de error para un umbral calibrado en un conjunto aparte.

## Fuentes principales

- [τ-bench](https://github.com/sierra-research/tau-bench) y [τ²-bench](https://arxiv.org/pdf/2506.07982)
- [FraudBench](https://arxiv.org/html/2608.18136)
- [Policy Loopholes in Agent Evaluation](https://arxiv.org/pdf/2609.14400)
- [Benchmarks Are Not Validation](https://arxiv.org/html/2607.28840)
- [Trust or Escalate, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/08dabd5345b37fffcbe335bd578b15a0-Paper-Conference.pdf)
- [Reliability without Validity](https://arxiv.org/html/2606.19544v1)
- [Nubank, arXiv 2606.08867](https://arxiv.org/abs/2606.08867)
