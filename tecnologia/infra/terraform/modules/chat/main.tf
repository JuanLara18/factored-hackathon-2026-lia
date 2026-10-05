# Cuenta de ejecución del chat: mínimo privilegio (D-32). El agente en Agent Runtime NO se declara aquí:
# lo despliega tecnologia/infra/agent_runtime/desplegar.py (SDK de Agent Platform; `just desplegar-agente`)
# y su recurso se pasa al servicio en la variable LATAM_AGENT_RUNTIME_RECURSO.
resource "google_service_account" "chat" {
  project      = var.project_id
  account_id   = var.servicio
  display_name = "Chat de disputas (Cloud Run)"
}

locals {
  roles_proyecto = [
    "roles/bigquery.jobUser", # correr consultas (la lectura va por dataViewer del dataset)
    "roles/aiplatform.user",  # invocar el agente, Sessions y los modelos
    "roles/cloudtrace.agent", # enviar trazas
    "roles/datastore.user",   # Firestore: casos, bloqueos, traspasos y mensajes
  ]
}

resource "google_project_iam_member" "chat" {
  for_each = toset(local.roles_proyecto)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.chat.email}"
}

# Clave de las referencias opacas de la API (D-33). Terraform adopta el secreto y el permiso, no el valor:
# las versiones se crean a mano (`gcloud secrets versions add`) y nunca pasan por el estado.
resource "google_secret_manager_secret" "ref" {
  project   = var.project_id
  secret_id = var.secreto_ref

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "ref" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.ref.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.chat.email}"
}

# Paquetes del despliegue de Agent Runtime: se borran a los 7 días.
resource "google_storage_bucket" "staging" {
  project                     = var.project_id
  name                        = var.bucket_staging
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  labels                      = var.etiquetas

  lifecycle_rule {
    condition {
      age = var.dias_staging
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_cloud_run_v2_service" "chat" {
  project             = var.project_id
  name                = var.servicio
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = true
  labels              = merge(var.etiquetas, { proyecto = "latam-bank" })

  template {
    labels                           = { proyecto = "latam-bank" }
    service_account                  = google_service_account.chat.email
    timeout                          = "300s"
    max_instance_request_concurrency = 40

    scaling {
      min_instance_count = 0 # escala a cero
      max_instance_count = 1 # una instancia: la idempotencia de la demo vale por instancia
    }

    containers {
      image = var.imagen_inicial
      ports {
        container_port = 7860
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }

      # Sin esta variable el servicio no arranca (latam_tecnologia.banca.refs).
      env {
        name = "LATAM_REF_SECRETO"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.ref.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "LATAM_OPERADOR_CODIGO"
        value = var.operador_codigo
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      build_config, # lo escribe `gcloud run deploy --source` en cada despliegue
      scaling,      # el día de la demo se sube a mano con --min-instances 1
      client,
      client_version,
    ]
  }
}

# El sitio y la banca llaman al chat sin credenciales de Google; el acceso lo limitan la sesión y el código del experto.
resource "google_cloud_run_v2_service_iam_member" "publico" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.chat.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Mantiene despierta la instancia: sin el ping, el primer acceso tras un rato paga el arranque en frío.
# No despierta al agente de Agent Runtime.
resource "google_cloud_scheduler_job" "despierto" {
  project          = var.project_id
  region           = var.region
  name             = "${var.servicio}-despierto"
  description      = "Mantiene despierta la instancia de Cloud Run del demo (evita el arranque en frio)"
  schedule         = "*/5 * * * *"
  time_zone        = "America/Bogota"
  attempt_deadline = "60s"

  http_target {
    http_method = "GET"
    uri         = "https://${var.servicio}-${var.project_number}.${var.region}.run.app/api/textos?registro=usted"
  }

  retry_config {
    max_backoff_duration = "3600s"
    max_doublings        = 5
    max_retry_duration   = "0s"
    min_backoff_duration = "5s"
    retry_count          = 0
  }
}
