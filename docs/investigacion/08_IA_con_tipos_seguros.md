# Investigación 8: IA con tipos seguros

**Pregunta:** ¿qué significa "type-safe AI" en la práctica, qué herramientas hay, qué cuesta en
calidad y en latencia, y cómo se convierte en algo **innovador** para este reto y no solo en
"validar un JSON"?

**Hallazgo central:** hay dos niveles. El primero, ya maduro, es **que el modelo devuelva datos
con la forma correcta** (salidas estructuradas). El segundo, poco explotado y mucho más
interesante para un banco, es **usar el sistema de tipos para que lo peligroso no se pueda
escribir**: que una herramienta **no compile** sin una sesión autenticada, que un monto no pueda
existir sin moneda, que un hecho "verificado" y una afirmación del modelo sean **tipos
distintos**. Eso convierte requisitos del enunciado (permisos fuera del texto del modelo, reportar
solo lo verificado, traspaso que separa hechos de interpretación) en **garantías del código**.

---

## 1. Nivel 1: salidas estructuradas

### Las cuatro maneras de obtener datos con forma

| Técnica | Cómo | Garantía | Ejemplos |
|---|---|---|---|
| **Prompt + parser** | se pide el formato y se parsea | ninguna | a mano |
| **Modo JSON / *function calling*** del proveedor | la API entrega JSON o una llamada | JSON válido; el esquema, según el proveedor | OpenAI, Anthropic, Gemini |
| **Validación con reintento** | se valida contra un esquema y, si falla, se devuelve el error al modelo | la forma, al costo de más llamadas | **Instructor**, **PydanticAI** |
| **Decodificación restringida** | una gramática enmascara los tokens inválidos al generar | **la forma, por construcción** | **XGrammar**, Outlines, llguidance |
| **Parseo alineado al esquema** | el modelo escribe libre y un parser tolerante lo corrige con el esquema | la forma, sin restringir la generación | **BAML** |

### Qué dicen las herramientas

