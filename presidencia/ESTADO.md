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

Dataset `latam_bank`, con la capa como prefijo de tabla (7,2 GB lógicos en 45 objetos; ya no rige el tope de 10 GB del sandbox porque hay facturación, y el almacenamiento activo de este volumen cuesta centavos al mes. Las tablas ya no vencen: el vencimiento del sandbox se quitó el 30 sep en `latam_bank` y `latam_seguridad`, también como valor por defecto del dataset):

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
  (Agent Runtime, escala a cero, Sessions de 24 h; se invoca con la cuenta `latam-chat@`). Modelo: `gemini-3.1-flash-lite`
  con el proveedor nativo de Google en GEAP (región `global`), prompt `disputas/agente@1.2.0`, trabajador `disputas` 0.3.0.
  Trazas en Cloud Trace con `latam.trabajador.id` y versión.
- **Redesplegar el agente (actualiza el mismo recurso):** `uv run --with "google-cloud-aiplatform[agent_engines]" --with
  cloudpickle python tecnologia/infra/agent_runtime/desplegar.py --bucket latam-bank-hackaton-2026-staging --recurso
  projects/47808508188/locations/us-central1/reasoningEngines/6796256743388086272`. **Chat:** `just desplegar-chat-run-agente <recurso>`
  (usa `--update-env-vars`; la clave de referencias viene de Secret Manager, `latam-ref-secreto`). Al guion: `LATAM_MODELO=guionado`.
- **Pendiente:** Agent Identity exige que el proyecto esté en una organización (hoy "sin organización").
  `roles/editor` sigue en la cuenta de Compute (la usa Cloud Build); retirarlo tras mover los builds a su propia cuenta.
  Sesiones, confirmaciones y operadores viven en memoria por instancia de Cloud Run (máximo 1 instancia); para escalar
  a varias hay que moverlos a Firestore.

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

## Barrido de errores (30 sep), fusionado

Reportes: `tecnologia/web/QA_2026-09-30.md` (QA en navegador real, suite en `tests/e2e/`, se corre con
`LATAM_E2E=1 LATAM_E2E_OPERADOR=<código> uv run --with playwright pytest tests/e2e`),
`tecnologia/REVISION_BACKEND_2026-09-30.md`, `tecnologia/web/HALLAZGOS_BACKEND.md` e
`ia/evaluacion/reportes/geap_2026-09-30.md`. Lo principal: enlaces de `/banca` que salían del banco, bloqueo de tarjetas,
saldos (tabla nueva `oro_operacional_saldos_productos`, solo para la banca), montos de México, tiempos máximos hacia el
agente, turnos vacíos como falla, ids de mensaje ordenables, tablas de BigQuery sin vencimiento, Terraform alineado y
enlaces de la documentación. Después del despliegue apareció uno más: los handlers async con consultas a BigQuery y
Firestore bloqueaban el bucle de eventos de la única instancia (la banca tardaba más de 20 s bajo carga); ahora son
síncronos y corren en hilos, con prueba de regresión.

**Verificación en producción (30 sep):** la suite de Playwright (`tests/e2e/`) contra https://latam-bank-hackaton-2026.web.app
pasa entera (70 pruebas, 1 omitida), incluido el recorrido reclamo, persona, experto y resolución; los únicos avisos del
log son los 401 que las pruebas provocan a propósito. El primer acceso tras un rato sin uso tarda unos segundos por el
arranque en frío; para el día de la demo conviene `--min-instances 1` en Cloud Run (costo de unos centavos por hora).

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

**Evaluación en GEAP (30 sep, `ia/evaluacion/reportes/geap_2026-09-30.md`):** 19 de 23 escenarios (83%) con
Gemini 3.1 Flash-Lite nativo, 0 inseguros, 0 llamadas malformadas (antes 12 de 21 y 6 malformadas con 2.5 por el
endpoint compatible con OpenAI). Las fallas restantes son de ruta (un bloqueo de más, escalar cuando el simulador pide
persona). El 29 sep el GenAI Evaluation Service dio trayectoria exacta 52% y en orden 62%; falta repetirlo.

## En curso (4 oct)

