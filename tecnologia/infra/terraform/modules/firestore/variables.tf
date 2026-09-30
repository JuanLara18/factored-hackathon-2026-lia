variable "project_id" { type = string }
variable "location" {
  description = "Multirregión de Firestore (nam5 = Estados Unidos). No se puede cambiar después de crearla."
  type        = string
  default     = "nam5"
}
