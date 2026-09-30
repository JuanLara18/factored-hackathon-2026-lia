# Principios del proyecto

Estos principios **no se negocian por tiempo**. Si en algún momento del plan hay que recortar, se
recorta alcance (menos escenarios, menos idiomas, menos pulido), nunca un principio. Cada uno dice
**por qué** existe, **cómo se garantiza** en el código o en el proceso, y **qué lo viola**, para que
se pueda revisar en cualquier momento si se está cumpliendo.

Cada principio tiene un código (P1 a P13) que se cita en el plan, en las decisiones y en las
revisiones.

---

## Sobre cómo se mide

### P1. Los criterios se fijan antes que los resultados

- **Por qué:** si las métricas o los umbrales se definen después de ver el resultado, se eligen a su
  medida y la evaluación deja de valer. El enunciado pide exactamente lo contrario: evaluación sobre
  casos retenidos.
- **Cómo se garantiza:** las métricas, rutas esperadas y umbrales están en
  [01_Interacciones_y_criterios.md](01_Interacciones_y_criterios.md) y se **versionan**. El conjunto
  retenido se **congela** (con su huella) antes de construir el sistema, y solo se corre al final,
  sobre versiones candidatas. Todo cambio de criterio posterior queda en el registro de decisiones
  con su motivo, y se reporta.
- **Lo viola:** ajustar un prompt o un umbral mirando casos del retenido; cambiar la definición de
  "resolución segura" después de medir; quitar casos que salen mal.

### P2. Toda afirmación lleva denominador e incertidumbre, y las fallas se reportan

- **Por qué:** el enunciado pide conteos y denominadores, tamaños de muestra, variabilidad entre
  corridas y los fallos incluidos. Un "95%" sin denominador no dice nada; "cero incidentes" en 50
  casos no es "riesgo cero".
- **Cómo se garantiza:** toda tasa se reporta como *x de n* con intervalo de Wilson; cero eventos,
  con la cota de la regla del tres; comparaciones con McNemar; k corridas por caso con pass^k. La
  tabla de resultados tiene una fila de **fallas** obligatoria.
- **Lo viola:** reportar solo el promedio; esconder casos fallidos; presentar una simulación como
  mejora medida en producción.

### P3. Se separa lo medido, lo simulado y lo proyectado

- **Por qué:** el enunciado prohíbe presentar una comparación offline como mejora en producción.
- **Cómo se garantiza:** el reporte tiene tres secciones con etiqueta explícita: **medición
  offline** (conjunto retenido), **simulación** (usuario simulado, carga simulada) y **proyección**
  (ahorros, con sus supuestos).
- **Lo viola:** "el sistema reduce el costo del contact center en 40%" sin decir que es una
  proyección.

## Sobre cómo se construye

### P4. El modelo de lenguaje entiende y redacta; el código decide y actúa

- **Por qué:** los LLM se pierden en conversaciones de varios turnos, no guardan la
  confidencialidad y no deben inventar reglas (investigaciones 2 y 3). El enunciado pide aplicar
  permisos y política **fuera** del texto del modelo.
- **Cómo se garantiza:** el LLM produce **salidas tipadas** (intención, entidades, necesidad de
  aclarar, borrador de respuesta) y nada más. El flujo, las reglas, los plazos y las acciones viven
  en un **motor determinista** con estado explícito y una **tabla de política versionada**.
- **Lo viola:** una regla de negocio escrita en el prompt ("si el monto supera X, escala"); el
  modelo decidiendo ejecutar una acción; el estado de la conversación guardado solo en el historial.

### P5. Seguridad por construcción

- **Por qué:** los filtros de inyección se evaden hasta en un 100% y los *frameworks* de agentes no
  autorizan cada llamada (investigaciones 3, 8 y 10).
