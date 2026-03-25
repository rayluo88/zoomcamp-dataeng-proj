variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "financial-risk-control-system"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "asia-southeast1"
}

variable "bucket_name" {
  description = "GCS data lake bucket name (must be globally unique)"
  type        = string
  default     = "financial-risk-control-system-datalake"
}
