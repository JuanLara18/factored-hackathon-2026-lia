# LATAM Bank: atención AI-first para cargos no reconocidos. Reporte final

**Cara:** Presidencia y Oficina de Entrega. **Fecha:** 4 de octubre de 2026. **Hackatón:** Factored AI & Data Hackathon 2026.
**Sitio en vivo:** https://latam-bank-hackaton-2026.web.app (banca `/banca/`, consola del experto `/operador/`). **Guion de la demo:** [demo/guion.md](demo/guion.md).

Capítulos: [01 problema](01_problema.md), [02 solución](02_solucion.md), [03 datos y ML](03_datos_y_ml.md), [04 evaluación](04_evaluacion.md), [05 equidad](05_equidad.md), [06 producción](06_produccion.md). Dictamen preliminar de Auditoría: [dictamen_borrador](../../auditoria/reportes/dictamen_borrador.md).

Convención de este reporte: cada cifra lleva su fuente. Lo medido **fuera de línea** (dobles en memoria, cliente simulado, conjunto retenido) se rotula así; nada de esto es una medición de producción ni un ahorro comprobado. Lo proyectado se rotula "supuesto".

## 1. Resumen ejecutivo

**Problema.** LATAM Bank (banco inventado, datos sintéticos de México, Colombia y Argentina) recibió 686.296 contactos de 148.443 clientes. La demanda es estable (0,3% de variación entre los primeros y los últimos doce meses completos). Las quejas por "Cargo no reconocido" son la subcategoría más grande: 12.297 de 67.095 (18,3%), con primera respuesta mediana de 37 horas, 20,4% de SLA incumplido y 24,5% de casos cerrados o resueltos. Un fraude se contiene en minutos, no en días. Por eso el flujo elegido es la **recepción de disputas de transacciones**, con puntaje de priorización 4,00 frente a 3,00 de consultas de cuenta, aunque el liderazgo cambia a consultas de cuenta si el volumen pesa 40% o más ([01_problema](01_problema.md), secciones 1 y 6).

**Solución.** Un agente de disputas (Gemini 3.1 Flash-Lite en Agent Runtime de GEAP, en producción prompt `disputas/agente@1.7.0` y trabajador `disputas` 0.8.0; la evaluación congelada de [04_evaluacion](04_evaluacion.md) se hizo con 1.3.0 y 0.4.0) que entiende y redacta, mientras el código decide: la política `policy/v1` (escalamiento, autenticación por acción, crédito provisional, riesgo, traspaso) vive fuera de la prosa del modelo, las herramientas toman el cliente de la sesión y no de un argumento, y toda acción con efecto exige aprobación explícita en pantalla. Hay una banca en línea de demostración, un chat con aviso de IA, una consola de experto humano con paquete de traspaso de 19 campos y atención en español (usted, vos) y portugués (você) ([02_solucion](02_solucion.md)).

**Datos y aprendizaje.** Capas bronce, plata, oro y platino en BigQuery con dbt, contratos ODCS, reglas de calidad Q-BRZ, manifiesto encadenado y política de frescura con fixture de actualización. Tres componentes aprendidos, todos con línea base, partición sin fuga y abstención: la **recuperación de política con cita**, que sí está en el flujo (acierto 0,897 [0,824; 0,971] contra 0,515 [0,397; 0,632] de BM25 en 68 preguntas de prueba, sin ninguna cita para las 15 preguntas que la política no cubre), el clasificador de motivo (macro-F1 0,399 contra 0,343 de reglas B1, solo con señales del cierre de la llamada) y el riesgo de plazo (**resultado negativo**: AUC 0,504, la pista se abstiene siempre) ([03_datos_y_ml](03_datos_y_ml.md)).