- **Cómo se garantiza:** las herramientas exigen en su firma una `SesionAutenticada` que solo crea
  el servicio de identidad; el cliente sale de la sesión, nunca de un argumento del modelo; las
  acciones con efecto exigen un objeto `Confirmacion`; negación por defecto. Se verifica con
  **mypy o pyright en modo estricto** y con **pruebas de propiedades** sobre invariantes ("nunca una
  acción sin sesión"; "nunca un dato de otro cliente"). Los filtros del gateway son una capa
  **adicional**, y su aporte se mide aparte.
- **Lo viola:** una herramienta que recibe `customer_id` como texto; confiar en que el prompt de
  sistema impida el acceso; declarar "seguro" porque hay un guardarraíl.

### P6. Solo se afirma lo verificado

- **Por qué:** el caso Air Canada (la empresa responde por lo que dice su bot) y el requisito de
  reportar solo acciones verificadas y anclar las respuestas.
- **Cómo se garantiza:** los hechos existen como tipo `HechoVerificado` (lo produce solo una
  herramienta, con fuente y hora) y las reglas como `ReglaDePolitica` (con su versión y norma). La
  redacción solo puede afirmar montos, fechas, estados y plazos a partir de esos tipos. Después de
  cada acción se **relee el estado** antes de informarla.
- **Lo viola:** "listo, radicamos tu disputa" sin haber leído el caso creado; un plazo que el modelo
  "sabe"; un resumen del modelo pasado al traspaso como hecho.

### P7. Un humano siempre disponible, y escalar no es fracasar

- **Por qué:** 87% de los clientes lo exige; Klarna y Commonwealth Bank muestran el costo de
  optimizar contención (investigación 1). El enunciado distingue contención de resolución.
- **Cómo se garantiza:** pedir un humano funciona en cualquier estado; la **contención no es meta**
  en ninguna tabla; la métrica de escalamiento premia escalar bien (sensibilidad) y reporta los
  traspasos innecesarios aparte; el paquete de traspaso es un artefacto evaluado.
- **Lo viola:** retener al cliente para subir la contención; un traspaso sin contexto; medir el
  éxito por "casos sin humano".

### P8. Profundidad antes que amplitud

- **Por qué:** el enunciado lo dice: más flujos no dan puntos; se califica profundidad,
  comportamiento demostrado y criterio.
- **Cómo se garantiza:** **un flujo**, con todas sus rutas, fallas y ataques cubiertos, antes de
  pensar en otro. Toda idea nueva se evalúa con la pregunta "¿profundiza el flujo elegido?".
- **Lo viola:** agregar un segundo flujo a medio terminar el primero.

### P9. Lo simple primero; la complejidad se gana contra una línea base

- **Por qué:** en fraude, el gradient boosting compite con las GNN; en preguntas simples, el RAG
  vectorial empata con GraphRAG; en intención, un clasificador pequeño le gana a un LLM
  (investigaciones 5, 9 y 11).
- **Cómo se garantiza:** cada componente sofisticado (GNN, GraphRAG, LLM grande, varios agentes)
  entra **solo si supera** a su alternativa simple sobre los mismos datos, y esa comparación queda
  en el reporte.
- **Lo viola:** usar una tecnología porque es innovadora sin mostrar que aporta.

## Sobre los datos

### P10. Los datos se auditan antes de modelar

- **Por qué:** el dataset es sintético; el texto puede ser plantilla de la etiqueta y algunas
  relaciones pueden ser ruido (investigación 5). Un 99% por fuga no vale nada.
- **Cómo se garantiza:** antes de entrenar se corren las pruebas de fuga por plantilla, de señal
  (AUC frente a azar) y de calidad contra el contrato. Particiones **por cliente y por tiempo**. Las
  columnas "detectadas" (`detected_intents`, `main_topics`) nunca se usan como características.
- **Lo viola:** entrenar primero y auditar después; partir al azar por fila.

### P11. Privacidad y mínimo privilegio

- **Por qué:** el enunciado prohíbe enviar datos restringidos a modelos externos; CRMArena-Pro
  muestra que los modelos no protegen la confidencialidad por sí mismos.
- **Cómo se garantiza:** al modelo solo le llega lo necesario y **enmascarado**; redacción de datos
  personales en la frontera; credenciales fuera del contexto del modelo y fuera del repositorio;
  política de retención escrita; los datos de todos los clientes nunca están al alcance de una
  consulta del modelo. Los datos del organizador **no salen**: ninguna fila en el repositorio ni en el
  reporte, los casos de evaluación guardan llaves y se materializan localmente, y nada va a un modelo
  externo sin autorización explícita de los organizadores (D-15).
- **Lo viola:** mandar la fila completa del cliente al prompt; texto a consulta libre sobre la base;
  la llave de AWS en un archivo versionado; subir filas del dataset a un repositorio público o
  pegarlas en un ejemplo del reporte.

### P12. Equidad medida, no supuesta

- **Por qué:** los LLM tratan distinto las variantes del español; el enunciado pide comparar por
  idioma y segmento e investigar las disparidades.
- **Cómo se garantiza:** las métricas principales se reportan desagregadas por idioma, variante y
  segmento, con tamaño de grupo e intervalos. Ninguna decisión del sistema depende del acento.
- **Lo viola:** reportar solo el agregado; enrutar decisiones por acento.

## Sobre el proceso

### P13. Todo es reproducible y trazable

- **Por qué:** el enunciado pide instalación reproducible, trazas y explicaciones basadas en
  registros de ejecución, no en el razonamiento oculto del modelo.
- **Cómo se garantiza:** un comando levanta todo; versiones fijadas de dependencias, modelos,
  prompts, política y datos en cada corrida; trazas OpenTelemetry por conversación; **registro de
  decisiones** ([Decisiones.md](../../presidencia/decisiones.md)) con fecha, alternativas y principio que la guía; cada
  exigencia del enunciado mapeada a su evidencia.
- **Lo viola:** un resultado que solo se obtiene en la máquina de alguien; una decisión que nadie
  recuerda por qué se tomó.

### Y uno transversal: honestidad sobre los límites

El enunciado pide *"an honest account of the work required before deployment"*. El reporte final
incluye lo que **no** funciona, lo que se simuló, lo que no se probó y lo que faltaría para operar
de verdad. Esto no es un principio aparte porque está implícito en P2, P3 y P6; se escribe aquí
para que nadie lo olvide.

---

## Cómo se usan

- **Al decidir:** toda entrada del registro de decisiones cita el principio que la guía.
- **Al revisar código:** la lista de "lo viola" de cada principio es la lista de revisión.
- **Al cerrar cada fase del plan:** la compuerta de salida verifica los principios de esa fase.
- **Si dos principios chocan:** gana el de seguridad (P5, P6, P11) sobre los de producto, y los de
  medición (P1, P2, P3) sobre la presentación.
