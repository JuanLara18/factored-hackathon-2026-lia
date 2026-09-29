variable "project_id" { type = string }
variable "project_number" { type = string }
variable "billing_account" { type = string }
variable "prefijo" { type = string }
variable "correos_alerta" { type = list(string) }
variable "moneda" {
  type    = string
  default = "USD"
}
variable "monto" {
  description = "Tope del presupuesto en la moneda (D-29: US$250 de credito de prueba)."
  type        = number
  default     = 250
}
variable "umbrales" {
  description = "Fracciones del monto que disparan alerta (R-TEC-18)."
  type        = list(number)
  default     = [0.5, 0.8, 1.0]
}
