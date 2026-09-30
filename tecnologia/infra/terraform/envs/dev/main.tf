locals {
  # R-TEC-19: etiquetas obligatorias; "componente" lo refina cada módulo.
  etiquetas = {
    mision     = "cargo-no-reconocido"
    entorno    = var.entorno
    componente = "plataforma"
    dueno      = "tecnologia"
  }
}

# R-TEC-18: el presupuesto va primero; todo lo demás depende de él.
module "presupuesto" {
  source          = "../../modules/presupuesto"
  project_number  = var.project_number
  billing_account = var.billing_account
  monto           = var.presupuesto_monto
  moneda          = var.presupuesto_moneda
}

module "proyecto" {
  source     = "../../modules/proyecto"
  project_id = var.project_id
  depends_on = [module.presupuesto]
}

module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  depends_on = [module.proyecto]
}

module "chat" {
  source          = "../../modules/chat"
  project_id      = var.project_id
  region          = var.region
  etiquetas       = merge(local.etiquetas, { componente = "chat" })
  bucket_staging  = "${var.project_id}-staging"
  operador_codigo = var.operador_codigo
  env = {
    LATAM_GCP_PROJECT           = var.project_id
    LATAM_GCP_LOCATION          = var.bigquery_location
    LATAM_GEAP_LOCATION         = "global"
    LATAM_TRABAJADOR_VERSION    = var.trabajador_version
    LATAM_AGENT_RUNTIME_RECURSO = var.agent_runtime_recurso
  }
  depends_on = [module.proyecto]
}

module "bigquery" {
  source              = "../../modules/bigquery"
  project_id          = var.project_id
  location            = var.bigquery_location
  etiquetas           = local.etiquetas
  dueno_email         = var.dueno_email
  lectores_latam_bank = [module.chat.cuenta_email]
  depends_on          = [module.proyecto]
}
