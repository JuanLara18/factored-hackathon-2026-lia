# Equidad del servicio: línea base histórica y evaluación del sistema

**Cara:** VP Gobierno (equidad) con VP Datos. **Fecha:** 4 de octubre de 2026.
**Código:** `datos/src/latam_datos/analisis/equidad.py` (línea base), `gobierno/src/latam_gobierno/equidad.py` (reglas y tabla del sistema).
**Reproducir:** `uv run python -m latam_datos.analisis.equidad` (con `--desde-cache` no consulta BigQuery).
**Figuras:** `figuras/equidad_01_disputas.png`, `equidad_02_brechas_ajuste.png`, `equidad_03_contactos.png`.

El enunciado pide comparar resultados de servicio por idioma y por segmentos autorizados, declarar las muestras pequeñas e investigar las disparidades. Este informe hace tres cosas: mide cómo trató el servicio histórico a cada grupo, fija el corte y las reglas con que se medirá al agente nuevo, y propone cómo vigilarlo en producción.

## 1. Atributos y por qué

| Atributo | Fuente | Uso | Razón |
|---|---|---|---|
| País de la cuenta (MX, CO, AR) | `plata_customers` | decidir y auditar | fija la ley aplicable; es la única variable demográfica que el motor usa |
| Idioma (es, pt) | conversación | elegir idioma y cola; auditar | el servicio en portugués es un compromiso de la misión |
| Segmento comercial | `plata_customers` | solo auditar | R-GOB-46; nunca decide ni prioriza |
| Canal | complaints, interactions | auditar | confusor natural de los tiempos |
| Acento detectado | `plata_customers`, interactions | solo auditar | proxy del idioma en el histórico; nunca decide (R-GOB-51) |
| Franja de edad (menos de 65, 65 o más; bandas como control) | `plata_restringida_clientes` | solo auditar, agregado | R-GOB-46 |
| Género | `plata_restringida_clientes` | solo auditar, agregado | R-GOB-46 |
| Estado civil, educación | `plata_restringida_clientes` | no se usan | minimización; solo con acta que lo justifique |

Garantías: los atributos restringidos entran únicamente en consultas de agregación; cada celda con menos de 20 casos se descarta dentro de BigQuery (k-anonimato 20) y el código vuelve a verificarlo antes de guardar. No se versiona ninguna fila por cliente: `equidad_cifras.json` y `equidad_resumen.json` solo traen conteos por grupo. La guarda del repositorio (`latam_gobierno.guardas`) pasa limpia.

## 2. Método

**Ámbitos.** Quejas por cargo no reconocido (subcategoría de `plata_complaints`, 12.297 casos; sirve de línea base de disputas) y todas las quejas (67.095). Contactos transaccionales (240.056, donde caen las disputas por chat y voz) y todos los contactos (686.296).

**Métricas.** Quejas: con primera respuesta registrada, horas a la primera respuesta (mediana), incumple SLA, resuelta (tiene fecha de resolución), escalada (estado `Escalated`) y CSAT de resolución (1 a 5). Contactos: resuelto, escalado, requiere seguimiento, espera en segundos (mediana) y CSAT de encuesta (`main_score`, escala 1 a 7).

**Regla de disparidad** (R-GOB-48). Cada grupo se compara con el mejor de su dimensión entre los de 30 casos o más. Se marca para investigar si la brecha peor es de 5 puntos o más con el intervalo de Newcombe sin el cero, o si la razón peor sobre mejor cruza la regla de los cuatro quintos (menor que 0,8, o mayor que 1,25 en tasas malas) con el intervalo sin el cero. Tiempos: mediana mayor que 1,25 veces la del mejor grupo. CSAT: diferencia de 0,25 puntos o más con el intervalo del 95% sin el cero. Un grupo con menos de 30 casos se marca "muestra insuficiente".

**Ajuste por mezcla** antes de atribuir. Para cada grupo se calcula la tasa esperada si tuviera la misma mezcla que el conjunto: canal, tipo de caso, categoría, moneda y tercil del monto reclamado para quejas; canal, tipo de interacción, motivo y tercio del día para contactos. La tasa ajustada es la global por el cociente observado sobre esperado, y se repite la comparación. Una brecha marcada que desaparece al ajustar se llama "explicada por mezcla"; si sigue, "persiste tras ajustar". El canal no se ajusta contra sí mismo (lo anularía por construcción).

## 3. Resultados de la línea base

Se evaluaron 392 comparaciones de proporciones (ámbitos, dimensiones, grupos y métricas), 102 de tiempos y 107 de CSAT. El servicio histórico trata casi igual a todos los grupos.

- **Contactos: ninguna disparidad.** En los 686.296 contactos y los 240.056 transaccionales, resolución, escalamiento, seguimiento y espera difieren en menos de 0,5 puntos entre países, segmentos, canales, acentos, edades y géneros (resuelto 91,4% a 91,6% por acento, género y edad; espera mediana de 119 a 120 segundos).
- **Tiempos: ninguna disparidad.** La mediana a primera respuesta en disputas es de 36 a 38 horas en todos los grupos.
- **Quejas por cargo no reconocido: seis marcas, ninguna con brecha grande y sostenida.**

