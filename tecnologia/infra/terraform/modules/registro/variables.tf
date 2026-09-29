variable "project_id" { type = string }
variable "region" { type = string }
variable "nombre" {
  type    = string
  default = "imagenes"
}
variable "etiquetas" { type = map(string) }
variable "versiones_a_conservar" {
  type    = number
  default = 5
}
variable "dias_retencion" {
  type    = number
  default = 14
}
