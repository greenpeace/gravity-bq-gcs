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

locals {
  project = "global-data-resources"
}

provider "google" {
  alias = "initial"
}

data "google_client_config" "config-default" {
  provider = google.initial
}

data "google_service_account_access_token" "default" {
  provider               = google.initial
  target_service_account = "terraform@${local.project}.iam.gserviceaccount.com"
  scopes                 = ["cloud-platform"]
  lifetime               = "300s"
}

provider "google" {
  project      = local.project
  region       = "EU"
  access_token = data.google_service_account_access_token.default.access_token
}

module "artifacts" {
  source = "../artifacts/"
}

module "example" {
  source   = "../module/"
  app_name = "cosmos-bq-gcs"

  data_source = "internal"

  entity      = "dev"
  environment = "test"

  source_archive_bucket = module.artifacts.source_bucket
  source_archive_object = module.artifacts.source_object

  input_topic  = google_pubsub_topic.input.id
  output_topic = google_pubsub_topic.output.id
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
  project = local.project
  topic   = google_pubsub_topic.input.id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${module.example.service_account_email}"
}

resource "google_pubsub_topic_iam_member" "publisher" {
  project = local.project
  topic   = google_pubsub_topic.output.id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${module.example.service_account_email}"
}

output "input_topic" {
  value = google_pubsub_topic.input.name
}

output "output_topic" {
  value = google_pubsub_topic.output.name
}
