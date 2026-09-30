# R-TEC-18: el presupuesto es lo primero. Sin reglas de notificación propias: llegan los correos
# por defecto a los administradores de la cuenta de facturación (lo que hay desplegado).
resource "google_billing_budget" "presupuesto" {
  billing_account = var.billing_account
  display_name    = var.nombre

  budget_filter {
    projects               = ["projects/${var.project_number}"]
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
    calendar_period        = "MONTH"
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
      spend_basis       = "CURRENT_SPEND"
    }
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }
}
