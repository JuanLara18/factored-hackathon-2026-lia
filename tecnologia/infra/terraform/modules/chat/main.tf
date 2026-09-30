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
  deletion_protection = false
  labels              = merge(var.etiquetas, { proyecto = "latam-bank" })

  template {
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

      dynamic "env" {
        for_each = var.operador_codigo == null ? [] : [1]
        content {
          name  = "LATAM_OPERADOR_CODIGO"
          value = var.operador_codigo
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
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
