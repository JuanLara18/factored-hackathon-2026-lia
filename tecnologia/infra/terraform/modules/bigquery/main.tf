# Las capas van como prefijo en el nombre de cada tabla de latam_bank (bronce_, plata_,
# plata_restringida_, oro_analitico_, oro_aprendizaje_, oro_operacional_, platino_).
# latam_seguridad guarda la llave de seudonimización; latam_pruebas, los fallos de dbt.
resource "google_bigquery_dataset" "d" {
  for_each                    = var.datasets
  project                     = var.project_id
  dataset_id                  = each.key
  location                    = var.location
  labels                      = merge(var.etiquetas, { componente = each.key })
  default_table_expiration_ms = each.value.vencimiento_ms
  delete_contents_on_destroy  = false

  # Acceso tal como está desplegado (los grupos de proyecto vienen por defecto).
  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }
  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
  access {
    role          = "OWNER"
    user_by_email = var.dueno_email
  }

  dynamic "access" {
    for_each = each.value.lectores ? toset(var.lectores_latam_bank) : toset([])
    content {
      role          = "READER" # equivale a roles/bigquery.dataViewer sobre el dataset
      user_by_email = access.value
    }
  }
}
