variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "etiquetas" {
  type    = map(string)
  default = {}
}
variable "servicio" {
  type    = string
  default = "latam-chat"
}
variable "bucket_staging" {
  description = "Bucket de paquetes del despliegue de Agent Runtime."
  type        = string
}
variable "dias_staging" {
  type    = number
  default = 7
}
variable "imagen_inicial" {
  description = "Solo para crear el servicio: gcloud run deploy --source la reemplaza y Terraform ignora la imagen."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
variable "env" {
  description = "Variables de entorno del servicio (las mismas que fija just desplegar-chat-run-agente)."
  type        = map(string)
}
variable "operador_codigo" {
  description = "Código de acceso de la consola del experto (LATAM_OPERADOR_CODIGO). Nulo = no se declara."
  type        = string
  default     = null
  sensitive   = true
}
