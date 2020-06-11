output "source_bucket" {
  value = google_storage_bucket.source_bucket.name
}
output "source_object" {
  value = google_storage_bucket_object.source_file.name
}
