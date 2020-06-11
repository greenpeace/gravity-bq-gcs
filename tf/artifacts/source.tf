
resource "google_storage_bucket" "source_bucket" {
  name          = "bq-gcs-source"
  location      = "EU"
  project       = "global-data-resources"
  force_destroy = "true"

  labels = {
    app       = "bq-gcs"
    component = "source"
  }
}

data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "${path.module}/../../src"
  output_path = "build/bq-gcs.zip"
  excludes    = ["tests", "__pycache__", "Makefile"]
}

resource "google_storage_bucket_object" "source_file" {
  name   = "bq-gcs-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.source_bucket.name
  source = data.archive_file.function_source.output_path
}
