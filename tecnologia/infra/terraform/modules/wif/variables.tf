variable "project_id" { type = string }
variable "prefijo" { type = string }
variable "repositorio" {
  description = "owner/repo de GitHub."
  type        = string
  default     = "JuanLara18/factored-hackathon-2026"
}
variable "rama" {
  type    = string
  default = "main"
}
variable "cuenta_cd_name" {
  description = "Nombre completo de la cuenta de despliegue (projects/.../serviceAccounts/...)."
  type        = string
}
