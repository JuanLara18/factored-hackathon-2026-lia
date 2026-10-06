# Recuperación de política con cita: componente aprendido contra línea base

**Cara:** VP IA, con Clientes y Gobierno. **Fecha:** 5 de octubre de 2026.
**Código:** `tecnologia/src/latam_tecnologia/herramientas/conocimiento.py` (recuperadores) e `ia/src/latam_ia/recuperacion/` (evaluación). **Datos:** `clientes/conocimiento/articulos.yaml` (16 artículos) e `ia/evaluacion/recuperacion/consultas.yaml` (131 preguntas con juicio de relevancia). **Reproducir:** `uv run python -m latam_ia.recuperacion` (con `LATAM_GCP_PROJECT`; `--sin-red` corre solo BM25 y el azar).

Todo es medición fuera de línea sobre preguntas escritas por el equipo. No es una medición de producción.

## 1. Qué decide este componente

Cuando un cliente pregunta por una regla del banco ("¿me abonan algo mientras revisan?", "¿puedo reclamar un cobro revertido?"), el asistente no responde de memoria: llama a `consultar_politica`, que devuelve el artículo de la base de conocimiento que responde la pregunta y las reglas de `policy/v1` que lo sustentan, o nada. Sin fuente, el asistente dice que no tiene esa información. El componente toma dos decisiones: **qué artículo** y **si hay artículo**. La segunda es la que protege: citar una regla para una pregunta que la política no cubre es un resultado materialmente incorrecto.

Lo que es determinista y no se aprende: el país. Un artículo marcado con país (México, Colombia, Argentina) solo vale para clientes de ese país, y el país sale de la cuenta de la sesión, no de la pregunta.

## 2. Datos y juicios de relevancia

| Aspecto | Hecho |
|---|---|
| Base | 16 artículos en español y portugués, cada uno con las reglas de `policy/v1` de las que sale (`ESC-01` a `ESC-05`, `TRA-01` a `TRA-07`, niveles de autenticación, crédito provisional por país) |
| Preguntas | 131: 101 con un artículo relevante (de 6 a 7 por artículo) y 30 que la base no cubre (tasas, cupos, horarios, inversiones) |
| Idioma | 89 en español, incluidas de voseo, y 42 en portugués |
| Quién las escribió | el equipo, un solo autor, antes de correr ningún recuperador; no hay segundo anotador ni acuerdo entre anotadores |
| Relevancia | binaria y única: un artículo por pregunta. Las preguntas generales de crédito provisional (K-01) tienen variantes por país (K-02 a K-04) que en la práctica también responderían; aquí cuentan como error |
| Fuga | ninguna pregunta repite un escenario de desarrollo ni de los conjuntos retenidos del agente |

**Partición.** Mitad a validación y mitad a prueba dentro de cada artículo, con semilla 202616737: 63 de validación y 68 de prueba. El umbral de abstención y el margen se eligen solo en validación; la prueba se evalúa una vez con esos valores.

## 3. Sistemas

| Sistema | Qué es |
|---|---|
| Azar | puntajes aleatorios con la misma regla de decisión; piso de referencia |
| BM25 | línea base léxica sobre el texto de cada artículo en los dos idiomas, sin tildes ni palabras vacías; no usa red |
| Vectorial | `gemini-embedding-001` de Vertex AI, 768 dimensiones, tipo de tarea de consulta y de documento; similitud de coseno contra el mejor de los dos idiomas de cada artículo. Modelo preentrenado, sin ajuste |

**Representación.** Los vectores de los artículos se calculan una vez y se guardan en el repositorio (`vectores.json`, con la huella de los artículos); en producción solo se calcula el vector de la pregunta. Si los artículos cambian y los vectores no, el sistema usa BM25 en lugar de citar con vectores viejos.

