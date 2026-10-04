# Equidad del sistema (R-GOB-47, R-GOB-48)

Código: `gobierno/src/latam_gobierno/equidad.py`. Prueba: `gobierno/tests/test_equidad.py` con
`fixtures/casos_ejemplo.json` (sintético, con un portugués peor sembrado, un grupo pequeño y un inseguro).

**Cortes de la evaluación:** idioma (es, pt), país de la cuenta (MX, CO, AR) y segmento comercial. Nunca género,
edad, estado civil ni acento como entrada; esos atributos solo desagregan la línea base histórica de Datos.

**Uso:** `uv run python -m latam_gobierno.equidad ruta/casos.json` imprime la tabla y sale con 1 si algún grupo
exige investigación. Desde código: `tabla_disparidad(cargar_casos(ruta))`.

**Entrada:** lista JSON con `caso, idioma, pais, segmento, resultado, inseguro, escalo, debia_escalar, latencia`.
`resultado` es booleano o una de `exito, resuelto, resuelto_seguro, ok`; un caso inseguro nunca cuenta como éxito.

**Salida por dimensión y grupo:** resolución segura, sensibilidad de escalamiento, traspaso innecesario, inseguros
y latencia p95, con *n*, Wilson, brecha de Newcombe y razón frente al mejor grupo. Estados: `referencia`, `ok`,
`investigar` y `muestra_insuficiente` (menos de 30 casos en el denominador).

**Gancho pendiente:** `ia/evaluacion/reportes` no tiene todavía un JSON por caso (solo informes en Markdown).
Cuando la corrida representativa lo escriba, se aplica con el comando de arriba y la tabla se pega en el acta de
equidad de F6. Cada fila `investigar` necesita acta (R-GOB-48).
