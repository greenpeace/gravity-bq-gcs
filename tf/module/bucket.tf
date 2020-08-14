
resource "google_storage_bucket" "destination" {
  name     = var.destination_bucket_name
  location = var.destination_bucket_location
  project  = var.destination_bucket_project

  # For uniform bucket ACL
  bucket_policy_only = true

  # Enable force-deletion if the bucket is not empty
  force_destroy = true

  lifecycle_rule {
    condition {
      age = var.lifecycle_rule_delete_age
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    app         = var.app_name
    component   = "data"
    lifecycle   = var.data_lifecycle
    source      = var.data_source
    environment = var.environment
    entity      = var.entity
  }
}

resource "google_storage_bucket_iam_member" "destination" {
  bucket = google_storage_bucket.destination.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.function.email}"
}
