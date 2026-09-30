# Estado del proyecto

Traspaso entre sesiones. Se reescribe al cerrar cada jornada; el historial está en [bitacora.md](bitacora.md).

**Actualizado:** 30 de septiembre de 2026.

## Dónde estamos

| Frente | Estado | Dónde |
|---|---|---|
| Plataforma | Todo en Google Cloud (D-30). Proyecto `latam-bank-hackaton-2026` con **facturación abierta** y presupuesto mensual de COP 20.000 (alertas al 25, 50 y 100%); ya no es el sandbox de BigQuery, pero las tablas conservan el vencimiento del 28 de noviembre de 2026 | [decisiones.md](decisiones.md) |
| Datos | Bronce, plata, oro y platino en BigQuery; manifiesto encadenado; reglas Q-BRZ; dbt con 56 pruebas en verde; siete fichas de oro operacional y 12 dominios canónicos; control del 30 sep: `validar` con 5 avisos y 0 bloqueantes, cadena del manifiesto íntegra (13 registros), contratos sin deriva contra las columnas vivas | [datos/README.md](../datos/README.md), [LIMITACIONES](../datos/LIMITACIONES.md) |
| Gobierno | Guardas contra datos y credenciales en pre-commit y CI; gitleaks configurado; `policy/v1` con huella (escalamiento, crédito provisional, riesgo, ACR por acción, traspaso) que el motor lee | `gobierno/src/latam_gobierno/guardas.py` |
| Auditoría | `fuentes.yaml` con 66 fuentes; plantillas del paquete de independencia y del informe sellado | `auditoria/` |
| Tecnología | ADR 0001 a 0010; perfiles de Compose; spike S4 (retoma idempotente de chat a voz) y spike S3 (chat AG-UI) funcionan; motor del caso de disputa y herramientas del agente (lectura de oro por cliente, efectos idempotentes con aprobación); chat web de disputas (`just chat`, http://localhost:8765) con aprobación de un solo uso, aviso de IA y botón de persona; Terraform refleja lo desplegado y **valida** (1.16), pero **nunca se ha aplicado ni planeado** contra el proyecto | `tecnologia/adr/`, `tecnologia/infra/` |
| IA | Registro de agentes y prompts (IA-7.1, IA-9.1); arnés IA-5.1 con 23 escenarios: offline 23 de 23, 0 inseguros en 69 corridas; léxico prohibido único en `clientes/estilo/estilo.yaml` | [ia/README.md](../ia/README.md) |
| Sitio | Publicado en https://latam-bank-hackaton-2026.web.app (Firebase Hosting, plan gratuito): inicio, reclamos, transparencia, privacidad y chat; el chat en vivo lo atiende `latam-chat` en Cloud Run (https://latam-chat-ccmytkamga-uc.a.run.app); `just chat` lo corre local | `tecnologia/web/sitio/`, `firebase.json` |
| Clientes | Matriz estado x canal x registro, guía de estilo, 50 plantillas en usted y vos, linter en CI | [clientes/README.md](../clientes/README.md) |

## BigQuery

Dataset `latam_bank`, con la capa como prefijo de tabla (7,2 GB lógicos en 45 objetos; ya no rige el tope de 10 GB del sandbox porque hay facturación, y el almacenamiento activo de este volumen cuesta centavos al mes. Las tablas vencen el **28 de noviembre de 2026**: para quitar el vencimiento hay que actualizar cada tabla con `bq update --expiration 0`, y los datasets traen 60 días por defecto para tablas nuevas):

| Capa | Tablas | Contenido |
|---|---|---|
| `bronce_` | 13 | crudo, todo texto; cuadra con los CSV (`platino_manifiesto_tablas`) |
| `plata_` | 14 | tipado, deduplicado, PII seudonimizada; `plata_digital_events` es vista (se dejó vista por decisión de diseño, no por el tope) |
| `oro_` | 8 | siete operacionales para el agente, sin PII; línea base de reclamos |
| `platino_` | 8 | manifiesto, calidad, conversiones fallidas, huérfanos, respaldo, inventario |
| sin prefijo | 2 | semillas de dbt: `dominios_canonicos` y `directorio_comercios_equipo` |

`latam_seguridad` guarda la llave de seudonimización; `latam_pruebas`, los fallos de las pruebas de dbt (7 días).
`AS_OF` = 2026-06-17. Copia local del bucket (fuera de git) en `C:\Users\LaraJ\Projects\fh-datos\data\`
(`espejo/` 5,0 GB y `respaldo_20260831/` 4,5 GB; el respaldo del organizador está incompleto de origen).

## GEAP (D-32), en producción

- **Chat público → Cloud Run → Agent Runtime.** `latam-chat` (Cloud Run, cuenta `latam-chat@` de mínimo
  privilegio) reenvía cada turno al agente `projects/47808508188/locations/us-central1/reasoningEngines/6796256743388086272`
  (Agent Runtime, escala a cero, Sessions de 24 h; se invoca con la cuenta `latam-chat@`). Modelo: `gemini-2.5-flash-lite` en GEAP
  (región `global`). Trazas en Cloud Trace con `latam.trabajador.id` y versión. Probado de punta a punta: ficha,
  aprobación con datos de la base y caso creado.
- **Redesplegar el agente:** `uv run --with "google-cloud-aiplatform[agent_engines]" --with cloudpickle python
  tecnologia/infra/agent_runtime/desplegar.py --bucket latam-bank-hackaton-2026-staging` (crea un recurso nuevo:
  apuntar Cloud Run con `LATAM_AGENT_RUNTIME_RECURSO` y borrar el anterior). **Chat:** `just desplegar-chat-run-agente <recurso>`. Volver al agente en proceso: quitar la variable; al guion: `LATAM_MODELO=guionado`.
- **Pendiente:** Gemini 3 falla con herramientas por el endpoint compatible con OpenAI (pierde la `thought_signature`);
  volver a Gemini 3 exige el proveedor nativo de Google (hoy choca con dbt-bigquery en el lock). Agent Identity exige
  que el proyecto esté en una organización (hoy "sin organización"). Fase 3 hecha en parte (29 sep): arnés con cliente simulado por LLM, prompt de disputas 1.1.0 y GenAI Evaluation Service
  con trayectoria y rúbrica de tono (`ia/evaluacion/reportes/geap_2026-09-29.md`): 12 de 21 escenarios pasan, 0 inseguros;
  falla sobre todo la llamada malformada que persiste tras el reintento y la ruta (escalar, bloquear). Quedan E8 y E9 sin
  correr en la corrida final.
  `roles/editor` sigue en la cuenta de Compute (la usa Cloud Build); retirarlo tras mover los builds a su propia cuenta.

## Desplegar el sitio

La CLI de Firebase de esta máquina tiene otra cuenta; se despliega con una configuración aislada y las
credenciales de gcloud (ADC) del dueño del proyecto:

```bash
XDG_CONFIG_HOME=<carpeta temporal> GOOGLE_APPLICATION_CREDENTIALS=%APPDATA%/gcloud/application_default_credentials.json   firebase deploy --only hosting --project latam-bank-hackaton-2026
```

## Pendientes del usuario

1. Correr `terraform plan` en `tecnologia/infra/terraform/envs/dev` (ver `tecnologia/infra/ARRANQUE.md`): `fmt` y `validate`
   ya pasan; el `plan` adopta lo desplegado con `importar.tf` y no se ha corrido. El presupuesto se importa a mano.
2. Instalar `just` (las recetas del `justfile` se usan en la documentación).
3. Revisar el perfil `default` de AWS (quedaron ahí las llaves del organizador) y revocar el token de Hugging Face.
4. Meta (WhatsApp) y Twilio en modo de prueba, si se quieren canales reales; preguntas a los organizadores.
5. Mover el proyecto a la organización si se quiere Agent Identity en lugar de la cuenta `latam-chat@`.

## Banco de punta a punta (D-33), en producción

- **Sitio público** https://latam-bank-hackaton-2026.web.app: marca, selector MX/CO/AR, productos, ayuda, seguridad,
  contacto, reclamos, transparencia y privacidad.
- **Banca en línea** `/banca/`: seis clientes de demostración con historia (dos por país), productos, movimientos
  del oro operacional, detalle con "No reconozco este cargo" y "Bloquear tarjeta", asistente flotante, `/banca/reclamos`.
- **Consola del experto** `/operador/`: cola por prioridad, paquete de traspaso de 19 campos, mismo hilo, resolución.
  El código de acceso es `LATAM_OPERADOR_CODIGO` de Cloud Run
  (`gcloud run services describe latam-chat --region us-central1 --format="value(spec.template.spec.containers[0].env)"`).
- **Casos, bloqueos, traspasos y mensajes** en Firestore; los comparten Cloud Run y Agent Runtime.
- **Probado de punta a punta en producción (29 sep):** ingresar, movimientos, reclamar con la transacción fijada, aprobar,
  "Mis reclamos", pedir persona, cola con país correcto, tomar, mensaje visible para el cliente y resolver.
- Todos los frentes tienen modo `?demo=local` con fixtures para revisarlos sin backend.
- Provisionales por definir con Gobierno: tiempos de atención por prioridad (P1 120 s a P4 3600 s) y las 48 h del
  abono provisional de México.

## Evaluación del agente

**Evaluación en GEAP (29 sep, `ia/evaluacion/reportes/geap_2026-09-29.md`):** 12 de 21 escenarios (57%), 0 inseguros,
0 violaciones de registro y de enmascarado; trayectoria exacta 52% y en orden 62% en el GenAI Evaluation Service;
tono 2,95 de 5. Causa principal de fallas: llamadas malformadas de Gemini 2.5 por el endpoint compatible con OpenAI
(6 de 21 tras el reintento); las demás son de ruta (no escala, no bloquea). Costo total de la evaluación: unos US$0,07.

## Siguientes historias, en orden

1. **IA:** volver a Gemini 3 con el proveedor nativo de Google (es la causa principal de fallas en la evaluación) (sacar dbt-bigquery del lock del workspace, por
   ejemplo con `uvx`, para destrabar `pydantic-ai-slim[google]`); IA-3.1 e IA-7.2.
2. **Gobierno:** fijar el umbral de ESC-04 (hoy 1.000 USD provisional por moneda) y revisar la guía de estilo (S-CLI-02).
3. **Clientes:** CLI-2.1 (etiquetas de los componentes en `es.yaml`; hoy en `canales/textos.py`), CLI-1.4 y CLI-1.5 (portugués).
4. **Tecnología:** mover las compilaciones de Cloud Build a su propia cuenta y retirar `roles/editor` de la de Compute;
   voz (spike S1) y WhatsApp de prueba.
5. **Presidencia:** reporte final y guion de la demo (CLI-5.4).

## Cómo se trabaja

Worktree vivo: `../fh-datos` (guarda la copia local del bucket en `data/`, fuera de git). La carpeta `../fh-tec` quedó huérfana (git ya no la registra; se puede borrar a mano).

Ramas `feature/<cara>-<historia>-<tema>` desde `develop`, una por subagente en su propio worktree (`../fh-<tema>`);
se fusionan a `develop` con `just check` en verde. Commits de una línea.
