# D-33: casos, bloqueos, traspasos y mensajes en Firestore, compartidos por Cloud Run y Agent Runtime.
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location
  type        = "FIRESTORE_NATIVE"

  # La base guarda el estado de la demo: Terraform no la borra.
  deletion_policy = "ABANDON"
}

# Retención (D-27): los documentos llevan `expira_en` a 30 días de su creación (BancoFirestore) y Firestore
# los borra. La política va por grupo de colección; `mensajes` es subcolección de `conversaciones`.
resource "google_firestore_field" "vencimiento" {
  for_each   = toset(var.colecciones_con_vencimiento)
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = each.value
  field      = "expira_en"

  ttl_config {}

  # Solo se declara el TTL: los índices de un solo campo quedan con el valor por defecto de la base.
  lifecycle {
    ignore_changes = [index_config]
  }
}
