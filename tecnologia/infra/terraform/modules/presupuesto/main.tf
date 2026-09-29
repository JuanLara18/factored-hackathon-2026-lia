resource "google_monitoring_notification_channel" "correo" {
  for_each     = toset(var.correos_alerta)
  project      = var.project_id
  display_name = "Presupuesto ${each.value}"
  type         = "email"
  labels       = { email_address = each.value }
}

resource "google_billing_budget" "presupuesto" {
  billing_account = var.billing_account
  display_name    = "${var.prefijo}-presupuesto"

  budget_filter {
    projects               = ["projects/${var.project_number}"]
    credit_types_treatment = "EXCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = var.moneda
      units         = tostring(var.monto)
    }
  }

  dynamic "threshold_rules" {
    for_each = var.umbrales
    content {
      threshold_percent = threshold_rules.value
    }
  }

  all_updates_rule {
    monitoring_notification_channels = [for c in google_monitoring_notification_channel.correo : c.id]
    disable_default_iam_recipients   = false
  }
}
