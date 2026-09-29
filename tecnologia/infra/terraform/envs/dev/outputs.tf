output "registro" { value = module.registro.repositorio }
output "urls_servicios" { value = module.servicios.urls }
output "wif_proveedor" { value = module.wif.proveedor }
output "cuenta_cd" { value = module.identidades.cd_email }
output "cloud_sql" { value = module.datos.conexion }
output "job_pipeline" { value = module.pipeline.job }
output "datasets" { value = module.bigquery.datasets }
