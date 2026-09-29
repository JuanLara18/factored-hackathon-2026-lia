resource "google_storage_bucket" "espejo" {
  project                     = var.project_id
  name                        = var.bucket_espejo
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  labels                      = var.etiquetas
}

# Un solo secreto con JSON access_key_id y secret_access_key.
# Terraform crea el contenedor vacio; la version se carga a mano con gcloud.
resource "google_secret_manager_secret" "aws" {
  project   = var.project_id
  secret_id = "aws-organizador-credenciales"
  labels    = var.etiquetas

  replication {
    auto {}
  }
}

data "google_storage_transfer_project_service_account" "sts" {
  project = var.project_id
}

resource "google_secret_manager_secret_iam_member" "sts" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.aws.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_storage_transfer_project_service_account.sts.email}"
}

resource "google_storage_bucket_iam_member" "sts" {
  for_each = toset(["roles/storage.legacyBucketWriter", "roles/storage.objectAdmin"])
  bucket   = google_storage_bucket.espejo.name
  role     = each.value
  member   = "serviceAccount:${data.google_storage_transfer_project_service_account.sts.email}"
}

resource "google_storage_transfer_job" "s3" {
  project     = var.project_id
  description = "Copia del bucket S3 del organizador al espejo"
  status      = var.transferencia_activa ? "ENABLED" : "DISABLED"

  transfer_spec {
    aws_s3_data_source {
      bucket_name = var.bucket_s3
      # Sin llaves en Terraform ni en el estado: se leen de Secret Manager.
      credentials_secret = "projects/${var.project_number}/secrets/${google_secret_manager_secret.aws.secret_id}"
    }
    gcs_data_sink {
      bucket_name = google_storage_bucket.espejo.name
    }
    transfer_options {
      overwrite_when = "DIFFERENT"
    }
  }

  # DAT-1.5: cada 6 horas.
  schedule {
    schedule_start_date {
      year  = var.inicio.year
      month = var.inicio.month
      day   = var.inicio.day
    }
    repeat_interval = "21600s"
  }

  depends_on = [
    google_secret_manager_secret_iam_member.sts,
    google_storage_bucket_iam_member.sts,
  ]
}
