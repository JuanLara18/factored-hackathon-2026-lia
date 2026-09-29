# ADR 0010: spike S3, chat con PydanticAI y AG-UI

- Estado: nota de *spike* (TEC-0.3), no es una decisión nueva; confirma D-19.
- Fecha: 28 sep 2026
- Pregunta: ¿PydanticAI y AG-UI llevan componentes, aprobaciones y texto filtrado por frases a una web mínima?

## Veredicto

**Funciona**, con las brechas de la última sección. Todo se probó con `FunctionModel` (sin llaves ni llamadas de pago).

## Qué se construyó

- `canales/chat_agui.py`: agente PydanticAI expuesto con `AGUIAdapter.dispatch_request` en `POST /agui` (SSE).
- `canales/frases.py`: segmentador por frases y filtro de salida (enmascara tarjetas, bloquea "radicado", "bloqueada", etc.).
- `web/spike_s3/`: página estática (`index.html` y `app.js`, sin scripts en línea) que dibuja texto, ficha y aprobación.
- `tests/test_chat_agui.py`: 10 pruebas (12 casos) sobre el flujo de eventos.

## Cómo llegó cada pieza

| Necesidad | Mecanismo | Resultado |
|---|---|---|
| Texto por frases | subclase de `AGUIEventStream` que sobrescribe `handle_text_start`, `handle_text_delta` y `handle_text_end` | un `TEXT_MESSAGE_CONTENT` por frase ya filtrada, aunque el modelo emita trozos de 6 caracteres |
| Filtro antes de enviar | el mismo gancho: cada frase pasa por `FiltroFrase` | una tarjeta partida en varios trozos sale como `**** 1111`; nunca aparece cruda |
| Bloqueo de frase | el filtro devuelve `bloqueada`; se emite la plantilla de respaldo, se descarta el resto del mensaje y se anota `filtro_salida.bloqueo` en la traza | funciona |
| Componente | herramienta **de interfaz**: la web envía `tools` en `RunAgentInput` y PydanticAI la trata como herramienta externa diferida | salen `TOOL_CALL_START`, `TOOL_CALL_ARGS` (por trozos) y `TOOL_CALL_END`; el servidor no ejecuta nada |
| Aprobación | herramienta con `requires_approval=True` | `RUN_FINISHED` trae `outcome.type = "interrupt"` con `interrupts[].responseSchema`; la web responde en `RunAgentInput.resume` con `{approved: true/false}` |
| `nonce` de ida y vuelta | `preparar_confirmacion` (herramienta del servidor) emite el `nonce` ligado al `threadId`; la herramienta aprobada lo consume | vigencia de 5 minutos, misma sesión y un solo uso, probados; un rechazo no ejecuta la acción |

Un turno con componente y aprobación es **una** corrida que termina en interrupción; la siguiente corrida
lleva el historial (que la web reconstruye desde los eventos) y `resume`.

## Latencia observada

Con `TestClient` en proceso y modelo simulado: primer texto p50 12 ms y p95 14 ms (20 turnos). Es el costo
del adaptador y del segmentador, no del modelo real: **no** valida R-TEC-79 de punta a punta, solo
muestra que el filtro por frases no añade una espera relevante. La página muestra el primer texto y el turno completo en pantalla; no se midió en
un navegador real.

## Brechas y decisiones para TEC-5

1. **Versión del SDK.** `pydantic-ai-slim[ag-ui]` 2.51 exige `ag-ui-protocol<1`; el 1.0.0 es incompatible. Se resolvió con 0.1.22. La definición 2.9 debe fijar ese rango.
2. **Identificador de interrupción.** PydanticAI lo forma como `int-<toolCallId>`; un valor con otro prefijo lanza `UserError` y responde 500 en vez de 4xx. Hay que validar en la superficie antes de despachar.
3. **Filtro incompleto.** Solo hay enmascaramiento y afirmaciones prohibidas. Falta el **anclaje de cifras** contra `HechoVerificado` y `ReglaDePolitica` (R-TEC-75) y Model Armor. El gancho lo permite: recibe la frase y puede recibir el contexto.
4. **Mensajes de texto vacíos.** Una respuesta solo con herramientas emite `TEXT_MESSAGE_START` y `TEXT_MESSAGE_END` vacíos (lo hace el adaptador para validar el padre de la llamada). La web debe ignorarlos.
5. **Historial en el cliente.** El navegador debe devolver mensajes de asistente, llamadas y resultados en orden; un error de reconstrucción rompe la reanudación. Hace falta un módulo probado en TypeScript (R-TEC-43) o guardar el historial en el servidor por `threadId`.
6. **Sin `@ag-ui/client`.** La web del spike lee el SSE a mano; queda por probar el cliente oficial y su verificador de eventos, y el JavaScript solo tiene revisión de sintaxis, no prueba en navegador.
7. **`STATE_SNAPSHOT` y `STATE_DELTA`** (estado visible del caso) no se probaron.
8. **El texto emitido tras el filtro se reescribe**: al añadir un espacio al final de cada frase, el texto acumulado no es idéntico al del modelo. Es lo esperado, pero la traza debe guardar ambos.
9. **Alcance.** El monto de la confirmación viaja como argumento del modelo; en TEC-5 debe salir de la base (R-TEC-77) y la plantilla, del catálogo (R-TEC-76).

## Cómo correrlo

```
uv run uvicorn latam_tecnologia.canales.chat_agui:crear_app --factory --port 8765
```

y abrir `http://localhost:8765/`.
