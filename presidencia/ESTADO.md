# Estado del proyecto

Traspaso entre sesiones. Se reescribe al cerrar cada jornada; el historial está en [bitacora.md](bitacora.md).

**Actualizado:** 29 de septiembre de 2026.

## Dónde estamos

| Frente | Estado | Dónde |
|---|---|---|
| Plataforma | Todo en Google Cloud (D-30). Proyecto `latam-bank-hackaton-2026` en **sandbox de BigQuery**, sin facturación: la cuenta de facturación está cerrada | [decisiones.md](decisiones.md) |
| Datos | Bronce, plata, oro y platino en BigQuery; manifiesto encadenado; reglas Q-BRZ; dbt con 56 pruebas en verde; siete fichas de oro operacional y 12 dominios canónicos | [datos/README.md](../datos/README.md), [LIMITACIONES](../datos/LIMITACIONES.md) |
| Gobierno | Guardas contra datos y credenciales en pre-commit y CI; gitleaks configurado; `policy/v1` con huella (escalamiento, crédito provisional, riesgo, ACR por acción, traspaso) que el motor lee | `gobierno/src/latam_gobierno/guardas.py` |
| Auditoría | `fuentes.yaml` con 66 fuentes; plantillas del paquete de independencia y del informe sellado | `auditoria/` |
| Tecnología | ADR 0001 a 0010; perfiles de Compose; spike S4 (retoma idempotente de chat a voz) y spike S3 (chat AG-UI) funcionan; motor del caso de disputa y herramientas del agente (lectura de oro por cliente, efectos idempotentes con aprobación); chat web de disputas (`just chat`, http://localhost:8765) con aprobación de un solo uso, aviso de IA y botón de persona; Terraform escrito y **sin validar ni aplicar** | `tecnologia/adr/`, `tecnologia/infra/` |
| IA | Registro de agentes y prompts (IA-7.1, IA-9.1); arnés IA-5.1 con 23 escenarios: offline 23 de 23, 0 inseguros en 69 corridas; léxico prohibido único en `clientes/estilo/estilo.yaml` | [ia/README.md](../ia/README.md) |
| Sitio | Publicado en https://latam-bank-hackaton-2026.web.app (Firebase Hosting, plan gratuito): inicio, reclamos, transparencia, privacidad y chat; el chat en vivo necesita backend y hoy solo corre local | `tecnologia/web/sitio/`, `firebase.json` |
| Clientes | Matriz estado x canal x registro, guía de estilo, 50 plantillas en usted y vos, linter en CI | [clientes/README.md](../clientes/README.md) |

## BigQuery

Dataset `latam_bank`, con la capa como prefijo de tabla (7,2 GB de 10 GB; las tablas vencen el **28 de noviembre de 2026**):

| Capa | Tablas | Contenido |
|---|---|---|
| `bronce_` | 13 | crudo, todo texto; cuadra con los CSV (`platino_manifiesto_tablas`) |
| `plata_` | 14 | tipado, deduplicado, PII seudonimizada; `plata_digital_events` es vista |
| `oro_` | 8 | siete operacionales para el agente, sin PII; línea base de reclamos |
| `platino_` | 8 | manifiesto, calidad, conversiones fallidas, huérfanos, respaldo, inventario |

`latam_seguridad` guarda la llave de seudonimización; `latam_pruebas`, los fallos de las pruebas de dbt (7 días).
`AS_OF` = 2026-06-17. Copia local del bucket (fuera de git) en `C:\Users\LaraJ\Projects\fh-datos\data\`
(`espejo/` 5,0 GB y `respaldo_20260831/` 4,5 GB; el respaldo del organizador está incompleto de origen).

## GEAP (D-32), en producción

- **Chat público → Cloud Run → Agent Runtime.** `latam-chat` (Cloud Run, cuenta `latam-chat@` de mínimo
  privilegio) reenvía cada turno al agente `projects/47808508188/locations/us-central1/reasoningEngines/6796256743388086272`
  (Agent Runtime, escala a cero, Sessions de 24 h, cuenta `latam-chat@`). Modelo: `gemini-2.5-flash-lite` en GEAP
  (región `global`). Trazas en Cloud Trace con `latam.trabajador.id` y versión. Probado de punta a punta: ficha,
  aprobación con datos de la base y caso creado.
- **Redesplegar el agente:** `uv run --with "google-cloud-aiplatform[agent_engines]" --with cloudpickle python
  tecnologia/infra/agent_runtime/desplegar.py --bucket latam-bank-hackaton-2026-staging` (crea un recurso nuevo:
  apuntar Cloud Run con `LATAM_AGENT_RUNTIME_RECURSO` y borrar el anterior). **Chat:** `just desplegar-chat-run`
  con esa variable. Volver al agente en proceso: quitar la variable; al guion: `LATAM_MODELO=guionado`.
- **Pendiente:** Gemini 3 falla con herramientas por el endpoint compatible con OpenAI (pierde la `thought_signature`);
  volver a Gemini 3 exige el proveedor nativo de Google (hoy choca con dbt-bigquery en el lock). Agent Identity exige
  que el proyecto esté en una organización (hoy "sin organización"). En modo runtime el chat no dibuja la ficha visual.
  El despliegue crea un recurso nuevo en vez de actualizar. Fase 3: GenAI Evaluation Service con los 23 escenarios.
  `roles/editor` sigue en la cuenta de Compute (la usa Cloud Build); retirarlo tras mover los builds a su propia cuenta.

## Desplegar el sitio

La CLI de Firebase de esta máquina tiene otra cuenta; se despliega con una configuración aislada y las
credenciales de gcloud (ADC) del dueño del proyecto:

```bash
XDG_CONFIG_HOME=<carpeta temporal> GOOGLE_APPLICATION_CREDENTIALS=%APPDATA%/gcloud/application_default_credentials.json   firebase deploy --only hosting --project latam-bank-hackaton-2026
```

## Pendientes del usuario

1. Decidir si se reabre la facturación (tope real US$20). Sin ella no hay Cloud Run, Vertex AI, Cloud SQL ni
   buckets; los modelos irían por el nivel gratuito de la API de Gemini (llave de AI Studio).
2. Instalar Terraform y correr `terraform fmt -recursive` y `terraform validate` en `tecnologia/infra/terraform/envs/dev`.
3. Instalar `just` (las recetas del `justfile` se usan en la documentación).
4. Las llaves del organizador quedaron en el perfil `default` de AWS; revisar si había credenciales propias ahí.
5. Meta (WhatsApp) y Twilio en modo de prueba; preguntas a los organizadores.
6. Crear una llave de AI Studio (https://aistudio.google.com/apikey) y exportarla como `GEMINI_API_KEY`; sin ella la IA corre con `TestModel`.


## Siguientes historias, en orden

1. **Gobierno:** fijar el umbral de ESC-04 (hoy 1.000 USD provisional por moneda) y revisar la guía de estilo (S-CLI-02).
2. **Clientes:** CLI-2.1 (etiquetas de los componentes en `es.yaml`; hoy en `canales/textos.py`), CLI-1.4 y CLI-1.5 (portugués).
3. **Tecnología:** backend público del chat (Cloud Run si se reabre la facturación, o un Space gratuito de Hugging Face) y apuntar `config.js`; voz (spike S1) y WhatsApp de prueba.
4. **IA:** IA-3.1 (redacción por locale), IA-7.2 (hojas de vida) y correr el arnés con Gemini cuando haya llave.
5. **Presidencia:** reporte final y guion de la demo (CLI-5.4).

## Cómo se trabaja

Ramas `feature/<cara>-<historia>-<tema>` desde `develop`, una por subagente en su propio worktree (`../fh-<tema>`);
se fusionan a `develop` con `just check` en verde. Commits de una línea.
