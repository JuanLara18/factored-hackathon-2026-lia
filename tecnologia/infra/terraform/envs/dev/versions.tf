terraform {
  required_version = "~> 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Bucket creado en el arranque manual (ARRANQUE.md). Se pasa con:
  #   terraform init -backend-config="bucket=<bucket>"
  backend "gcs" {
    prefix = "dev"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
