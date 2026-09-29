locals {
  cuentas = {
    cd        = "Despliegue desde GitHub Actions"
    servicios = "Identidad de ejecucion de los servicios de Cloud Run"
  }
}

resource "google_service_account" "cuentas" {
  for_each     = local.cuentas
  project      = var.project_id
  account_id   = "${var.prefijo}-${each.key}"
  display_name = each.value
}

# Roles minimos de la cuenta de despliegue (sin llaves; entra por WIF).
resource "google_project_iam_member" "cd" {
  for_each = toset([
    "roles/run.developer",
    "roles/artifactregistry.writer",
    "roles/cloudsql.client",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cuentas["cd"].email}"
}

# El CD puede actuar como la identidad de ejecucion al desplegar revisiones.
resource "google_service_account_iam_member" "cd_actua_como_servicios" {
  service_account_id = google_service_account.cuentas["servicios"].name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cuentas["cd"].email}"
}

# Roles minimos de los servicios en ejecucion.
resource "google_project_iam_member" "servicios" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/cloudsql.instanceUser",
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cuentas["servicios"].email}"
}
