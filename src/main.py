"""Extracts a BQ table to GCS bucket"""

# import os
import base64
import json
import logging
import sys

import sentry_sdk

from google.cloud import storage
from google.cloud import bigquery

from os import environ
from time import sleep

# from google.api_core import retry

APP_NAME = "bq-gcs"
APP_VERSION = "1.0.0"
RELEASE_STRING = "%s@%s" % (APP_NAME, APP_VERSION)

sentry_sdk.init(dsn=environ["SENTRY_DSN"], release=RELEASE_STRING)

LOGGER = logging.getLogger()

ENVIRONMENT = environ["ENVIRONMENT"]
BUCKET = environ["BUCKET"]

if "prod" in ENVIRONMENT:
    LOGGER.setLevel(logging.INFO)
else:
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.debug("Debug mode enabled")

LOGGER.info("%s", RELEASE_STRING)

# Instantiates clients
CS = storage.Client()
BQ = bigquery.Client()


def handler(event, context):
    """Parses event payload, extracts data from BigQuery table, writes to GCS"""
    json_data = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(json_data)

    # Default BQ location to EU, as that's where we prefer our datasets
    location = "EU"

    # ... but the payload knows best
    if "location" in data:
        location = data["location"]

    # # Default to environment, but allow override in payload?
    # bucket = BUCKET
    # if "bucket" in data:
    #     bucket = data["bucket"]

    destination_uri = "gs://{}/{}/{}.csv".format(BUCKET, data["dataset"], data["table"])
    dataset_ref = bigquery.DatasetReference(data["project"], data["dataset"])
    table_ref = dataset_ref.table(data["table"])

    extract_job = BQ.extract_table(
        table_ref,
        destination_uri,
        # Location must match that of the source table.
        location=location,
    )  # API request
    extract_job.result()  # Waits for job to complete.

    LOGGER.debug(extract_job)


def main(event, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """
    try:
        handler(event, context)
        sleep(1)
    except:
        for error in sys.exc_info():
            LOGGER.error("%s", error)
        sleep(5)
        raise

# @todo: implement deadletter topic

# SOURCE_PROJECT = os.getenv("SOURCE_PROJECT")
# SOURCE_DATASET = os.getenv("SOURCE_DATASET")
# SOURCE_TABLE = os.getenv("SOURCE_TABLE")
#
# DESTINATION_PROJECT = os.getenv("DESTINATION_PROJECT")
# DESTINATION_BUCKET = os.getenv("DESTINATION_BUCKET")

# ERROR_TOPIC = "projects/%s/topics/quarantine_error_%s" % (DESTINATION_PROJECT, APP_NAME)
# SUCCESS_TOPIC = "projects/%s/topics/quarantine_success_%s" % (
#     DESTINATION_PROJECT,
#     APP_NAME,
# )

# project = "bigquery-public-data"
# dataset_id = "samples"
# table_id = "shakespeare"
#
# bucket_name = "gpi-data-test"
