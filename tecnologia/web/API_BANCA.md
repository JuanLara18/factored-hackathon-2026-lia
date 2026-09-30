# Contrato de la API de la banca en línea y la consola del experto (D-33)

Lo implementa `latam_tecnologia.banca` en el mismo servicio de Cloud Run que el chat (`chat_web`). Todo es JSON.
La sesión viaja en la cabecera `X-Sesion` (la misma que usa el chat). Ningún campo lleva nombre, documento,
correo, teléfono, número completo de tarjeta ni identificadores internos a la vista: las referencias (`*_ref`) son
opacas y la interfaz nunca las muestra. Montos como texto con formato del país (`"128.482,28"`) más `moneda` ISO.

## Cliente (banca en línea)

| Método y ruta | Entrada | Salida |
|---|---|---|
| `GET /api/banca/clientes-demo` | | `[{indice, alias, pais}]` (alias ficticio, p. ej. "Cliente 1 · Argentina") |
| `POST /api/banca/ingresar` | `{indice, registro?}` | `{sesion, cliente: {alias, pais, moneda, registro}}` |
| `GET /api/banca/resumen` | | `{cliente, productos: [{producto_ref, tipo, etiqueta, final, estado, moneda, saldo, limite}]}` (`saldo` y `limite` pueden ser `null`) |
| `GET /api/banca/movimientos?producto_ref=&limite=50&antes_de=` | | `{movimientos: [Movimiento], siguiente}` |
| `GET /api/banca/movimientos/{tx_ref}` | | `Movimiento` |
| `POST /api/banca/movimientos/{tx_ref}/reclamar` | `{registro?}` | `{conversacion}`: abre una conversación del chat con esa transacción fijada en el servidor; el widget arranca con ella |
| `GET /api/banca/reclamos` | | `[{caso_ref, tx_ref, descripcion, monto, moneda, estado, abierto_en, credito_provisional, plazo, historial: [{fecha, evento}]}]` |
| `POST /api/banca/tarjetas/{producto_ref}/bloqueo` | `{confirmo: true}` | `{estado: "bloqueada", ya_estaba: bool}` (idempotente) |
| `GET /api/banca/conversaciones/{conversacion}/mensajes?desde=` | | `[{id, autor: "cliente"\|"asistente"\|"persona", texto, en}]` (mensajes de la persona tras un traspaso) |
| `POST /api/banca/conversaciones/{conversacion}/mensajes` | `{texto}` | `{id}` (cuando el caso ya está con una persona) |

`Movimiento`: `{tx_ref, fecha, hora, descripcion, categoria, tipo, canal, monto, moneda, estado, pais,
es_extranjera, tarjeta_final, reclamable, caso_ref}`. `descripcion` es el comercio o, si no hay, el tipo en español.

## Experto (consola)

| Método y ruta | Entrada | Salida |
|---|---|---|
| `POST /api/operador/ingresar` | `{codigo}` (código de demostración de `LATAM_OPERADOR_CODIGO`) | `{sesion_operador}` en `X-Operador` |
| `GET /api/operador/cola` | | `[{id_traspaso, prioridad, motivo, motivo_texto, pais, idioma, registro, canal, creado_en, estado, tomado_por}]`, ordenada por prioridad y antigüedad |
| `GET /api/operador/traspasos/{id}` | | `PaqueteTraspaso` con los 19 campos de la sección 2.5.2 de `clientes/definicion.md`, cada hecho con fuente y hora, y la `interpretacion` marcada como de la IA |
| `POST /api/operador/traspasos/{id}/tomar` | | `{estado: "tomado"}` |
| `POST /api/operador/traspasos/{id}/mensaje` | `{texto}` | `{id}` (entra al mismo hilo del cliente) |
| `POST /api/operador/traspasos/{id}/resolver` | `{resultado, etiqueta_correccion?, nota}` | `{estado: "resuelto"}` |

## Almacén

Firestore nativo (`nam5`) en `latam-bank-hackaton-2026`, colecciones `casos`, `bloqueos`, `traspasos`,
`conversaciones/{id}/mensajes`. En pruebas, el mismo puerto con un doble en memoria. Lo usan el chat en proceso,
el agente en Agent Runtime (banco y almacén dejan de ser simulados en memoria) y la consola.