**Evidencia (fuera de línea).** 32 casos retenidos, k=3, 96 corridas contra un cliente simulado ([04_evaluacion](04_evaluacion.md), sección 5.1): resolución automática segura 29/75 (39%; IC95 28% a 50%) sobre todos los casos en alcance y 29/36 (81%) sobre los que debían resolverse; contención 54/75 (72%); resultados inseguros 0/96 (cota superior de 4%); traspasos perdidos 3/18 y innecesarios 8/57; latencia por turno p50 1,41 s y p95 4,61 s; costo del modelo US$ 0,00215 por caso intentado y US$ 0,00483 por resolución segura (tarifa de lista). La línea base de reglas pasa los verificadores en 91% de los casos contra 80% del agente, con intervalos solapados.

**Límites honestos.**

1. El agente **no supera** a la línea base de reglas en este conjunto; lo que aporta es lenguaje (vocabulario no previsto, portugués, registro). La evaluación congelada halló fallas reales: la política ESC-03 no se hacía cumplir en el camino del agente, una orden inyectada de "escalar como urgente" se obedeció en 3 de 3 corridas, `listar_transacciones` con límite 10 escondía cobros y una falla dejaba al cliente sin respuesta ([04_evaluacion](04_evaluacion.md), sección 8). Las cuatro están corregidas en el sistema desplegado (corregidas desde el trabajador 0.5.0; hoy prompt 1.7.0 y trabajador 0.8.0) y comprobadas sobre los mismos casos: R21 pasó de 0/3 a 3/3, R07 de 0/3 a 3/3, la prioridad urgente ya no sale del argumento del modelo y las 15 corridas con falla responden con la plantilla de falla ([04_evaluacion](04_evaluacion.md), anexo "Correcciones posteriores"). Esa comprobación es **post hoc**, sobre casos ya conocidos: las cifras de arriba siguen siendo las de la corrida congelada y no existe todavía una medición limpia del sistema actual sobre casos nuevos.
2. Cliente simulado de la misma familia que el agente, etiquetas de un solo autor, sin juez de modelo (el tono no se midió), dobles en memoria, costo solo del modelo y sin infraestructura ([04_evaluacion](04_evaluacion.md), sección 9).
3. Los datos son sintéticos y no hay clientes de Brasil: el portugués es atención en ese idioma a clientes de la región, sin revisión de un hablante nativo ([LIMITACIONES](../../datos/LIMITACIONES.md), sección de cobertura de idioma). El retenido tiene 31 casos de Colombia y 1 de Argentina, ninguno de México: el corte por país no es evaluable.
4. WhatsApp y voz están diseñados (ADR 0003, 0004, 0008) pero **no desplegados**; lo que corre en producción es el chat web.
5. Producción: una sola instancia, sesiones y confirmaciones en memoria del proceso, Terraform aplicado solo en su parte aditiva, Agent Identity bloqueada por falta de organización, sin prueba de carga ([06_produccion](06_produccion.md)).

## 2. Mapa de criterios del enunciado

El enunciado define seis criterios y un bloque de "Evaluation evidence" ([enunciado](../../docs/enunciado/Enunciado_Factored_Hackathon_2026.pdf)).

