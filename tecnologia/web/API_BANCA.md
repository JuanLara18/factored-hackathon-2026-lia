# Contrato de la API de la banca en línea y la consola del experto (D-33)

Lo implementa `latam_tecnologia.banca` en el mismo servicio de Cloud Run que el chat (`chat_web`). Todo es JSON.
La sesión viaja en la cabecera `X-Sesion` (la misma que usa el chat). Ningún campo lleva nombre, documento,
correo, teléfono, número completo de tarjeta ni identificadores internos a la vista: las referencias (`*_ref`) son
opacas y la interfaz nunca las muestra. Montos como texto con formato del país (`"128.482,28"`) más `moneda` ISO.

## Cliente (banca en línea)

| Método y ruta | Entrada | Salida |
|---|---|---|
| `GET /api/banca/clientes-demo` | | `[{indice, nombre, alias, pais}]` (`nombre` ficticio fijo por índice, p. ej. "Valentina Ríos"; `alias` ("Cliente 1 · Argentina") queda de respaldo) |
| `POST /api/banca/ingresar` | `{indice, registro?}` (`registro`: `usted`, `vos` o `voce`; `voce` es portugués y fija el idioma del agente, las plantillas y `idioma = pt` en el traspaso) | `{sesion, cliente: {nombre, alias, pais, moneda, registro}}` La respuesta trae además `conversacion`, la conversación general de la sesión: el asistente atiende en ella sin que el cliente abra un movimiento. |
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
| `GET /api/operador/cola` | | `[{id_traspaso, prioridad, motivo, motivo_texto, pais, idioma, registro, canal, creado_hace_s, estado, tomado_por}]`, ordenada por prioridad y antigüedad; solo `en_cola` y `tomado` |
| `GET /api/operador/traspasos/{id}` | | la vista del `PaqueteTraspaso` (forma final abajo) |
| `POST /api/operador/traspasos/{id}/tomar` | | `{estado: "tomado"}` |
| `POST /api/operador/traspasos/{id}/mensaje` | `{texto}` | `{id}` (entra al mismo hilo del cliente) |
| `POST /api/operador/traspasos/{id}/resolver` | `{resultado, etiqueta_correccion?, nota}` (`resultado`: `resuelto`, `radicado`, `escalado` o `sin_accion`; `etiqueta_correccion` es un objeto de etiquetas del equipo) | `{estado: "resuelto"}` |

### Forma de `GET /api/operador/traspasos/{id}`

Es la de `tecnologia/web/sitio/operador/fixtures/traspaso_*.json` (una prueba compara las claves). `estado` es
`en_cola`, `tomado` o `resuelto`; las horas son `HH:MM` de Bogotá y los plazos vienen como `vence_en_s`.
Claves: `id_traspaso, hilo_id, caso_id, prioridad (P1 a P4), motivo {codigo, texto, regla {id, version}},
cola_destino, idioma, registro, pais_cuenta, canal_actual, canales_usados, creado_hace_s, estado, tomado_por,
identidad {nivel, metodo, hora} o null, que_hacer_primero [{paso, regla}], compromisos_comunicados [{texto, hora}],
solicitud {cita, idioma}, interpretacion {motivo, urgencia, entidades, confianza}, hechos_verificados
[{texto, fuente, hora}], acciones_realizadas [{accion, resultado, hora}], acciones_no_realizadas [{accion, motivo}],
conflictos [{tipo, declarado, registro}], preguntas_abiertas [{pregunta, a_quien, bloquea}], plazos_en_curso
[{regla, inicio, vence_en_s}], evidencia {traza_url, reglas, plantillas}, transcripcion [{autor, texto, en}],
mensajes [{id, autor, texto, en}]`.

- `fuente` de un hecho: `transacciones`, `productos`, `casos` o `conversacion` (cuando no hay movimiento); nunca
  texto del modelo. `interpretacion` es la de la IA: `confianza` es `null` mientras el modelo no la reporte.