| Grupo | Métrica | Tasa | Referencia | Brecha | Tras ajustar | Lectura |
|---|---|---|---|---|---|---|
| Edad 18 a 24 (n=678) | con primera respuesta | 58,0% | 35 a 44: 63,8% | menos 5,8 pp | menos 5,8 pp | persiste, brecha de 5 pp o más |
| Segmento Plus (n=3.029) | incumple SLA | 21,6% | Student: 16,9% | 4,7 pp, razón 1,28 | 4,3 pp | persiste, solo por razón |
| Segmento Plus | escalada | 5,4% | Student: 3,5% | 1,9 pp, razón 1,55 | 1,9 pp | marcada solo por razón, sobre tasas bajas |
| Edad 25 a 34 y 45 a 54 | escalada | 5,5% y 5,4% | 35 a 44: 4,1% | 1,3 a 1,5 pp | menos de 1,5 pp | explicada por mezcla |
| Edad 55 a 64 | escalada | 5,7% | 35 a 44: 4,1% | 1,6 pp | 1,5 pp | persiste, solo por razón |

- **CSAT de resolución.** Una marca: canal sucursal (n=95, media 2,68) frente a web (3,14), 0,46 puntos menos. El CSAT de quejas cubre apenas el 1,6% de los casos.
- **Género y acento.** Sin marcas. La menor tasa de respuesta es la de género "O" en disputas (59,5% frente a 63,1% en F, 3,6 pp, bajo el umbral), que se vigila.

La figura 2 muestra que el ajuste por mezcla casi no mueve las brechas: la mezcla de productos, montos y canales no explica lo poco que hay.

## 4. Investigación de las marcas

1. **Edad 18 a 24, primera respuesta.** La brecha aparece en todos los cortes donde hay casos suficientes: AR 55,1%, CO 58,3%, MX 58,9%; canales call center 57,0%, correo 50,8%, web 59,5%; segmentos Basic a Premium entre 57% y 62%. No es mezcla ni un país concreto. Tres razones piden cautela antes de atribuirla: el grupo de referencia es el máximo de seis bandas (sesgo de selección; la banda 25 a 34 también queda 3 puntos abajo), el corte de política (menos de 65 y 65 o más) no muestra diferencia (61,4% frente a 61,8%), y con unas 400 comparaciones se esperan decenas de marcas por azar a ese nivel. La respuesta registrada tampoco es el resultado para el cliente. Decisión: no atribuir; vigilar en producción con la banda fina y reabrir si se repite en dos cortes mensuales.
2. **Plus, SLA y escalamiento.** Student es un segmento pequeño (n=394 en disputas) y su intervalo es amplio (figura 1); la referencia es el mejor de cuatro, otra vez por selección. Plus no se separa de Basic ni de Premium. La razón de 1,28 pasa el tamiz de 1,25 por poco y la brecha es de 4,3 pp, bajo los 5 pp. Persiste tras ajustar, así que no la explica el producto ni el monto, pero no hay una causa que se pueda señalar con estos datos. Se deja en vigilancia.
3. **Escalamiento por edad.** Brechas de 1,3 a 1,6 pp sobre tasas del 4% al 6%: la razón dispara el tamiz, la brecha absoluta es pequeña. Se anota sin acción.
4. **CSAT en sucursal.** Muestra de 95 respuestas; sin un patrón por categoría (cada celda tiene menos de 25 respuestas) ni por tipo de caso. Es plausible que sea ruido o un efecto propio de la atención presencial; no es comparable con un agente digital. Se mide, no se atribuye.

Conclusión: no se encontró un trato desigual atribuible a idioma, país, segmento, acento, edad o género en el histórico. La mayoría de las diferencias están dentro del ruido; la única brecha de 5 pp o más (edad 18 a 24) queda sin causa identificada y en vigilancia.

## 5. Equidad del sistema en la evaluación

**Corte.** Idioma (es, pt), país de la cuenta (MX, CO, AR) y segmento comercial, según el diseño del conjunto representativo (150 casos en español con MX 40, CO 40, AR 40 y neutro 30; 50 en portugués con cuentas de los tres países). Los pares de equidad (12 casos base por cinco variantes) se evalúan aparte por divergencia de ruta, no por tasas.

**Herramienta.** `latam_gobierno.equidad.tabla_disparidad` recibe el JSON por caso con los campos `caso, idioma, pais, segmento, resultado, inseguro, escalo, debia_escalar, latencia` y devuelve, por dimensión y grupo: resolución segura, sensibilidad de escalamiento (escaló entre los que debían), traspaso innecesario (escaló entre los que no debían), inseguros y latencia p95; con *n*, Wilson, brecha de Newcombe, razón y estado (`referencia`, `ok`, `investigar`, `muestra_insuficiente`). Cualquier caso inseguro marca `investigar` en su grupo. Línea de comandos: `uv run python -m latam_gobierno.equidad casos.json`.

