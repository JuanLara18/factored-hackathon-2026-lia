# VP Tecnología: núcleo, canales, plataforma

| Ruta | Qué es |
|---|---|
| `definicion.md` | definición de la cara (reglas R-TEC) |
| `adr/` | decisiones de arquitectura |
| `src/latam_tecnologia/motor/` | máquina de estados y punto de decisión |
| `src/latam_tecnologia/herramientas/` | capa de herramientas tipada |
| `src/latam_tecnologia/servicios/` | servicios simulados BIAN e identidad |
| `src/latam_tecnologia/canales/` | chat (AG-UI), WhatsApp, voz en navegador y teléfono |
| `src/latam_tecnologia/gateway/` | LiteLLM, Presidio, Model Armor |
| `web/` | sitio de LATAM Bank, vista del experto, panel de trazas |
| `infra/terraform/` | Google Cloud como código: declara lo desplegado (presupuesto, Firestore, `latam-chat`, BigQuery), valida y no se ha aplicado; ver `infra/ARRANQUE.md` |
| `src/latam_tecnologia/runtime/` | agente de disputas como agente propio de Agent Runtime (`query`, `stream_query`, Sessions) |
| `infra/agent_runtime/` | `desplegar.py` (paquete, `--dry-run`, despliegue), `iam.sh` (mínimo privilegio) |

## Agente en Agent Runtime (D-32, fase 2)

`AgenteDisputasRuntime` envuelve `crear_agente_disputas` y expone `query`, `stream_query`, `async_query` y
`async_stream_query`. Reglas:

- El cliente, el nivel y el vencimiento salen del **estado de la sesión** de Agent Runtime Sessions, que el canal
  fija al abrirla (`crear_sesion`). Los argumentos de `query` no los aceptan y el modelo no los nombra.
- El historial de mensajes se guarda como eventos de la sesión.
- Las herramientas con efecto devuelven `{"tipo": "aprobacion", "aprobaciones": [...]}`; el canal la resuelve con
  `aprobaciones={id: true|false}` y solo entonces se ejecutan. Un texto escrito no resuelve una pendiente.
- Lectura de BigQuery con `LecturaBigQuery` (solo lectura); banco y almacén siguen simulados, en memoria de la
  instancia (la idempotencia vale por instancia; con `max_instances=1` basta para la demo).

El chat web reenvía los turnos al agente si existe `LATAM_AGENT_RUNTIME_RECURSO`
(`projects/<p>/locations/<l>/reasoningEngines/<id>`); sin ella corre el agente en proceso, sin cambios. En ese
modo la ficha visual (`FichaTransaccion`) no se dibuja, porque es una herramienta del navegador que el agente
remoto no conoce.

Despliegue: `just probar-agente-runtime` (arma y valida, sin API), `just desplegar-agente`, `iam.sh` para los
permisos. El registro en Agent Registry es automático al desplegar con el SDK.

Cuentas: el chat en Cloud Run usa `latam-chat@` con solo `bigquery.dataViewer` sobre `latam_bank` (a nivel de
dataset), `bigquery.jobUser`, `aiplatform.user` (invocar el agente, Sessions y modelos), `cloudtrace.agent` y
`datastore.user` (Firestore). El
agente en Agent Runtime corre con esa misma cuenta (`identity_type: SERVICE_ACCOUNT`): Agent Identity exige que el
proyecto esté en una organización y no lo está (`iam.sh agente` queda para ese día). Así se deja de depender de la
cuenta de Compute por defecto con `roles/editor`, que sigue asignada porque Cloud Build la usa.

