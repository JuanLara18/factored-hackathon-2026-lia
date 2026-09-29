variable "project_id" { type = string }
variable "region" { type = string }
variable "prefijo" { type = string }
variable "etiquetas" { type = map(string) }
variable "bucket_oro" {
  description = "Nombre globalmente unico del bucket de oro (R-TEC-13: el manifiesto declara origen)."
  type        = string
}
variable "crear_cloud_sql" {
  description = "Cloud SQL es lo mas caro del entorno; se crea solo si se pide (TEC-11.2)."
  type        = bool
  default     = false
}
variable "encendida" {
  type    = bool
  default = true
}
variable "tier" {
  type    = string
  default = "db-f1-micro"
}
variable "proteccion_borrado" {
  description = "Se pone en false para just destroy-demo (R-TEC-20)."
  type        = bool
  default     = false
}
variable "bases" {
  type    = list(string)
  default = ["latam"]
}
variable "usuarios_iam" {
  description = "Correos de cuentas de servicio con acceso IAM a la base."
  type        = list(string)
  default     = []
}
