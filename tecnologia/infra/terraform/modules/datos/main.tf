resource "google_sql_database_instance" "pg" {
  count               = var.crear_cloud_sql ? 1 : 0
  project             = var.project_id
  name                = "${var.prefijo}-pg"
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = var.proteccion_borrado

  settings {
    tier              = var.tier
    edition           = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_size         = 10
    disk_type         = "PD_HDD"
    disk_autoresize   = false
    # NEVER apaga la instancia (demo-off); ALWAYS la enciende.
    activation_policy = var.encendida ? "ALWAYS" : "NEVER"
    user_labels       = var.etiquetas

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled = false
    }

    ip_configuration {
      ipv4_enabled = true # sin red privada; acceso por IAM y el conector de Cloud SQL
    }
  }
}

resource "google_sql_database" "bases" {
  for_each = var.crear_cloud_sql ? toset(var.bases) : toset([])
  project  = var.project_id
  instance = google_sql_database_instance.pg[0].name
  name     = each.value
}

resource "google_sql_user" "iam" {
  for_each = var.crear_cloud_sql ? toset(var.usuarios_iam) : toset([])
  project  = var.project_id
  instance = google_sql_database_instance.pg[0].name
  # Las cuentas de servicio usan el correo sin el sufijo gserviceaccount.com
  name = trimsuffix(each.value, ".gserviceaccount.com")
  type = "CLOUD_IAM_SERVICE_ACCOUNT"
}

resource "google_storage_bucket" "oro" {
  project                     = var.project_id
  name                        = var.bucket_oro
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true
  labels                      = var.etiquetas
}
