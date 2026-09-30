output "datasets" { value = [for d in google_bigquery_dataset.d : d.dataset_id] }