- `prioridad` es la mayor entre la del motivo (lista cerrada de 2.5.1) y la del caso (monto sobre el umbral: P2;
  urgente: P1). `motivo.regla` sale de `policy/v1` (`TRA-nn` o `ESC-nn`) o es `null` si el motivo no la tiene.
- `traza_url` es `null` si no hay traza real. Sin nombre, documento, número de tarjeta, segmento ni `fraud_score`.
- `mensajes` trae el hilo compartido (cliente y persona); la consola lo sondea con este mismo GET.
- Tomar, escribir y resolver exigen que el traspaso lo haya tomado quien llama (409 si no); `tomado_por` es un alias
  ("Experto 1"). Errores: `{error}` con 401 (sesión), 404 (no existe o no es suyo), 409 (estado) y 400 (entrada).

### Notas del lado del cliente

- `hora` y `en` de los mensajes van como `HH:MM` de Bogotá; `id` de mensaje es ordenable (sirve de `desde`).
- `POST /api/traspaso` (botón de persona del chat) acepta `{conversacion}` para la conversación abierta con
  `reclamar`; sin él usa la de la sesión. `POST /api/agui` acepta ese `threadId`. Otra conversación responde 403.
- `reclamar` responde 409 `{error: "ya_reclamado", caso_ref}` si el movimiento ya tiene caso y 409
  `no_reclamable` si su estado no permite disputa; pedirlo dos veces devuelve la misma conversación.
- Textos de pantalla: cada movimiento trae, además de los códigos crudos (`estado`, `categoria`, `tipo`, `canal`, que
  siguen igual), `estado_texto`, `categoria_texto`, `tipo_texto` y `canal_texto` en español (portugués si el
  registro es `voce`), `sentido` (`cargo` o `abono`: depósito y reverso son abono), `monto_con_signo` (`-1.234,56` o
  `+1.234,56`, con el formato del país) e `icono`, un slug estable para el SVG: `compras`, `comida`, `transporte`,
  `entretenimiento`, `servicios`, `salud`, `efectivo`, `transferencia`, `pago`, `deposito`, `otro`. Si el movimiento no
  es compra, el icono sale del tipo; si es compra, de la categoría (`compras` si no la tiene). Las etiquetas son las
  de `datos/dominios/dominios_canonicos.csv`, copiadas al código (la imagen no trae `datos/`) y verificadas por prueba.
- `resumen` trae el bloque `resumen {saldo_disponible: [{moneda, monto}], gasto_mes_tarjetas: [{moneda, monto}],
  reclamos_abiertos}`: el saldo suma cuentas (no tarjetas, préstamos ni seguros); el gasto es de compras aprobadas o
  pendientes en tarjetas durante el mes de Bogotá en curso.
- `resumen` incluye también `cliente {nombre, alias, pais, moneda, registro}`; `producto.tipo` es el código
  (`credit_card`) y `etiqueta` el texto en español.

## Restablecer la demostración

`POST /api/demo/restablecer` borra casos, bloqueos, traspasos y conversaciones con sus mensajes de los clientes demo
(solo de ellos) y los reclamos en memoria de sus sesiones. Exige `X-Operador` válido o `{codigo}` en el cuerpo (el
código del experto; 401 si falla, con el mismo límite de intentos que el ingreso). Idempotente: responde
`{restablecido: true, casos, bloqueos, traspasos, conversaciones}` con los conteos borrados. El registro solo
guarda conteos.

## Almacén

Firestore nativo (`nam5`) en `latam-bank-hackaton-2026`, colecciones `casos`, `bloqueos`, `traspasos`,
`conversaciones/{id}/mensajes`. En pruebas, el mismo puerto con un doble en memoria. Lo usan el chat en proceso,
el agente en Agent Runtime (banco y almacén dejan de ser simulados en memoria) y la consola.