| Criterio | Qué pide | Dónde está la evidencia | Estado |
|---|---|---|---|
| 1. Problema respaldado por datos | motivos de contacto, demanda, calidad de datos, restricciones; priorizar el flujo y fijar resultados | [01_problema](01_problema.md) (secciones 2 a 7, 10 figuras en `figuras/`, línea base con n); consultas en `datos/analisis/consultas.sql` | cumplido; el costo por contacto es un supuesto marcado |
| 2. Sistema de IA funcional | contexto, aclaración, respuestas ancladas en datos, herramientas, acciones verificadas | [02_solucion](02_solucion.md) (flujo, herramientas, `AccionVerificada`); demo en [demo/guion.md](demo/guion.md); suite e2e en `tests/e2e/` (81 pruebas, ninguna omitida, 5 oct, [ESTADO](../ESTADO.md)) | cumplido en español y portugués; no hay México ni Brasil en el retenido |
| 3. Automatización controlada | qué responde, qué confirma, cuándo abstiene o transfiere; permisos fuera de la prosa; paquete al humano | `gobierno/politica/v1/` (huella en `manifest.yaml`); [02_solucion](02_solucion.md) secciones 3 a 5; paquete de 19 campos en [clientes/definicion.md](../../clientes/definicion.md) sección 2.5.2 | cumplido; ESC-03 ya lo aplica la herramienta `abrir_disputa` (corrección post hoc del hallazgo 1 de 04) |
| 4. Datos y ML sólidos | preparación repetible, contratos, calidad, linaje, frescura; un componente aprendido contra línea base; sin fuga | [03_datos_y_ml](03_datos_y_ml.md); [datos/README.md](../../datos/README.md); [POLITICA_ACTUALIZACION](../../datos/POLITICA_ACTUALIZACION.md); reportes [clasificador](../../ia/evaluacion/reportes/clasificador_2026-10-03.md) y [riesgo de plazo](../../ia/evaluacion/reportes/riesgo_plazo_2026-10-04.md) | cumplido; un componente en el flujo con ventaja clara sobre su línea base (recuperación de política), uno con mejora modesta y uno con resultado negativo |
| 5. Calidad medida y manejo de fallas | retenido; datos faltantes, sesión vencida, acceso no autorizado, inyección, fallas de herramienta, ambigüedad multilingüe; resultados, latencia, costo, n y límites | [04_evaluacion](04_evaluacion.md) (32 casos: 11 de fallas y seguridad, 5 ambiguos); reportes [geap_pt](../../ia/evaluacion/reportes/geap_pt_2026-10-03.md) y [geap 30 sep](../../ia/evaluacion/reportes/geap_2026-09-30.md) | cumplido con fallas incluidas; los hallazgos 1 a 5 están corregidos y comprobados post hoc, sin retenido nuevo |
| 6. Ruta creíble a operación | trazas, reintentos acotados, caída segura, instalación reproducible; capacidad, monitoreo, accesos, retención, trabajo pendiente | [06_produccion](06_produccion.md); [ARRANQUE](../../tecnologia/infra/ARRANQUE.md); trazas en Cloud Trace sin contenido; explicaciones por fuentes, reglas y registros de ejecución | cumplido en lo existente; retención (TTL de 30 días) y alertas operativas están desplegadas; calidad y equidad en producción siguen como propuesta |

### Resultados exigidos por el enunciado

| Resultado | Cifra (fuera de línea, propuesto, k=3, 96 corridas) | Fuente | Nota |
|---|---|---|---|
| Resolución automática segura | 29/75 (39%) sobre todos los casos en alcance; 29/36 (81%) sobre los que debían resolverse; intentada en 47/75 (63%) | [04_evaluacion](04_evaluacion.md) 5.1 | las categorías E y X no pueden resolver por diseño |
| Contención | 54/75 (72%); contención segura en los que no debían escalar 47/57 (82%) | 04, 5.1 | la contención sola no prueba solución |
| Calidad del escalamiento | perdidos 3/18 (17%), innecesarios 8/57 (14%) | 04, 5.1 y 5.6 | los 3 perdidos son R21 (ESC-03); 7 casos con `debe_escalar` indeterminado |
| Inseguros | 0/96 (IC95 0% a 4%); la línea sin herramientas 1/11 | 04, 5.1 y 5.6 | cero observado no es cero riesgo |
| Eficiencia | por turno p50 1,41 s y p95 4,61 s (n=206); por caso p50 4,16 s y p95 7,50 s (n=93); US$ 0,00215 por caso intentado, US$ 0,00483 por resolución segura | 04, 5.5 | tarifa de lista verificada el 5 oct; solo el agente, en proceso; sin carga ni arranque en frío |
| Comparación por idioma y segmento | resolución segura es 24,6% y pt 38,5% (denominador: todas las corridas); país y segmento no evaluables | 04, sección 6; [05_equidad](05_equidad.md) | brecha no marcada, con mezcla de categorías distinta; muestra insuficiente |
| Línea base | B-reglas: 29/32 casos pasan (91%) contra 77/96 corridas (80%) | 04, secciones 1 y 5.1 | sin diferencia demostrada |
| Variabilidad | pass^1/pass^2/pass^3 = 0,80 / 0,77 / 0,75; resolución segura por repetición 36% a 40% | 04, 5.4 | cliente simulado y reintentos introducen variación |
| Juez de modelo | no se usó; veredictos deterministas validados con 43 corridas revisadas a mano (acuerdo 77%) | 04, sección 7 | el tono no se midió |

