locals {
  prefijo = "lb-${var.entorno}"
  # R-TEC-19: etiquetas obligatorias; "componente" lo refina cada modulo.
  etiquetas = {
    mision     = "cargo-no-reconocido"
    entorno    = var.entorno
    componente = "plataforma"
    dueno      = "tecnologia"
  }
}

# R-TEC-18: el presupuesto va primero; todo lo demas depende de el.
module "presupuesto" {
  source          = "../../modules/presupuesto"
  project_id      = var.project_id
  project_number  = var.project_number
  billing_account = var.billing_account
  prefijo         = local.prefijo
  correos_alerta  = var.correos_alerta
  monto           = var.presupuesto_monto
}

module "proyecto" {
  source     = "../../modules/proyecto"
  project_id = var.project_id
  depends_on = [module.presupuesto]
}

module "identidades" {
  source     = "../../modules/identidades"
  project_id = var.project_id
  prefijo    = local.prefijo
  depends_on = [module.proyecto]
}

module "wif" {
  source         = "../../modules/wif"
  project_id     = var.project_id
  prefijo        = local.prefijo
  repositorio    = var.repositorio_github
  cuenta_cd_name = module.identidades.cd_name
}

module "registro" {
  source     = "../../modules/registro"
  project_id = var.project_id
  region     = var.region
  etiquetas  = merge(local.etiquetas, { componente = "registro" })
  depends_on = [module.proyecto, module.presupuesto]
}

module "secretos" {
  source         = "../../modules/secretos"
  project_id     = var.project_id
  region         = var.region
  prefijo        = local.prefijo
  etiquetas      = merge(local.etiquetas, { componente = "secretos" })
  cuenta_lectora = module.identidades.servicios_email
  depends_on     = [module.proyecto, module.presupuesto]
}

module "datos" {
  source          = "../../modules/datos"
  project_id      = var.project_id
  region          = var.region
  prefijo         = local.prefijo
  etiquetas       = merge(local.etiquetas, { componente = "datos" })
  bucket_oro      = var.bucket_oro
  crear_cloud_sql = var.crear_cloud_sql
  encendida       = var.cloud_sql_encendida
  usuarios_iam    = [module.identidades.servicios_email]
  depends_on      = [module.proyecto, module.presupuesto]
}

module "servicios" {
  source          = "../../modules/servicios"
  project_id      = var.project_id
  region          = var.region
  etiquetas       = local.etiquetas
  cuenta_servicio = module.identidades.servicios_email
  depends_on      = [module.proyecto, module.presupuesto]
}

module "espejo" {
  source               = "../../modules/espejo"
  project_id           = var.project_id
  project_number       = var.project_number
  region               = var.region
  etiquetas            = merge(local.etiquetas, { componente = "espejo" })
  bucket_espejo        = var.bucket_espejo
  bucket_s3            = var.bucket_s3_organizador
  transferencia_activa = var.transferencia_activa
  depends_on           = [module.proyecto, module.presupuesto]
}

module "pipeline" {
  source        = "../../modules/pipeline"
  project_id    = var.project_id
  region        = var.region
  prefijo       = local.prefijo
  etiquetas     = local.etiquetas
  bucket_espejo = module.espejo.bucket
  depends_on    = [module.proyecto, module.presupuesto]
}

module "bigquery" {
  source          = "../../modules/bigquery"
  project_id      = var.project_id
  location        = var.bigquery_location
  etiquetas       = local.etiquetas
  cuenta_pipeline = module.pipeline.cuenta_email
  depends_on      = [module.proyecto, module.presupuesto]
}
