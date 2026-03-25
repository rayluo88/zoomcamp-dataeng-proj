terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state backend — keeps tfstate in GCS instead of local disk
  backend "gcs" {
    bucket = "financial-risk-control-system-datalake"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Data Lake ──────────────────────────────────────────────────────────────────

resource "google_storage_bucket" "datalake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = false

  # Prevent accidental public exposure
  public_access_prevention = "enforced"

  # Clean up incomplete multipart uploads after 1 day
  lifecycle_rule {
    condition { age = 1 }
    action { type = "AbortIncompleteMultipartUpload" }
  }

  # Auto-archive old raw data to cheaper storage after 90 days
  lifecycle_rule {
    condition {
      age                = 90
      matches_prefix     = ["raw/"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# ── BigQuery ───────────────────────────────────────────────────────────────────

resource "google_bigquery_dataset" "raw" {
  dataset_id  = "raw"
  description = "Landing zone — raw data loaded directly from GCS"
  location    = var.region
}

resource "google_bigquery_dataset" "staging" {
  dataset_id  = "staging"
  description = "Cleaned and typed data, not yet transformed"
  location    = var.region
}

resource "google_bigquery_dataset" "production" {
  dataset_id  = "production"
  description = "dbt-transformed models consumed by the dashboard"
  location    = var.region
}

# ── Service Account ────────────────────────────────────────────────────────────

resource "google_service_account" "pipeline" {
  account_id   = "risk-pipeline"
  display_name = "Risk Control Pipeline"
  description  = "Used by Airflow, Spark, and dbt to access GCP resources"
}

resource "google_project_iam_member" "pipeline_gcs" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bq_job" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# Service account key — downloaded locally for Airflow/dbt to authenticate
resource "google_service_account_key" "pipeline" {
  service_account_id = google_service_account.pipeline.name
}

resource "local_sensitive_file" "pipeline_key" {
  content  = base64decode(google_service_account_key.pipeline.private_key)
  filename = "${path.module}/../credentials/pipeline-sa-key.json"
}
