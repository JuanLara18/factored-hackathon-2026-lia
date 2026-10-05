output "politicas" {
  value = [
    google_monitoring_alert_policy.caido.name,
    google_monitoring_alert_policy.errores.name,
    google_monitoring_alert_policy.latencia.name,
  ]
}
