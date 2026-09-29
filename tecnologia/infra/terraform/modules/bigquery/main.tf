locals {
  datasets = toset([
    "latam_bronce",
    "latam_plata",
    "latam_plata_restringida",
    "latam_oro_analitico",
    "latam_oro_aprendizaje",
    "latam_oro_operacional",
    "latam_platino",
    "latam_seguridad",
  ])
}

# El acceso es explicito: la cuenta del pipeline escribe en todos; en latam_seguridad
# solo ella, sin el grupo de propietarios del proyecto.
resource "google_bigquery_dataset" "d" {
  for_each   = local.datasets
  project    = var.project_id
  dataset_id = each.value
  location   = var.location
  labels     = merge(var.etiquetas, { componente = each.value })
  # Sin expiracion por defecto de tablas (default_table_expiration_ms no se define).
  delete_contents_on_destroy = true

  access {
    role          = "WRITER"
    user_by_email = var.cuenta_pipeline
  }

  dynamic "access" {
    for_each = each.value == "latam_seguridad" ? [] : [1]
    content {
      role          = "OWNER"
      special_group = "projectOwners"
    }
  }
}
