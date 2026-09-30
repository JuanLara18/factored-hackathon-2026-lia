terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Sin backend remoto: no existe un bucket de estado. El estado es local (ignorado por git) y
  # importar.tf adopta lo desplegado a mano. Para un equipo, crear un bucket con versionado y
  # añadir backend "gcs".
}

provider "google" {
  project = var.project_id
  region  = var.region
}
