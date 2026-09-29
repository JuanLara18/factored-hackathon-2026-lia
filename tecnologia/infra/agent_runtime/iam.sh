#!/usr/bin/env bash
# Mínimo privilegio del chat y del agente en Agent Runtime (D-32 fase 2). Lo corre el dueño del proyecto.
# Uso:
#   iam.sh cuenta                              crea la cuenta latam-chat y le da solo lo necesario
#   iam.sh agente <ORG_ID> <ID_DEL_MOTOR>      da al Agent Identity del agente lo que necesita
#   iam.sh quitar-editor                       retira roles/editor de la cuenta de Compute (tras verificar el chat)
set -euo pipefail

PROYECTO="${PROYECTO:-latam-bank-hackaton-2026}"
UBICACION_RUNTIME="${UBICACION_RUNTIME:-us-central1}"
DATASET="latam_bank"
CUENTA="latam-chat@${PROYECTO}.iam.gserviceaccount.com"
NUMERO="$(gcloud projects describe "$PROYECTO" --format='value(projectNumber)')"

# Concede un rol de BigQuery sobre el dataset (no sobre el proyecto).
dataviewer_dataset() {
  bq query --use_legacy_sql=false --location=US \
    "GRANT \`roles/bigquery.dataViewer\` ON SCHEMA \`${PROYECTO}.${DATASET}\` TO \"$1\""
}

cuenta() {
  gcloud iam service-accounts create latam-chat --project "$PROYECTO" \
    --display-name "Chat de disputas (Cloud Run)" || true
  dataviewer_dataset "serviceAccount:${CUENTA}"
  # jobUser: correr consultas; aiplatform.user: llamar al agente de Agent Runtime y a Sessions
  # (incluye aiplatform.reasoningEngines.query) y a los modelos; cloudtrace.agent: enviar trazas.
  for rol in roles/bigquery.jobUser roles/aiplatform.user roles/cloudtrace.agent; do
    gcloud projects add-iam-policy-binding "$PROYECTO" --member "serviceAccount:${CUENTA}" --role "$rol" \
      --condition=None --quiet >/dev/null
  done
  echo "Cuenta lista: ${CUENTA}. Despliegue del chat: just desplegar-chat-run-agente <recurso>"
}

agente() {
  local org="$1" motor="$2"
  local principal="principal://agents.global.org-${org}.system.id.goog/resources/aiplatform/projects/${NUMERO}/locations/${UBICACION_RUNTIME}/reasoningEngines/${motor}"
  dataviewer_dataset "$principal"
  for rol in roles/bigquery.jobUser roles/aiplatform.user roles/cloudtrace.agent \
             roles/serviceusage.serviceUsageConsumer; do
    gcloud projects add-iam-policy-binding "$PROYECTO" --member "$principal" --role "$rol" \
      --condition=None --quiet >/dev/null
  done
  echo "Agent Identity listo: ${principal}"
}

quitar_editor() {
  gcloud projects remove-iam-policy-binding "$PROYECTO" \
    --member "serviceAccount:${NUMERO}-compute@developer.gserviceaccount.com" --role roles/editor
  echo "Si 'gcloud run deploy --source' falla al construir, dar a esa cuenta roles/cloudbuild.builds.builder."
}

case "${1:-}" in
  cuenta) cuenta ;;
  agente) agente "${2:?falta ORG_ID}" "${3:?falta ID_DEL_MOTOR}" ;;
  quitar-editor) quitar_editor ;;
  *) sed -n '2,7p' "$0"; exit 2 ;;
esac
