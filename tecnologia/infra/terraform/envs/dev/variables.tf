variable "project_id" { type = string }
variable "project_number" { type = string }
variable "billing_account" { type = string }
variable "correos_alerta" { type = list(string) }
variable "bucket_oro" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "entorno" {
  type    = string
  default = "dev"
}
variable "repositorio_github" {
  type    = string
  default = "JuanLara18/factored-hackathon-2026"
}
variable "presupuesto_monto" {
  type    = number
  default = 250
}
variable "crear_cloud_sql" {
  type    = bool
  default = false
}
variable "cloud_sql_encendida" {
  type    = bool
  default = true
}
variable "bigquery_location" {
  type    = string
  default = "US"
}
