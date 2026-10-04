# Infraestructura de Google Cloud

Proyecto `latam-bank-hackaton-2026` (número `47808508188`), facturación abierta con presupuesto de COP 20.000
al mes (D-29, D-32). Lo que hay desplegado se creó a mano y con `gcloud`; `terraform/envs/dev` lo declara y lo
adopta con `importar.tf`. **Terraform no se ha aplicado nunca**: `terraform validate` pasa (1.16, proveedor
`google ~> 6.0`), pero el `plan` contra el proyecto real está pendiente de que lo corra el dueño.

## Qué declara Terraform

| Módulo | Recursos |
|---|---|
| `presupuesto` | presupuesto mensual `latam-bank-hackaton-2026 tope` en COP 20.000, con alertas al 25, 50 y 100% del gasto y al 100% del pronóstico |
| `proyecto` | APIs que usa la plataforma |
| `firestore` | base `(default)` en `nam5`, modo nativo (D-33: casos, bloqueos, traspasos y mensajes) |
| `chat` | cuenta `latam-chat@` (`bigquery.jobUser`, `aiplatform.user`, `cloudtrace.agent`, `datastore.user`), bucket `<proyecto>-staging` con borrado a los 7 días, servicio Cloud Run `latam-chat` (1 vCPU, 1 GiB, 0 a 1 instancia, concurrencia 40, 300 s, puerto 7860, acceso público) con sus variables de entorno |
| `bigquery` | `latam_bank` (capas como prefijo), `latam_seguridad` (llave de seudonimización) y `latam_pruebas` (fallos de dbt); `latam-chat@` lee `latam_bank` con `dataViewer` a nivel de dataset y no ve `latam_seguridad` |

## Qué no declara y por qué

- **Agent Runtime.** El agente de disputas lo despliega el script `agent_runtime/desplegar.py` con el SDK (`just
  desplegar-agente`), porque el recurso `reasoningEngines` se empaqueta desde el código. El recurso actual se pasa a
  Cloud Run en `LATAM_AGENT_RUNTIME_RECURSO` (variable `agent_runtime_recurso`).
- **La imagen de `latam-chat`.** La construye `just desplegar-chat-run-agente` con `gcloud run deploy --source` (Cloud
  Build); Terraform ignora la imagen. El repositorio `cloud-run-source-deploy` de Artifact Registry y el bucket
  `run-sources-*` los crea `gcloud` solo.
- **Sitio.** Firebase Hosting se despliega con la CLI de Firebase (ver `presidencia/ESTADO.md`).
- **Estado remoto.** No existe bucket de estado: el estado es local. Para trabajar en equipo hay que crear uno con
  versionado y añadir `backend "gcs"`.
- **Retirado** por no existir en el proyecto: Cloud SQL, Workload Identity Federation y cuenta de despliegue, Cloud Run
  Job `pipeline-datos` y Artifact Registry propio. El pipeline de datos corre desde la máquina del dueño (dbt y la
  carga usan sus credenciales).
- **Secret Manager.** Existe un secreto creado a mano el 30 sep, `latam-ref-secreto` (clave de las referencias opacas
  de la API), que Cloud Run monta como `LATAM_REF_SECRETO` y que `latam-chat@` lee con `secretAccessor`. Todavía no
  está en Terraform: hay que añadirlo al adoptar lo desplegado.

## Adoptar lo desplegado (sin aplicar)

```bash
cd tecnologia/infra/terraform/envs/dev
cp terraform.tfvars.example terraform.tfvars      # billing_account y dueno_email
terraform init
terraform plan                                    # leer el plan: debe adoptar sin destruir
```

El presupuesto se importa a mano (ver el final de `importar.tf`). Dos diferencias a tener presentes: los datasets
tienen vencimiento por defecto de 60 días (7 en `latam_pruebas`) y las tablas vigentes vencen el 28 de noviembre de 2026.

## Costo

Cloud Run escala a cero con una instancia como máximo; Agent Runtime escala a cero; Firestore cabe en el nivel
gratuito a este volumen. La evaluación completa del agente en GEAP costó unos US$0,07.

Los modelos se sirven desde Gemini Enterprise Agent Platform (Vertex AI) con `roles/aiplatform.user`; si un modelo de
Model Garden pide aceptar términos, se hace una vez en la consola.
