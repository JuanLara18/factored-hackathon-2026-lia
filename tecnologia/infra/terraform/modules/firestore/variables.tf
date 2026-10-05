variable "project_id" { type = string }
variable "location" {
  description = "Multirregión de Firestore (nam5 = Estados Unidos). No se puede cambiar después de crearla."
  type        = string
  default     = "nam5"
}
variable "colecciones_con_vencimiento" {
  description = "Debe coincidir con COLECCIONES_CON_VENCIMIENTO de latam_tecnologia.banca.firestore."
  type        = list(string)
  default     = ["casos", "bloqueos", "traspasos", "conversaciones", "mensajes"]
}
