variable "project_id" { type = string }
variable "location" {
  type    = string
  default = "US"
}
variable "etiquetas" { type = map(string) }
variable "cuenta_pipeline" {
  description = "Correo de la cuenta de servicio del pipeline."
  type        = string
}
