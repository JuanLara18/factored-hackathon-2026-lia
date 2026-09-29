variable "project_id" { type = string }
variable "project_number" { type = string }
variable "region" { type = string }
variable "etiquetas" { type = map(string) }
variable "bucket_espejo" {
  description = "Nombre globalmente unico del bucket de aterrizaje."
  type        = string
}
variable "bucket_s3" {
  description = "Nombre del bucket S3 del organizador."
  type        = string
}
variable "transferencia_activa" {
  description = "Dejar en false hasta cargar la version del secreto con las llaves AWS."
  type        = bool
  default     = false
}
variable "inicio" {
  type = object({ year = number, month = number, day = number })
  default = {
    year  = 2026
    month = 9
    day   = 29
  }
}
