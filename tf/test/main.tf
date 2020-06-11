terraform {
  required_version = ">= 0.12.0"

  required_providers {
    google = "~> 3.20.0"
  }

  backend "gcs" {
    bucket = "global-data-terraform-state"
    # Structure:
    # state/<application>/<entity>/<component>/<environment>
    prefix = "state/gravity/dev/bq-gcs/test"
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
  app_name = "gravity-bq-gcs"

  destination_bucket_name = "gravity-bq-gcs-data"

  data_source = "internal"

  entity      = "dev"
  environment = "test"

  source_archive_bucket = module.artifacts.source_bucket
  source_archive_object = module.artifacts.source_object

  input_topic = google_pubsub_topic.input.name

  sentry_dsn = var.sentry_dsn
}

// PubSub topic to push CSL events to
resource "google_pubsub_topic" "input" {
  name = "gravity-bq-gcs-test-input"

  labels = {
    app         = "gravity-bq-gcs"
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
