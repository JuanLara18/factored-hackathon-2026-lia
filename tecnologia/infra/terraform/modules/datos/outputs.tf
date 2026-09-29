output "conexion" { value = try(google_sql_database_instance.pg[0].connection_name, null) }
output "bucket_oro" { value = google_storage_bucket.oro.name }
