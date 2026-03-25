output "datalake_bucket" {
  description = "GCS data lake bucket name"
  value       = google_storage_bucket.datalake.name
}

output "pipeline_sa_email" {
  description = "Service account email for pipeline tools"
  value       = google_service_account.pipeline.email
}

output "pipeline_key_path" {
  description = "Local path to service account key (for Airflow/dbt)"
  value       = local_sensitive_file.pipeline_key.filename
  sensitive   = true
}
