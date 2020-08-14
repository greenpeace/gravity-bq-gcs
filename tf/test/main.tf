terraform {
  required_version = ">= 0.12.0"

  required_providers {
    google = "~> 3.33.0"
  }

  backend "gcs" {
    bucket = "global-data-terraform-state"
    # Structure:
    # state/<application>/<entity>/<component>/<environment>
    prefix = "state/cosmos/dev/bq-gcs/test"
  }
}

provider "google" {
  project = "global-data-resources"
  region  = "EU"
}

module "artifacts" {
  source = "../artifacts/"
}

module "example" {
  source   = "../module/"
  app_name = "cosmos-bq-gcs"

  destination_bucket_name = "cosmos-bq-gcs-dev-test-data"

  data_source = "internal"

  entity      = "dev"
  environment = "test"

  source_archive_bucket = module.artifacts.source_bucket
  source_archive_object = module.artifacts.source_object

  input_topic  = google_pubsub_topic.input.id
  output_topic = google_pubsub_topic.output.id

  sentry_dsn = var.sentry_dsn
}

resource "google_pubsub_topic" "input" {
  name = "cosmos-bq-gcs-dev-test-input"

  labels = {
    app         = "cosmos-bq-gcs"
    entity      = "dev"
    environment = "test"
  }
}

resource "google_pubsub_topic" "output" {
  name = "cosmos-bq-gcs-dev-test-output"

  labels = {
    app         = "cosmos-bq-gcs"
    entity      = "dev"
    environment = "test"
  }
}

resource "google_pubsub_topic_iam_member" "subscriber" {
  project = "global-data-resources"
  topic   = google_pubsub_topic.input.name
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${module.example.service_account_email}"
}

output "input_topic" {
  value = google_pubsub_topic.input.name
}

output "output_topic" {
  value = google_pubsub_topic.output.name
}
