terraform {
  required_version = "= 0.13.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "= 3.90.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "= 3.1.0"
    }
  }

  backend "gcs" {
    bucket = "sentry-testing-terraform"
    prefix = "v0.13/sentry-st-testing/iap"
  }
}

provider "google" {
  region  = local.region
  project = local.project
}
