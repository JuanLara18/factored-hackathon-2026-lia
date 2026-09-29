output "urls" { value = { for k, s in google_cloud_run_v2_service.s : k => s.uri } }