| Rama | Worktree | Qué hace |
|---|---|---|
| `feature/ia-ia-5-4-evaluacion-final` | `../fh-eval2` | conjunto retenido (~30 casos con fallas, inyección, sesión vencida, acceso ajeno), línea base contra sistema, métricas del enunciado, `presidencia/reporte/04_evaluacion.md` |
| `feature/gobierno-gob-equidad` | `../fh-equidad` | equidad histórica por país, segmento, canal, edad y género (solo auditoría, agregada) y función de cortes para la evaluación; `presidencia/reporte/05_equidad.md` |
| `feature/ia-ia-10-riesgo-plazo` | `../fh-sla` | segundo componente aprendido: riesgo de incumplir el plazo al radicar la disputa; solo sube la prioridad del traspaso |

## Qué falta para la entrega (contra el enunciado, 3 oct)

`main` = `develop` = producción desde el 3 oct. Brechas, en orden de impacto en la calificación:

1. **Hecho (3 oct):** plantillas pt-BR (você) con retrotraducción, selector de idioma en banca, widget y chat, prompt 1.3.0 con cambio y mezcla de idioma, 9 escenarios pt en GEAP (`ia/evaluacion/reportes/geap_pt_2026-10-03.md`), recorrido pt verificado en producción. Falta revisión de un hablante nativo. Antes: **Portugués** (obligatorio: "demonstrate interactions in Spanish and Portuguese"): el prompt tiene `pt voce`, pero
   plantillas, sitio, banca y escenarios están solo en español (CLI-1.5). Faltan plantillas pt, interruptor de idioma,
   escenarios pt en el arnés y un caso de demo; el dataset no trae clientes de Brasil (limitación que hay que declarar).
2. **Hecho (3 oct):** clasificador de motivo de contacto, `ia/evaluacion/reportes/clasificador_2026-10-03.md` y model card. Antes: **Componente aprendido contra línea base** (criterio 4): no hay ninguno evaluado. Lo más directo: clasificador de
   motivo/intención (IA-2.x) con etiquetas válidas (semilla humana IA-1.1 o etiquetas derivadas de `complaints`),
   partición temporal sin fuga, línea base de reglas y métricas con umbrales justificados; o el experimento de
   `fraud_score` (IA-10.1).
3. **Hecho (3 oct):** `presidencia/reporte/01_problema.md` y 10 figuras (`uv run python -m latam_datos.analisis`). Antes: **Problema sustentado con datos** (criterio 1): análisis escrito de motivos de contacto, demanda, calidad y
   restricciones operativas (bloques A a C de Datos) que justifique elegir disputas y fije la línea base de negocio.
4. **Evaluación con las métricas del enunciado** (criterio 5 y "Evaluation evidence"): sobre el mismo conjunto
   retenido, línea base (B-reglas) contra el sistema; resolución automática segura, contención, calidad de escalamiento
   (faltantes e innecesarias), resultados inseguros con denominador, p50/p95 de latencia y costo por caso y por
   resolución, variabilidad entre corridas, cortes por idioma y segmento, validación del juez. Faltan casos de
   inyección de prompt, sesión vencida, acceso no autorizado y falla de herramienta en el arnés.
5. **Equidad**: comparar resultados por segmento autorizado (`plata_restringida_clientes`) y por idioma.
6. **Reporte final y demo** (D10): reporte con todo lo anterior, "AI-first" (PRE-3.4), capítulo de trabajo restante
   para producción (PRE-3.5), capacidad, monitoreo, controles de acceso y retención; guion y grabación de la demo
   (normal, ambiguo y traspaso a persona, en español y portugués); dictamen de Auditoría (AUD-1 a AUD-3).
7. **Pulido**: umbrales provisionales de Gobierno (ESC-04, tiempos por prioridad, 48 h de México); `--min-instances 1`
   el día de la demo; decidir si el repositorio se hace público (sin datos ni credenciales: la guarda lo asegura).

## Cómo se trabaja

Worktree vivo: `../fh-datos` (guarda la copia local del bucket en `data/`, fuera de git). La carpeta `../fh-tec` quedó huérfana (git ya no la registra; se puede borrar a mano).

Ramas `feature/<cara>-<historia>-<tema>` desde `develop`, una por subagente en su propio worktree (`../fh-<tema>`);
se fusionan a `develop` con `just check` en verde. Commits de una línea.