**Métrica y umbral.** Cada pregunta termina en uno de cinco resultados: respuesta correcta, abstención correcta, sin respuesta (había artículo y no se citó), cita equivocada (otro artículo) y cita falsa (se citó algo para una pregunta sin cobertura). El costo pesa 5 una cita equivocada o falsa y 1 una pregunta sin respuesta, porque abstenerse solo obliga al cliente a preguntar a una persona y citar mal lo desinforma. El umbral es el de menor costo medio en validación. Los intervalos son bootstrap sobre preguntas (2.000 réplicas).

## 4. Resultados en prueba (68 preguntas, una sola evaluación)

| Sistema | Umbral | Acierto (IC95) | Correctas | Abstención correcta | Sin respuesta | Cita equivocada | Cita falsa | Costo medio | Recall@1 | Recall@3 | MRR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Azar | 1,000 | 0,221 [0,132; 0,324] | 0 | 15 | 52 | 1 | 0 | 0,838 | 0,057 | 0,264 | 0,246 |
| BM25 | 5,426 | 0,515 [0,397; 0,632] | 20 | 15 | 32 | 1 | 0 | 0,544 | 0,642 | 0,774 | 0,733 |
| Vectorial | 0,682 | **0,897** [0,824; 0,971] | 46 | 15 | 3 | 4 | 0 | 0,338 | 0,925 | 0,981 | 0,958 |

Recall y MRR se calculan sin umbral sobre las 53 preguntas de prueba que tienen artículo.

Por idioma, en prueba: el vectorial acierta 40 de 46 en español (0,870) y 21 de 22 en portugués (0,955); BM25, 21 de 46 (0,457) y 14 de 22 (0,636).

**Lectura.**

1. El recuperador vectorial supera a BM25 con intervalos que no se solapan (0,897 contra 0,515). La diferencia viene sobre todo de preguntas que no comparten palabras con el artículo: BM25 deja 32 sin respuesta y el vectorial 3.
2. **Ninguno citó una fuente para las 15 preguntas sin cobertura.** Quince preguntas no demuestran que no pueda pasar: la cota superior al 95% de la tasa de cita falsa es de 18%.
3. Las cuatro citas equivocadas del vectorial: dos son preguntas generales de crédito provisional que recibieron el artículo de Argentina (el filtro de país de producción lo impide para clientes de otro país, y aquí no se aplicó), una confundió sesión vencida con confirmación en pantalla y otra confundió "no recuerdo los datos de la compra" con el artículo de datos que se muestran. Las tres sin respuesta son preguntas coloquiales o indirectas.
4. El acierto en validación del vectorial es 1,000 porque el umbral se eligió ahí; la cifra honesta es la de prueba.

## 5. Límites

- **Muestra pequeña y de un solo autor.** 131 preguntas, 68 en prueba, de 2 a 4 por artículo en prueba. Quien escribió las preguntas escribió también los artículos, lo que favorece a cualquier recuperador.
- **Base pequeña.** Con 16 artículos el problema es más fácil que con una base real; el margen sobre BM25 no se puede extrapolar.
- **La pregunta que llega no es la del cliente.** El agente escribe el argumento de la herramienta y a veces lo resume. En desarrollo eso dejó preguntas bajo el umbral, y por eso la herramienta vuelve a buscar con el mensaje original si la primera búsqueda no trae fuente. Ese segundo intento no está medido aquí; se mide de punta a punta en los casos P del retenido v3.
- **No mide la respuesta.** Que el artículo sea el correcto no garantiza que el asistente lo transmita bien; eso lo verifican `citas` y `cita_sin_fuente` en el arnés del agente.
- **Dependencia.** Un llamado de red por pregunta de política (tope de 8 s). Si falla, responde BM25 con su propio umbral: más preguntas sin respuesta, ninguna cita inventada.
- **Portugués** sin revisión de un hablante nativo.

## 6. Decisión

Se usa el recuperador vectorial con umbral 0,6823, margen 0,01 y hasta dos artículos, con BM25 de respaldo (`clientes/conocimiento/recuperacion.yaml`). La pista solo informa: nunca ejecuta una acción ni cambia la ruta del caso.
