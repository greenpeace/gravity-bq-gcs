# BigQuery to GCS extract module

This module describes a Google Cloud Function and support resources which is triggered by a pubsub topic,
extracts the contents of the BQ table as specified in the topic payload, and
writes the resultant CSV(s) to a GCS object.

## Usage

See tf/test folder for example usage

## Development Requirements

1. terraform >= 0.12.0
2. gcloud
3. python
4. make
