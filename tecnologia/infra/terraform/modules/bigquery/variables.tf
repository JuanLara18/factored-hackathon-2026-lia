variable "project_id" { type = string }
variable "location" {
  type    = string
  default = "US"
}
variable "etiquetas" {
  type    = map(string)
  default = {}
}
variable "dueno_email" {
  description = "Cuenta humana dueña de los datasets (OWNER)."
  type        = string
}
variable "lectores_latam_bank" {
  description = "Cuentas de servicio con lectura de latam_bank (dataViewer a nivel de dataset)."
  type        = list(string)
  default     = []
}
variable "datasets" {
  description = "Datasets y su vencimiento por defecto de tablas nuevas en milisegundos (null = sin vencimiento)."
  type        = map(object({ vencimiento_ms = number, lectores = bool, descripcion = string }))
  default = {
    # Sin vencimiento desde el 30 sep: el de 60 días venía del sandbox y habría borrado las capas.
    latam_bank = {
      vencimiento_ms = null, lectores = true,
      descripcion    = "Capas bronce, plata, oro y platino con prefijo en el nombre de cada tabla (D-30)"
    }
    latam_seguridad = {
      vencimiento_ms = null, lectores = false,
      descripcion    = "Llave de tokenizacion; solo la cuenta del pipeline"
    }
    latam_pruebas = {
      vencimiento_ms = 604800000, lectores = false, # 7 días
      descripcion    = "Fallos guardados y temporales de las pruebas de dbt"
    }
  }
}
