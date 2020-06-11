variable "app_name" {
  description = "Unique identifier for this module instance"
}

variable "data_source" {
  description = "Origin system from which the data is sourced"
}

variable "environment" {
  default     = "production"
  description = "Module deployment environment: dev, stage, prod"
}

variable "entity" {
  description = "Business unit which owns this data"
}


# FUNCTION

variable "function_project" {
  default = "global-data-resources"
}

variable "function_location" {
  default     = "europe-west1"
  description = "Location in which to execute cloud functions"
}

variable "sentry_dsn" {
  description = "sentry.greenpeace.org DSN identifier"
}

variable "input_topic" {
  description = "PubSub topic which triggers this function"
}

variable "source_archive_bucket" {
  description = "GCS bucket containing function source"
}

variable "source_archive_object" {
  description = "Path and filename of function source in GCS bucket"
}


# BUCKET

variable "destination_bucket_name" {
  description = "GCS Bucket name to which we write the CSV export"
}

variable "destination_bucket_location" {
  default = "EU"
}

variable "destination_bucket_project" {
  default = "global-data-resources"
}

variable "data_lifecycle" {
  default     = "raw"
  description = "State of data: raw, sensitive, pii, non_pii"
}

variable "lifecycle_rule_delete_age" {
  default     = "7"
  description = "Files older than this in days are deleted"
}
