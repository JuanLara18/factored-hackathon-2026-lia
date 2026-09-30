# Adopta lo desplegado a mano (Terraform >= 1.5). `terraform plan` debe salir sin cambios
# destructivos antes de cualquier apply; este repositorio no aplica nada por su cuenta.

import {
  to = module.firestore.google_firestore_database.default
  id = "projects/${var.project_id}/databases/(default)"
}

import {
  to = module.chat.google_service_account.chat
  id = "projects/${var.project_id}/serviceAccounts/latam-chat@${var.project_id}.iam.gserviceaccount.com"
}

import {
  to = module.chat.google_storage_bucket.staging
  id = "${var.project_id}/${var.project_id}-staging"
}

import {
  to = module.chat.google_cloud_run_v2_service.chat
  id = "projects/${var.project_id}/locations/${var.region}/services/latam-chat"
}

import {
  to = module.chat.google_cloud_run_v2_service_iam_member.publico
  id = "projects/${var.project_id}/locations/${var.region}/services/latam-chat roles/run.invoker allUsers"
}

import {
  for_each = toset(["roles/bigquery.jobUser", "roles/aiplatform.user", "roles/cloudtrace.agent", "roles/datastore.user"])
  to       = module.chat.google_project_iam_member.chat[each.value]
  id       = "${var.project_id} ${each.value} serviceAccount:latam-chat@${var.project_id}.iam.gserviceaccount.com"
}

import {
  for_each = toset(["latam_bank", "latam_seguridad", "latam_pruebas"])
  to       = module.bigquery.google_bigquery_dataset.d[each.value]
  id       = "projects/${var.project_id}/datasets/${each.value}"
}

# El presupuesto se importa con su id de la cuenta de facturación:
#   gcloud billing budgets list --billing-account=<cuenta>
#   terraform import module.presupuesto.google_billing_budget.presupuesto billingAccounts/<cuenta>/budgets/<id>
