
resource "google_cloudfunctions_function" "bq_gcs_extract" {
  name                = "${var.app_name}-${var.entity}-${var.environment}"
  project             = var.function_project
  region              = var.function_location
  entry_point         = "main"
  runtime             = "python37"
  available_memory_mb = 256
  timeout             = 300

  service_account_email = google_service_account.function.email

  source_archive_bucket = var.source_archive_bucket
  source_archive_object = var.source_archive_object

  event_trigger {
    event_type = "providers/cloud.pubsub/eventTypes/topic.publish"
    resource   = var.input_topic
  }

  labels = {
    app         = var.app_name
    component   = "app"
    entity      = var.entity
    environment = var.environment
  }

  environment_variables = {
    BUCKET       = google_storage_bucket.destination.name
    ENTITY       = var.entity
    ENVIRONMENT  = var.environment
    SENTRY_DSN   = var.sentry_dsn
    OUTPUT_TOPIC = var.output_topic
  }
}

resource "google_service_account" "function" {
  account_id   = "${var.app_name}-${var.entity}-${var.environment}"
  display_name = "${var.app_name} BigQuery to GCS extract function service accouont"
}

# resource "google_project_iam_member" "function_logging" {
#   project = var.function_project
#   role    = "roles/logging.logWriter"
#   member  = "serviceAccount:${google_service_account.function.email}"
# }

resource "google_project_iam_member" "function" {
  project = var.function_project
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.function.email}"
}
