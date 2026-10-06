variable "project_id" {
  type    = string
  default = "latam-bank-hackaton-2026"
}
variable "project_number" {
  type    = string
  default = "47808508188"
}
variable "billing_account" { type = string }
variable "dueno_email" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "entorno" {
  type    = string
  default = "dev"
}
variable "presupuesto_monto" {
  type    = number
  default = 20000
}
variable "presupuesto_moneda" {
  type    = string
  default = "COP"
}
variable "bigquery_location" {
  type    = string
  default = "US"
}
variable "trabajador_version" {
  description = "Debe coincidir con ia/agentes/trabajadores/disputas.yaml."
  type        = string
  default     = "0.8.0"
}
variable "agent_runtime_recurso" {
  description = "projects/<numero>/locations/us-central1/reasoningEngines/<id>, que imprime desplegar.py."
  type        = string
  default     = "projects/47808508188/locations/us-central1/reasoningEngines/6796256743388086272"
}
variable "operador_codigo" {
  description = "Se pasa con TF_VAR_operador_codigo (el valor vive en el servicio, no en el repositorio)."
  type        = string
  sensitive   = true
}