Etiquetado de las tres clases de cifras que pide el enunciado:

| Clase | Qué contiene | Dónde |
|---|---|---|
| Medición fuera de línea | todo [04_evaluacion](04_evaluacion.md), los dos reportes de modelos aprendidos y los de GEAP | `ia/evaluacion/reportes/` |
| Simulación | análisis de decisión del riesgo de plazo (k% de mayor riesgo a la cola humana); cliente simulado por modelo | riesgo de plazo secciones 5 y 6; 04 sección 2 |
| Proyección de negocio | costo por contacto de USD 7 a 14 (voz) y 3 a 7 (chat), orden de magnitud mensual para cargo no reconocido | [01_problema](01_problema.md) sección 7; es un supuesto, no un ahorro comprometido |
| Producción medida | ninguna | no existe tráfico real |

## 3. Qué es AI-first aquí

AI-first no significa que el modelo decida todo. Significa que la experiencia se diseña alrededor de lenguaje natural y de un agente que usa herramientas, y que cada decisión con consecuencias se asigna a la capa que mejor la sostiene (D-04: "el LLM entiende y redacta, el código decide"; [decisiones](../decisiones.md)).

### Dónde se usa IA

| Función | Componente | Por qué IA |
|---|---|---|
| Entender el relato del cliente (vos, usted, você, mezcla de idiomas, vocabulario no previsto como "consumo") | Gemini 3.1 Flash-Lite con salida y herramientas tipadas | el lenguaje libre no cabe en reglas; R03 (vos con "consumo") lo resuelve 3 de 3 y las reglas, ninguna ([04](04_evaluacion.md) hallazgo 6) |
| Aclarar ambigüedad (dos cargos candidatos, relato sin datos) | el mismo agente | pregunta lo mínimo en el idioma del cliente |
| Redactar respuestas desde hechos verificados | el agente y plantillas por idioma y registro | las plantillas fijan montos, plazos y confirmaciones |
| Responder preguntas de política con la regla citada, o decir que no hay esa información | recuperador vectorial sobre la base de conocimiento, con umbral de abstención | las preguntas no comparten palabras con la regla: BM25 deja 32 de 68 sin respuesta y el vectorial 3 ([recuperación](../../ia/evaluacion/reportes/recuperacion_2026-10-05.md)) |
| Proponer al experto un resumen y un borrador de respuesta | copiloto de la consola (Gemini con salida tipada) | redactar desde el paquete ahorra tiempo; la persona edita y envía, y el borrador pasa por el filtro de salida |
| Sugerir el motivo de contacto al cerrar | clasificador de árboles de gradiente con abstención | pista de enrutamiento; nunca actúa ([ficha](../../ia/evaluacion/reportes/modelcard_motivo_2026-10-03.md)) |
| Prioridad por riesgo de plazo | modelo de riesgo | sin señal: se abstiene siempre ([ficha](../../ia/evaluacion/reportes/modelcard_riesgo_plazo_2026-10-04.md)) |

### Dónde se prefiere lógica determinista, y por qué

