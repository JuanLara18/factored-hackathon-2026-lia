# Política de actualización de datos

**AS_OF.** Es el mayor `process_date` de las tablas de hechos (`transactions`, `call_center_interactions`,
`digital_events`, `campaign_sends`) en `latam_bank.bronce_*`. Hoy es **2026-06-17**, el final de la ventana del
dataset. Se calcula, no se escribe a mano: `just inventario` lo consulta (solo esa columna) y lo deja en
`platino_inventario_insumos.as_of`. Todo lo que dependa de "hoy" (frescura, ventanas de corrección) usa AS_OF y no el reloj.

**Llegadas tardías.** La fuente entrega un archivo por tabla y día. Un archivo con `process_date` anterior a
AS_OF que llega o cambia después es tardío. Dentro de la ventana de corrección (`process_date` >= AS_OF menos 3 días)
se aplica en la siguiente corrida; fuera de ella se retiene y se revisa a mano. Ningún dato entra sin quedar en el
manifiesto con su sha256.

**Regeneración.** Si el organizador regenera el dataset (como el respaldo de 2026-08-31), se baja al espejo local
y se corre `just comparar-respaldo`: rutas y sha256 distintos indican regeneración, no corrección. Una regeneración no se
mezcla con la generación vigente; se decide con Presidencia y, si se adopta, se recarga con el cargador
(`bronce_<t>_nuevo`, conteo contra los CSV, reemplazo) y se corre `just manifiesto`, que encadena el manifiesto nuevo al anterior.

**Verificación.** `just verificar-cadena` en cada corrida; una cadena rota bloquea cifras oficiales (PD6). Las tablas
vencen el 2026-11-28 (vencimiento heredado del sandbox): antes de esa fecha se recargan desde el espejo local, y el manifiesto es la prueba de que
la recarga es igual.
