variable "project_id" { type = string }
variable "region" { type = string }
variable "prefijo" { type = string }
variable "etiquetas" { type = map(string) }
variable "imagen_inicial" {
  type    = string
  default = "us-docker.pkg.dev/cloudrun/container/job"
}
