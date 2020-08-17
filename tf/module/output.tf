output "service_account_email" {
  value = google_service_account.function.email
}

output "bucket" {
  value = google_storage_bucket.destination.name
}

output "input_topic" {
  value = var.input_topic
}

output "output_topic" {
  value = var.output_topic
}
