resource "google_cloud_run_v2_service" "s" {
  for_each            = var.servicios
  project             = var.project_id
  name                = each.key
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false
  labels              = merge(var.etiquetas, { componente = each.key })

  template {
    service_account                  = var.cuenta_servicio
    timeout                          = "${each.value.timeout_s}s"
    max_instance_request_concurrency = each.value.concurrencia

    scaling {
      min_instance_count = 0 # escala a cero
      max_instance_count = each.value.max_instancias
    }

    containers {
      image = var.imagen_inicial # el CD la reemplaza (R-TEC-17)

      resources {
        limits = {
          cpu    = each.value.cpu
          memory = each.value.memoria
        }
        cpu_idle = true
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

# Acceso publico a los servicios que lo piden; el resto exige IAM.
resource "google_cloud_run_v2_service_iam_member" "publico" {
  for_each = { for k, v in var.servicios : k => v if v.publico }
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.s[each.key].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