**Prueba offline.** `gobierno/tests/test_equidad.py` usa `gobierno/equidad/fixtures/casos_ejemplo.json` (167 casos sintéticos) con tres propiedades sembradas: el portugués peor en resolución y latencia, Argentina con 12 casos y un inseguro en México. La tabla marca las tres como corresponde.

**Gancho.** `ia/evaluacion/reportes` solo tiene informes en Markdown; aún no existe un JSON por caso de una corrida representativa. Cuando IA lo escriba con esos campos, se aplica con el comando anterior y la tabla entra al acta de equidad de F6. No se afirma ningún resultado del sistema hasta entonces.

**Alcance estadístico.** Con 50 casos en portugués y 40 por país, el intervalo de una tasa cerca del 80% mide unos 11 a 12 puntos de ancho: solo se detectan brechas grandes, de unos 20 puntos o más. "Sin disparidad detectada" en esas muestras no demuestra paridad; la tabla lo dice con `muestra_insuficiente` bajo 30 casos y este informe lo repite.

## 6. Limitaciones

- **Datos sintéticos.** Los resultados históricos son casi uniformes por construcción; la paridad observada describe el generador, no un banco real. Las pocas marcas son compatibles con ruido. La metodología sí es la que se aplicaría a datos reales.
- **No hay clientes brasileños.** Los clientes son de México, Colombia y Argentina. No existe línea base histórica en portugués; el acento (mexicano, colombiano, argentino, sin detectar) solo aproxima el idioma, y el servicio en portugués se mide por primera vez con la evaluación del sistema.
- **Muestras pequeñas de la evaluación** (sección 5) y de ciertos grupos históricos (Student, canal regulador, canal sucursal en CSAT).
- **Resultados definidos por proxy.** "Resuelta" es tener fecha de resolución; el 75% de las quejas sigue abierta o en proceso en la ventana, por lo que las tasas de resolución son bajas en todos los grupos. El monto reclamado falta en el 68% de las quejas y su tercil es débil como control. El CSAT cubre pocas respuestas y mezcla escalas distintas (1 a 5 en quejas, 1 a 7 en encuestas).
- **Comparaciones múltiples.** Se hicieron unas 600 comparaciones sin corrección; las marcas se tratan como alertas, no como hallazgos.
- **Ajuste limitado.** Controla la mezcla observada; no controla causas no medidas. Referencia al "mejor grupo" favorece marcar grupos pequeños.
- **Fuera del alcance:** estado civil y educación (no se usan) e inferencia del idioma por el texto del cliente.

## 7. Monitoreo en producción

| Qué | Métrica por grupo | Umbral de alerta | Frecuencia | Dueño |
|---|---|---|---|---|
| Resultados inseguros | conteo | cualquier caso en cualquier grupo: alerta inmediata y veto de la versión (R-GOB-64) | continua | Gobierno |
| Resolución automática segura | tasa con Wilson | brecha de 5 pp o más con Newcombe sin el cero, o razón menor que 0,8, con 30 casos o más por grupo | semanal, acumulada 28 días | Gobierno y Datos |
| Escalamiento | sensibilidad y traspaso innecesario | sensibilidad: igual que lo anterior; traspaso: razón mayor que 1,25 | semanal | Gobierno |
| Latencia | p95 | mayor que 1,25 veces la del mejor grupo | diaria | Tecnología |
| Voz | error de reconocimiento y retención frente a texto por acento | brecha de 5 pp o más; retención menor que 0,85 veces la mejor | semanal | IA |
| Primera respuesta y SLA de disputas | tasa y mediana de horas | misma regla de brecha; mediana mayor que 1,25 veces | mensual | Datos |
| Pares de equidad | divergencia de ruta o estado final | cualquier divergencia | en cada versión | Gobierno |
| CSAT por grupo | media | menos 0,25 puntos con intervalo sin el cero | mensual | Protección al consumidor |

Reglas operativas:

- Cortes: idioma, país, segmento y, solo para auditoría y agregados con al menos 20 casos, acento y franja de edad (menos de 65 y 65 o más). El género se mira únicamente agregado y en el informe mensual, no en tableros operativos.
- Mínimos: con menos de 30 casos en un grupo se acumula otra ventana antes de concluir; se informa como "muestra insuficiente".
- Alerta: una marca a la semana abre un registro; la misma marca en dos ventanas consecutivas obliga a acta de investigación con el ajuste por mezcla de este informe antes de cualquier cambio. Una marca de inseguros o una divergencia en un par de equidad es inmediata.
- Corrección múltiple: con muchos cortes se espera algún falso positivo; una marca aislada y sin mecanismo plausible se anota y se vigila, no se corrige.
- Sin ciclo de realimentación: ningún atributo de auditoría llega al oro operacional, a un prompt ni a la prioridad de cola (I-10, R-GOB-51); el monitoreo lee platino.
- Datos de producción: antes de usar atributos protegidos reales se necesita base legal y aviso al cliente; en este proyecto solo se usa el dataset sintético.