- **PydanticAI** ([docs](https://pydantic.dev/docs/ai/overview/), v2.0 de junio de 2026): agentes
  con **salida tipada**, **inyección de dependencias tipada** (`deps_type`: la conexión a la base,
  la sesión del cliente, sin variables globales), validación en dos etapas (sintáctica con
  Pydantic y **semántica** con `output_validator`) y reintento automático con `ModelRetry`. Se
  integra con Logfire y OpenTelemetry. Es el más natural para un agente único dentro de un código
  Python serio.
- **Instructor**: la librería más adoptada para extracción con reintentos.
- **BAML** ([BoundaryML](https://boundaryml.com/blog/schema-aligned-parsing)): un lenguaje propio
  para declarar funciones de LLM con tipos; genera clientes tipados en Python o TypeScript. Su
  **parseo alineado al esquema** reporta **98% de objetos válidos** en el Berkeley Function Calling
  Benchmark sin posprocesamiento, **2 a 4 veces más rápido** que el modo estricto de OpenAI y con
  ~300 tokens menos de prompt por usar definiciones compactas en lugar de JSON Schema
  ([benchmark](https://boundaryml.com/blog/sota-function-calling)). Son cifras del propio
  proveedor.
- **XGrammar** ([MLC](https://github.com/mlc-ai/xgrammar)): el motor por defecto de vLLM, SGLang y
  TensorRT-LLM; **sobrecosto casi nulo** en JSON; 97,1% de exactitud de esquema en estructuras
  anidadas frente a 76,4% de Outlines
  ([comparación](https://futureagi.com/blog/evaluating-llm-structured-output-modes-2026/)). Solo
  aplica si se sirve el modelo uno mismo.

### ¿Estructurar le quita calidad al modelo?

La discusión está abierta y conviene conocerla:

- [*Let Me Speak Freely?*](https://arxiv.org/abs/2408.02442) (EMNLP 2024): las restricciones de
  formato **bajan el razonamiento** (en una tarea, de 70% a 16% con XML) pero **suben la exactitud
  en clasificación**.
- [*Say What You Mean*](https://blog.dottxt.ai/say-what-you-mean.html), la respuesta de .txt (los
  autores de Outlines): el estudio usó prompts distintos para cada condición y no explicó el
  formato; con prompts equivalentes, **lo estructurado ganó** (0,77 frente a 0,65).
- **Consejo práctico que sale de ambos:** poner un **campo de razonamiento antes** del campo de
  respuesta, explicar el esquema en el prompt y comparar con prompts idénticos.
- [*Constraint Tax*](https://arxiv.org/abs/2606.25605) (2026): en modelos abiertos, activar a la vez
  **llamada a herramientas y esquema JSON** hace que el modelo **deje de llamar herramientas**,
  porque la gramática vuelve inalcanzables los tokens de llamada. Solución: **dos pasadas**, primero
  herramientas y luego la respuesta estructurada. Es un error de producción fácil de cometer.
- [*Constrained Decoding Attack*](https://arxiv.org/abs/2503.24191): si **un atacante controla el
  esquema** (enums, diccionarios), puede esconder la carga en la gramática y saltarse la alineación,
  con 94 a 99% de éxito en modelos punteros. En este sistema los esquemas son del equipo, así que
  el riesgo es bajo, pero es un argumento más para **no construir esquemas a partir de texto del
  usuario**.

**Para el reto:** la **clasificación de intención y la extracción de entidades** son exactamente
el tipo de tarea donde lo estructurado **ayuda**. La redacción de la respuesta al cliente es texto
libre, pero **a partir de datos tipados**.

## 2. Nivel 2: los tipos como mecanismo de seguridad

Aquí está lo innovador. En la industria de software hay tres ideas viejas y probadas que casi no
se han llevado a agentes de LLM:

### "Parse, don't validate"

En lugar de validar un dato y seguir pasando el texto crudo, **se parsea una vez a un tipo que no
puede estar mal** y todo lo que viene después recibe ese tipo. Un monto no es `float`: es
`Money(amount: Decimal, currency: Literal["COP","MXN","ARS","BRL","USD"])`. Un identificador de
cliente no es `str`: es `CustomerId`, que solo lo puede construir el servicio de identidad.

### Capacidades como tipos (*capability-based security*)

La capa de herramientas **exige en su firma** un objeto que solo existe si la autenticación pasó:

```python
def radicar_disputa(sesion: SesionAutenticada, cargo: CargoPropio, motivo: MotivoDisputa) -> CasoRadicado: ...
```

- `SesionAutenticada` solo la crea el servicio de identidad, trae el `customer_id` dentro y
  **expira**; el modelo **no puede fabricarla** porque no es texto, es un objeto del proceso.
- `CargoPropio` solo se obtiene consultando las transacciones **de esa sesión**; no se puede pedir
  un cargo de otro cliente porque no hay forma de construir el tipo.
- Si el modelo "decide" llamar la herramienta sin haber autenticado, **el programa no tiene con
  qué llamarla**. La autorización deja de ser una regla que alguien tiene que acordarse de revisar.

Es la misma idea de **CaMeL** (investigación 3), que rastrea la procedencia de cada dato con
capacidades, y la respuesta a *Capability Gates Are Not Authorization*: autorización **por
llamada, con los argumentos concretos**, pero garantizada por construcción.

### Estados tipados (*typestate*)

El flujo de disputa es una **máquina de estados** donde cada transición exige el tipo del estado
anterior: no se puede llegar a `CasoRadicado` sin pasar por `CargoIdentificado` y
`ConfirmadoPorCliente`. Las **acciones que requieren confirmación** (lo pide el enunciado) se
vuelven transiciones que exigen un objeto `Confirmacion` emitido cuando el cliente dijo "sí".

### Hechos verificados frente a afirmaciones del modelo

El enunciado pide **reportar solo acciones verificadas** y que el traspaso distinga **hechos
verificados** de lo demás. Con tipos:

- `HechoVerificado[T]`: lo produce **solo** una herramienta, lleva la fuente y la hora.
- `Interpretacion`: lo que dijo el modelo (la intención inferida, un resumen).
- La función que redacta la respuesta al cliente **solo acepta** `HechoVerificado` para afirmar
  montos, fechas y estados. El paquete de traspaso tiene dos listas con tipos distintos.

**Es auditable por construcción** y responde directamente a *"Provide explanations based on
sources, policy rules, and execution records"*.

## 3. Cómo se vería en el prototipo

| Pieza | Herramienta sugerida | Qué garantiza |
|---|---|---|
| Modelo de dominio (sesión, cliente, cargo, dinero, caso, motivo) | **Pydantic v2** con tipos propios | datos imposibles de construir mal |
| Comprensión (intención, entidades, necesidad de aclarar) | **PydanticAI** o BAML con salida tipada | forma correcta, reintento acotado |
| Motor de flujo | máquina de estados con **transiciones tipadas** | no hay atajos entre estados |
| Capa de herramientas | funciones que exigen `SesionAutenticada` y `Confirmacion` | autorización por construcción |
| Redacción | entrada tipada solo con `HechoVerificado` | no se afirma nada no verificado |
| Verificación estática | **mypy** o **pyright** en modo estricto en CI | los errores de este tipo se atrapan antes de correr |
| Pruebas | **Hypothesis** (pruebas basadas en propiedades) | "para cualquier secuencia de mensajes, nunca se llama una acción sin sesión" |

**Las pruebas basadas en propiedades** son otra pieza poco usada con agentes: en lugar de casos
escritos a mano, se generan miles de secuencias (incluidas las adversariales) y se verifica un
**invariante**. Es una evidencia de seguridad mucho más fuerte que "probamos 20 inyecciones".

## 4. Qué tan innovador es

La idea de salidas estructuradas es estándar en 2026. Lo que **no** es estándar, según lo que
aparece en la literatura y en los *frameworks*, es:

1. **La autorización como tipo**, no como verificación en tiempo de ejecución. Los *frameworks*
   de agentes auditados en 2026 no la traen por defecto.
2. **La distinción tipada entre hecho verificado e interpretación**, que ata la redacción y el
   traspaso a la evidencia.
3. **Invariantes de seguridad probados con propiedades** sobre el agente completo.

Se puede presentar como **"seguridad por construcción"**, conectando con CaMeL y los seis patrones
de la investigación 3: los artículos lo proponen con intérpretes propios; aquí se logra con el
sistema de tipos de Python y un verificador estático, que es más simple de mantener.

**Límite honesto:** Python no es un lenguaje con tipos fuertes en tiempo de ejecución; la
garantía viene del verificador estático más los constructores privados. Un atacante con acceso
al proceso lo rompe, pero el modelo de lenguaje no, porque **el modelo solo produce texto** que
se parsea a tipos que no incluyen capacidades.

## Fuentes principales

- [PydanticAI](https://pydantic.dev/docs/ai/overview/)
- [BAML, parseo alineado al esquema](https://boundaryml.com/blog/schema-aligned-parsing)
- [XGrammar](https://github.com/mlc-ai/xgrammar)
- [Let Me Speak Freely?](https://arxiv.org/abs/2408.02442) y [Say What You Mean](https://blog.dottxt.ai/say-what-you-mean.html)
- [Constraint Tax](https://arxiv.org/abs/2606.25605)
- [Constrained Decoding Attack](https://arxiv.org/abs/2503.24191)
- [CaMeL](https://arxiv.org/abs/2503.18813)
