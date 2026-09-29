variable "project_id" { type = string }
variable "region" { type = string }
variable "etiquetas" { type = map(string) }
variable "cuenta_servicio" { type = string }
variable "imagen_inicial" {
  description = "Imagen de arranque; el CD despliega las reales."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
variable "servicios" {
  type = map(object({
    cpu            = optional(string, "1")
    memoria        = optional(string, "512Mi")
    max_instancias = optional(number, 2)
    concurrencia   = optional(number, 80)
    timeout_s      = optional(number, 300)
    publico        = optional(bool, false)
  }))
  default = {
    "lb-api" = { publico = true }
    "lb-voz" = { memoria = "1Gi", concurrencia = 4, timeout_s = 3600, publico = true }
  }
}
