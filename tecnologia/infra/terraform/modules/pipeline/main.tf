resource "google_service_account" "pipeline" {
  project      = var.project_id
  account_id   = "${var.prefijo}-pipeline"
  display_name = "Pipeline de datos (Cloud Run Job)"
}

resource "google_project_iam_member" "job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# La escritura en los datasets (dataEditor) la da el modulo bigquery con bloques access.
resource "google_storage_bucket_iam_member" "lee_espejo" {
  bucket = var.bucket_espejo
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_cloud_run_v2_job" "pipeline" {
  project             = var.project_id
  name                = "pipeline-datos"
  location            = var.region
  deletion_protection = false
  labels              = merge(var.etiquetas, { componente = "pipeline-datos" })

  template {
    task_count = 1

    template {
      service_account = google_service_account.pipeline.email
      max_retries     = 1
      timeout         = "3600s"

      containers {
        image = var.imagen_inicial # el CD la reemplaza (R-TEC-17)

        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
      client,
      client_version,
    ]
  }
}
