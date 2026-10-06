# Retenido v3

Conjunto de evaluación congelado el **5 de octubre de 2026**, con el prompt `disputas/agente@1.6.0` y el trabajador 0.7.0 en producción y **antes** de construir las capacidades de política con cita, seguimiento del caso y varios pedidos. Se corre una sola vez, sobre el sistema final y sobre la línea base de reglas.

**Huella SHA-256:** `2e2318519474950d8f52a8601eb86c7ae3721a1b3f32973f3a539a0aeacae9f4` (`huella_retenido(DIR_RETENIDO_V3)`; la prueba `ia/tests/test_retenido_v3.py` falla si cambia).

## Por qué existe

El retenido anterior (`../retenido/`, versiones 1 y 2) está gastado: sus casos se conocen, dos se reetiquetaron después de ver resultados (D-34) y las correcciones del sistema se comprobaron sobre ellos. Además tenía 31 casos de Colombia, 1 de Argentina y ninguno de México.

## Mezcla

43 casos. Por idioma: 28 en español (19 de usted, 9 de vos) y 15 en portugués. Por país de la cuenta: 18 de Colombia, 16 de México y 9 de Argentina. Por etiqueta: 24 resolver, 8 abstenerse, 6 escalar y 5 fallo seguro; 37 en alcance y 6 fuera.

| Categoría | Casos | Qué cubre |
|---|---|---|
| N | 6 | cobro propio en MXN, COP y ARS; tarjeta robada; duplicado; caso ya abierto; movimiento fijado por la banca |
| A | 5 | dos y tres candidatas; monto que no existe; relato sin datos; mezcla de español y portugués |
| E | 6 | pide persona; monto sobre umbral; revertido con insistencia; suplantación con transferencia; producto inexistente; exige supervisor |
| F | 3 | préstamo y elegibilidad; pedido no bancario; cambio de datos personales |
| X | 10 | sesión vencida al inicio y a mitad; BigQuery, Firestore y Agent Runtime caídos; movimientos ajenos; inyección directa; dos inyecciones en texto de herramienta; datos personales en el mensaje |
| P | 5 | preguntas de política que deben responderse citando la regla (`debe_citar`), y una que la política no cubre (`sin_citas`) |
| S | 4 | seguimiento de un caso abierto, de uno que no existe, y seguimiento con pregunta de política |
| M | 4 | varios pedidos en una conversación |

## Reglas del congelamiento

1. Ningún caso se edita después de ver resultados del sistema. Un defecto de etiqueta se informa tal como corrió y se corrige en una versión nueva.
2. Las etiquetas salen de `policy/v1`, de las reglas del producto y del enunciado, no del comportamiento observado. `validar_etiquetas` comprueba la coherencia con `decidir` del motor.
3. Las capacidades nuevas se iteran solo con el conjunto de desarrollo (`../*.yaml`).
4. Lección de la versión 1: un caso fuera de alcance no exige cero traspasos, porque pasar a una persona a quien la pide es la regla del producto; exige que el traspaso no sea urgente.

## Lo que se sabe y no se sabe al congelar

- **Autor único.** Los casos y las etiquetas los escribió una sola parte (el asistente de desarrollo, con la Presidencia); no hay segundo etiquetador todavía.
- **Verificadores pendientes.** `debe_citar` y `sin_citas` quedan fijados aquí, pero su verificador se escribe con la capacidad de política con cita. Lo mismo pasa con la exactitud del estado informado en los casos S: hoy solo se verifican herramientas y efectos.
- **Mezcla elegida, no muestreada.** Las categorías P, S y M miden capacidades que la línea base de reglas no tiene; los resultados se informan por categoría para que esa ventaja no se confunda con una mejora en el flujo de disputa.
- **Prueba de humo.** Antes de congelar se comprobó que los 43 casos corren en el arnés sin excepción, con la línea base de reglas y cliente guionado, sin mirar cuáles pasan.
- **Países.** El país sale de la moneda de la cuenta; siguen sin existir cuentas de Brasil.
