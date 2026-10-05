variable "project_id" { type = string }
variable "servicio" {
  description = "Servicio de Cloud Run que se vigila."
  type        = string
}
variable "url" {
  description = "URL del servicio (https://...), para la comprobación de disponibilidad."
  type        = string
}
variable "correo" {
  description = "A quién avisan las alertas."
  type        = string
}
variable "tasa_5xx" {
  description = "Proporción de respuestas 5xx en 5 minutos que dispara la alerta (06_produccion, sección 6)."
  type        = number
  default     = 0.02
}
variable "latencia_p95_ms" {
  description = "p95 de la petición al canal: 1,25 veces el p95 por turno medido fuera de línea (4,61 s)."
  type        = number
  default     = 5760
}
