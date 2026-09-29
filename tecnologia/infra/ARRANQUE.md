# Arranque manual de Google Cloud (TEC-0.6)

Lo único manual es esto (R-TEC-15). Todo lo demás lo declara Terraform en `terraform/`. Regla de la decisión
D-29: crédito de prueba de Google Cloud, sin activar la cuenta completa, gasto real menor a US$20.

1. `gcloud auth login` y `gcloud auth application-default login` con la cuenta del equipo.
2. Crear el proyecto y vincularlo a la cuenta de facturación de prueba (consola o `gcloud projects create`
   y `gcloud billing projects link`). Anotar el id, el número del proyecto y el id de la cuenta de facturación.
3. Crear el bucket de estado con versionado (nombre único global), por ejemplo
   `gcloud storage buckets create gs://<bucket> --location=us-central1 --uniform-bucket-level-access`
   y `gcloud storage buckets update gs://<bucket> --versioning`. El módulo `modules/estado` documenta la
   misma configuración por si se quiere importarlo.
4. Habilitar a mano solo lo necesario para que Terraform arranque:
   `gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com cloudbilling.googleapis.com billingbudgets.googleapis.com`.
5. `cd terraform/envs/dev`, copiar `terraform.tfvars.example` a `terraform.tfvars` y completar los valores.
6. `terraform init -backend-config="bucket=<bucket>"`, `terraform plan` y `terraform apply`. El presupuesto
   con alertas al 50, 80 y 100% se crea antes que cualquier recurso con costo (R-TEC-18).
7. Comprobar que llegó la alerta de prueba al correo y anotarlo en la bitácora.
8. Con la salida `wif_proveedor` y `cuenta_cd`, configurar los secretos de repositorio de GitHub que usa la
   acción de autenticación (sin llaves, R-TEC-21). La condición limita el acceso a este repositorio y a `main`.

Los valores de los secretos (Twilio, Meta, LiteLLM) se cargan con `gcloud secrets versions add`, nunca en
Terraform ni en git.

## Costo

Cloud Run escala a cero. Cloud SQL queda apagado por defecto (`crear_cloud_sql = false`); al activarlo
(TEC-11.2) usa `db-f1-micro` zonal sin respaldos, y `cloud_sql_encendida = false` lo apaga (demo-off).
Para desmontar: poner `proteccion_borrado = false` en el módulo `datos` y ejecutar `terraform destroy`
(R-TEC-20); el bucket de estado no forma parte del desmontaje.

## Datos en Google Cloud (D-30)

Terraform crea los ocho datasets de BigQuery y el Cloud Run Job `pipeline-datos` (validaciones y dbt sobre
BigQuery). `latam_seguridad` solo lo lee la cuenta del pipeline. Las tablas crudas deben existir en `latam_bronce` antes de correr el pipeline (las deja un proceso externo).

Los servicios usan Vertex AI (Gemini y Model Garden como servicio) con el rol `roles/aiplatform.user`; la
API `aiplatform` se habilita en el módulo `proyecto`. Si un modelo de Model Garden pide aceptar términos,
se hace una vez en la consola.
