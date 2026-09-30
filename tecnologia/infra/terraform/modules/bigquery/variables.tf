variable "project_id" { type = string }
variable "location" {
  type    = string
  default = "US"
}
variable "etiquetas" {
  type    = map(string)
  default = {}
}
variable "dueno_email" {
  description = "Cuenta humana dueña de los datasets (OWNER)."
  type        = string
}
variable "lectores_latam_bank" {
  description = "Cuentas de servicio con lectura de latam_bank (dataViewer a nivel de dataset)."
  type        = list(string)
  default     = []
}
variable "datasets" {
  description = "Datasets y su vencimiento por defecto de tablas nuevas en milisegundos (null = sin vencimiento)."
  type        = map(object({ vencimiento_ms = number, lectores = bool }))
  default = {
    latam_bank      = { vencimiento_ms = 5184000000, lectores = true }  # 60 días
    latam_seguridad = { vencimiento_ms = 5184000000, lectores = false } # llave de seudonimización
    latam_pruebas   = { vencimiento_ms = 604800000, lectores = false }  # 7 días: fallos de dbt
  }
}
