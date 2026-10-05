# Monitoreo operativo del canal (criterio 6): disponibilidad, errores y latencia de `latam-chat`.
# Calidad, equidad y resultados inseguros no salen de métricas de plataforma: se miden con el registro
# por caso (presidencia/reporte/06_produccion.md, sección 6).
resource "google_monitoring_notification_channel" "correo" {
  project      = var.project_id
  display_name = "Dueño de la plataforma"
  type         = "email"
  labels = {
    email_address = var.correo
  }
}

resource "google_monitoring_uptime_check_config" "chat" {
  project      = var.project_id
  display_name = "${var.servicio}: /api/textos"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = "/api/textos"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = trimprefix(var.url, "https://")
    }
  }
}

locals {
  recurso = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"${var.servicio}\""
}

resource "google_monitoring_alert_policy" "caido" {
  project      = var.project_id
  display_name = "${var.servicio}: no responde"
  combiner     = "OR"

  conditions {
    display_name = "La comprobación falla desde dos regiones o más"
    condition_threshold {
      filter          = "metric.type = \"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type = \"uptime_url\" AND metric.labels.check_id = \"${google_monitoring_uptime_check_config.chat.uptime_check_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.host"]
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.correo.id]
  documentation {
    content = "El canal no responde. El sitio estático sigue en pie y el traspaso a una persona no depende del modelo. Revisar la última revisión de Cloud Run y volver a la anterior si hace falta."
  }
}

resource "google_monitoring_alert_policy" "errores" {
  project      = var.project_id
  display_name = "${var.servicio}: respuestas 5xx sobre ${var.tasa_5xx * 100}%"
  combiner     = "OR"

  conditions {
    display_name = "Proporción de 5xx en 5 minutos"
    condition_threshold {
      filter             = "metric.type = \"run.googleapis.com/request_count\" AND ${local.recurso} AND metric.labels.response_code_class = \"5xx\""
      denominator_filter = "metric.type = \"run.googleapis.com/request_count\" AND ${local.recurso}"
      comparison         = "COMPARISON_GT"
      threshold_value    = var.tasa_5xx
      duration           = "0s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
      denominator_aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.correo.id]
  documentation {
    content = "Sube la tasa de errores del canal. Un 503 suele ser el agente de Agent Runtime o la cuota del modelo (429); el cliente recibe la plantilla de falla con la opción de una persona."
  }
}

resource "google_monitoring_alert_policy" "latencia" {
  project      = var.project_id
  display_name = "${var.servicio}: p95 sobre ${var.latencia_p95_ms} ms"
  combiner     = "OR"

  conditions {
    display_name = "p95 de la petición durante 10 minutos"
    condition_threshold {
      filter          = "metric.type = \"run.googleapis.com/request_latencies\" AND ${local.recurso}"
      comparison      = "COMPARISON_GT"
      threshold_value = var.latencia_p95_ms
      duration        = "600s"
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MAX"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.correo.id]
  documentation {
    content = "El canal responde lento. Incluye turnos del agente (modelo y herramientas) y lecturas de la banca; el arranque en frío del agente puede dispararla tras un rato sin uso."
  }
}
