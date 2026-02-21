variable "project" {
  type        = string
  description = "Google Cloud project ID"
  nullable    = true
  default     = null
}

variable "location" {
  description = "Google Cloud location (Compute region)"
  type        = string
  nullable    = true
  default     = null
}

variable "agent_name" {
  type        = string
  description = "Agent name to identify cloud resources and logs"
  nullable    = true
  default     = null
}

variable "otel_instrumentation_genai_capture_message_content" {
  description = "Capture LLM message content in OpenTelemetry traces (TRUE/FALSE)"
  type        = string
  nullable    = true
  default     = null
}

variable "repository_name" {
  description = "GitHub repository name"
  type        = string
}

variable "repository_owner" {
  description = "GitHub repository owner - username or organization"
  type        = string
}

# Cross-project Artifact Registry promotion (optional — only used in stage/prod bootstraps)
variable "promotion_source_project" {
  description = "Source GCP project for image promotion (dev→stage or stage→prod). Set to null for dev."
  type        = string
  nullable    = true
  default     = null
}

variable "promotion_source_artifact_registry_name" {
  description = "Source Artifact Registry name for image promotion. Set to null for dev."
  type        = string
  nullable    = true
  default     = null
}

# Registry cleanup policy configuration
variable "registry_cleanup_general_retention_days" {
  description = "Number of days before tagged images are deleted (e.g., 30 for dev, 365 for prod). Set to null to disable."
  type        = number
  nullable    = true
  default     = 30
}

variable "registry_cleanup_keep_count" {
  description = "Number of most-recent image versions to keep. Set to null to disable the keep-recent-versions policy."
  type        = number
  nullable    = true
  default     = 5
}

variable "registry_cleanup_pr_retention_days" {
  description = "Number of days before PR-tagged images are deleted. Set to null to disable (e.g., prod)."
  type        = number
  nullable    = true
  default     = 7
}
