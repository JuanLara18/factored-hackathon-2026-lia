variable "project_id" { type = string }
variable "region" { type = string }
variable "nombre" {
  description = "Nombre globalmente unico del bucket de estado."
  type        = string
}
variable "etiquetas" { type = map(string) }