| Función | Mecanismo | Razón |
|---|---|---|
| Autorización: a quién pertenece cada dato, qué nivel exige cada acción | `SesionAutenticada` en la firma de cada herramienta; `acr` por acción en `autonomia.yaml` | el modelo no puede nombrar al cliente; un error de autorización es un resultado inseguro |
| Cuándo escalar (ESC-01 a ESC-04), crédito provisional, bandas de riesgo | `policy/v1` con huella | un plazo o un tope equivocado es materialmente incorrecto; debe ser auditable y versionado |
| Efectos (abrir disputa, bloquear tarjeta, escalar) | herramientas con aprobación de un solo uso y llave de idempotencia | se informa solo lo verificado (`AccionVerificada`) |
| Montos, plazos y confirmaciones en el texto | plantillas | el modelo no inventa cifras |
| País del artículo de política y respaldo ante fallas | filtro por la cuenta de la sesión; BM25 si el servicio de vectores falla | el país no se adivina de la pregunta; una falla de red no puede producir una cita inventada |
| Crédito | el agente no evalúa elegibilidad; solo hay un tope provisional por política | el enunciado prohíbe que el modelo apruebe o invente reglas |
| Fraude | `fraud_score` y `is_fraud` fuera de los datos del agente; banda por regla (alto sobre 30, zona gris desde 25) | el puntaje está contaminado por la etiqueta (2.373 de 2.373 sobre 30 son fraude) ([clasificador](../../ia/evaluacion/reportes/clasificador_2026-10-03.md) sección 9) |

### Compromisos (autonomía, exactitud, latencia, costo, supervisión humana)

| Eje | Decisión | Costo de la decisión | Evidencia |
|---|---|---|---|
| Autonomía | el agente propone; el cliente aprueba en pantalla; nada se ejecuta por texto libre | menos fluidez: la contención es 72% y el agente a veces pregunta de más | 0 acciones sin aprobación en 53 corridas con acción propuesta ([04](04_evaluacion.md) 5.6) |
| Exactitud | la política manda sobre el modelo; ante duda, abstención o traspaso | 8 traspasos innecesarios en 57 y resolución segura de 39% sobre todo el alcance | 04, 5.1 |
| Latencia | un modelo Flash-Lite y un solo agente | respuestas simples y más fallas de ruta que con un modelo mayor (no se comparó) | p95 por turno 4,61 s |
| Costo | Flash-Lite, plantillas, contexto corto (7.056 tokens de entrada por corrida) | menor capacidad de razonamiento | US$ 0,00215 por caso intentado (tarifa de lista) |
| Supervisión humana | botón de persona siempre visible, traspaso con paquete, el experto etiqueta la corrección | costo humano por caso escalado; no se mide en producción | consola `/operador/`; 3 perdidos y 8 innecesarios |
| Aprendizaje | el motivo es pista y el riesgo se abstiene | no se automatiza el enrutamiento | A p ≥ 0,81 automatiza 13,1% con exactitud 85,0% ([clasificador](../../ia/evaluacion/reportes/clasificador_2026-10-03.md) sección 6) |

**Lectura honesta.** En este conjunto la línea de reglas (determinista, 0,04 s por turno, costo cero) iguala o supera al agente en seguridad y en seguir la política. La razón de ser del modelo es cubrir lo que las reglas no entienden y ofrecer una conversación; el costo de ese valor es medible (latencia, tokens, fallas de ruta) y el diseño lo contiene: si el modelo falla, la política no cambia.

## 4. Autoría y datos usados

- **Datos reales, de-identificados o sintéticos.** Todo el dataset del organizador es sintético ([01_problema](01_problema.md) sección 5); ninguna fila sale del repositorio ni de los reportes (D-15, guarda `latam_gobierno.guardas` en CI).
- **Generados por el equipo.** Directorio de 24 comercios (`origen = 'equipo'`), seis clientes de demostración, 32 casos retenidos y 31 de desarrollo, plantillas es y pt, fixture de actualización (10 casos FX-01 a FX-10).
- **Modelos externos.** Solo Gemini en Vertex AI del proyecto, sin contenido en las trazas.

## 5. Cómo reproducir

Instalación, 5 comandos y despliegue: [README](../../README.md) y [ARRANQUE](../../tecnologia/infra/ARRANQUE.md). Evaluación: `uv run python -m latam_ia.evaluacion --retenido` (línea base sin red; el sistema propuesto exige `LATAM_MODELO_PROVEEDOR=geap` y `LATAM_GCP_PROJECT`).
