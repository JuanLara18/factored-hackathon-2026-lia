# Revisión de backend, 30 de septiembre de 2026

Alcance: `banca`, `canales` (sin `geap.py`), `herramientas`, `motor`, `runtime`, `servicios`, `comun` y `gobierno/src`.
Pruebas de regresión en `tecnologia/tests/test_revision_backend.py` (21).

## Errores de producción (48 h)

| Fuente | Hallazgo | Causa y arreglo |
|---|---|---|
| `latam-chat` (Cloud Run), severidad WARNING o más | Sin entradas | Nada que corregir |
| Agent Runtime `6796256743388086272` | 1 ERROR: `ContentFilterError` "undeclared function default_api.listar_transacciones" | Gemini llamó una herramienta con un nombre mal formado y el turno moría con traza. `runtime/agente.py` reintenta una vez (nada quedó guardado) y, si persiste, emite `error` con código `modelo`. Pruebas: `test_error_del_modelo_*` |

## Hallazgos

| # | Severidad | Hallazgo | Arreglo | Prueba |
|---|---|---|---|---|
| 1 | Alta | Montos de México con formato de Colombia (`1.250,00`); había cinco formateadores duplicados | `vista.monto(valor, moneda)` único; MXN usa `1,250.00` | `test_monto_por_pais`, `test_movimiento_mexicano_*` |
| 2 | Alta | Turno sin tope hacia Agent Runtime: el cliente podía quedar colgado | `asyncio.timeout` de 90 s, mensaje claro y mensaje de texto cerrado | `test_runtime_que_no_responde_*` |
| 3 | Alta | Turno de aprobación fallido dejaba la confirmación gastada y la sesión atascada en `aprobacion_pendiente` | La confirmación se vuelve a emitir si el turno falla | `test_aprobacion_se_puede_reintentar_*` |
| 4 | Alta | Efecto que fallaba (Firestore caído) dejaba la llave "en curso" y todo reintento daba `EfectoIncierto` | `ejecutar_una_vez` libera la reserva si el ejecutor lanza (los efectos del banco son idempotentes) | `test_efecto_que_falla_*` |
| 5 | Media | Sesiones de la consola sin vencimiento, sin tope y con alias reutilizables (`Experto N` por tamaño del dict) | Vencen a 8 h, tope de 50, contador monótono | `test_sesion_de_operador_vence_*` |
| 6 | Media | Código de la consola sin límite de intentos | 429 tras 5 fallos por minuto (la comparación ya era en tiempo constante) | `test_codigo_de_operador_se_limita_*` |
| 7 | Media | Transcripción del experto duplicaba turnos tras 60 (el índice usaba el largo topado) | Contador `turnos_guardados`; con Agent Runtime el chat ya no registra (lo hace el agente) | `test_transcripcion_del_chat_*`, `test_contador_de_turnos_*` |
| 8 | Media | `antes_de` con zona contra fechas sin zona daba 500; los empates en el borde se perdían; el historial se topaba en 50 | Se normaliza a UTC, el empate viaja junto, se leen hasta 200 | `test_antes_de_*`, `test_historial_mas_alla_*` |
| 9 | Media | Fecha y hora de los movimientos en UTC; fichas del chat con fecha UTC | Bogotá en la API y en las fichas (`vista.fecha`, `fecha_texto`) | `test_movimiento_mexicano_*` |
| 10 | Media | Cuerpos malformados o de tipo inesperado daban 500; sin límite de tamaño ni de mensaje | 400 o 413 (64 KB de cuerpo, 4.000 caracteres de mensaje) | `test_cuerpos_malos_*`, `test_mensaje_demasiado_largo_*` |
| 11 | Media | Errores no controlados sin JSON ni cabeceras; Firestore caído sin mensaje | Middleware: `{error: interno}` 500 o `servicio_no_disponible` 503, registra solo la clase | `test_error_no_controlado_*`, `test_firestore_caido_*` |
| 12 | Media | Falla al crear la sesión del agente dejaba sesiones a medias | 503 `agente_no_disponible` y sin sesión huérfana | `test_sin_agente_no_se_abre_la_sesion` |
| 13 | Media | El agente podía abrir disputa de un movimiento rechazado, fallido o revertido (la API ya lo negaba) | `NoDisputable` en `Herramientas`; la herramienta responde con texto | `test_no_se_abre_disputa_de_un_movimiento_rechazado` |
| 14 | Media | `resolver` y `abrir_caso` (reapertura) y `agregar_transcripcion` sin transacción en Firestore | Transacciones; resolver dos veces conserva la primera | `test_resolver_dos_veces_*` (memoria; Firestore cubierto por inspección) |
| 15 | Baja | Memoria sin tope: sesiones vencidas, confirmaciones sin gastar y traza | Purga al abrir sesión, tope de 2.000 confirmaciones, traza recortada | `test_vencimientos_no_crecen_sin_limite` |

## Revisado sin hallazgo

- Alcance por cliente: toda ruta y herramienta toma el cliente de la sesión; las referencias se resuelven solo entre lo del cliente; lo ajeno responde 404. El agente lee la sesión de Sessions y rechaza sesiones de otro usuario.
- Confirmación: un solo uso, vence a 5 minutos y es de la sesión (solo en memoria por proceso; con más de una instancia de Cloud Run la sesión ya es por instancia).
- CORS: lista cerrada de orígenes, solo GET y POST.

## Riesgos aceptados o pendientes

- Referencias opacas: la clave sale de `LATAM_REF_SECRETO`; si falta, se usa una de demostración del repositorio. Las referencias incluyen al cliente, así que falsificarlas no cruza clientes; rotar la clave invalida las referencias abiertas en los navegadores (se recargan). Fijar la variable en Cloud Run.
- Sesiones, confirmaciones y operadores viven en memoria de la instancia: escalar a más de una instancia exige moverlos a Firestore.
- Las pruebas de Firestore usan un doble; las transacciones nuevas no corrieron contra el emulador.
