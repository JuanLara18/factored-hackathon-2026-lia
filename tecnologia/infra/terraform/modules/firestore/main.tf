# D-33: casos, bloqueos, traspasos y mensajes en Firestore, compartidos por Cloud Run y Agent Runtime.
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location
  type        = "FIRESTORE_NATIVE"

  # La base guarda el estado de la demo: Terraform no la borra.
  deletion_policy = "ABANDON"
}
