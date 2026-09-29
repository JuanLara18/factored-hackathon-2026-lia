output "bucket" { value = google_storage_bucket.espejo.name }
output "secreto_aws" { value = google_secret_manager_secret.aws.secret_id }
output "trabajo_transferencia" { value = google_storage_transfer_job.s3.name }
