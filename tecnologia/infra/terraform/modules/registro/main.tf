resource "google_artifact_registry_repository" "imagenes" {
  project       = var.project_id
  location      = var.region
  repository_id = var.nombre
  format        = "DOCKER"
  description   = "Imagenes de los servicios"
  labels        = var.etiquetas

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "conservar-recientes"
    action = "KEEP"
    most_recent_versions {
      keep_count = var.versiones_a_conservar
    }
  }

  cleanup_policies {
    id     = "borrar-viejas"
    action = "DELETE"
    condition {
      older_than = "${var.dias_retencion * 86400}s"
    }
  }
}
