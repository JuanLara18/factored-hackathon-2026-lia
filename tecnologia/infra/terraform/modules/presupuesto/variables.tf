variable "project_number" { type = string }
variable "billing_account" { type = string }
variable "nombre" {
  type    = string
  default = "latam-bank-hackaton-2026 tope"
}
variable "moneda" {
  type    = string
  default = "COP"
}
variable "monto" {
  description = "Tope mensual en la moneda de la cuenta (D-29: gasto real menor a US$20, unos COP 80.000; el tope es COP 20.000)."
  type        = number
  default     = 20000
}
variable "umbrales" {
  description = "Umbrales sobre el gasto actual; el pronóstico se alerta al 100% aparte."
  type        = list(number)
  default     = [0.25, 0.5, 1.0]
}
