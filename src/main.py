"""Extracts a BQ table to GCS bucket"""

# import os
import base64
import json
import logging
import sys

from os import environ
from time import sleep

from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub_v1

import sentry_sdk

# from google.api_core import retry

APP_NAME = "bq-gcs"
APP_VERSION = "1.0.0"
RELEASE_STRING = "{}@{}".format(APP_NAME, APP_VERSION)

sentry_sdk.init(dsn=environ["SENTRY_DSN"], release=RELEASE_STRING)

LOGGER = logging.getLogger()

BUCKET = environ["BUCKET"]
ENTITY = environ["ENTITY"]
ENVIRONMENT = environ["ENVIRONMENT"]

if "prod" in ENVIRONMENT:
    LOGGER.setLevel(logging.INFO)
else:
    print("Debugging ...")
    LOGGER.setLevel(logging.DEBUG)

# Instantiate client
BQ = bigquery.Client()

LOGGER.info("%s: COLD", RELEASE_STRING)


def get_dataset_ref(data):
    """Return a Bigquery Dataset Reference"""
    return bigquery.DatasetReference(data["project"], data["dataset"])


def get_dataset_location(data):
    """Parse payload for dataset location"""
    # Default BQ location to EU, as that's where we prefer our datasets
    location = "EU"
    # ... but the payload knows best
    if "location" in data:
        location = data["location"]
    return location


def get_destination_uri(data):
    """Returns a parsed destination GCS URI"""
    return "gs://{}/{}/{}.csv".format(BUCKET, data["dataset"], data["table"])


def write_gcs_file(results, filename):
    """Create a file.

    The retry_params specified in the open call will override the default
    retry params for this particular file handle.

    Args:
    filename: filename.
    """
    gcs = storage.Client()

    bucket = gcs.bucket(BUCKET)
    blob = bucket.blob(filename)

    blob.upload_from_string(results)
    LOGGER.info("Created")


def bq_extract_table(data):
    """Perform the BQ to GCS extract job"""
    extract_job = BQ.extract_table(
        get_dataset_ref(data).table(data["table"]),
        get_destination_uri(data),
        # Location must match that of the source table.
        location=get_dataset_location(data),
    )
    results = extract_job.result()  # Waits for job to complete.
    LOGGER.debug(type(results))
    LOGGER.info(results)


def bq_extract_view(data):
    """Perform a manual query against the view, write to GCS blob"""
    query_job = BQ.query("""
    SELECT * FROM `{}.{}.{}`
    """.format(data["project"],
               data["dataset"],
               data["view"]),
                         location=get_dataset_location(data))
    results = query_job.result()  # Waits for job to complete.
    LOGGER.debug(type(results))
    LOGGER.info(results)
    write_gcs_file(results, get_destination_uri(data))


def get_callback(api_future, data, ref):
    """Wrap message data in the context of the callback function."""

    def callback(api_future):
        try:
            print(
                "Published message {} now has message ID {}".format(
                    data, api_future.result()
                )
            )
            ref["num_messages"] += 1
        except Exception:
            print(
                "A problem occurred when publishing {}: {}\n".format(
                    data, api_future.exception()
                )
            )
            raise

    return callback


def pub(data):
    """Publishes a message to a Pub/Sub topic."""

    # Exit early if output topic is not set
    if not environ["OUTPUT_TOPIC"]:
        return 'ok'

    # Initialize a Publisher client.
    client = pubsub_v1.PublisherClient()

    # Keep track of the number of published messages.
    ref = dict({"num_messages": 0})
    message = json.dumps({
        "entity": environ["ENTITY"],
        "component": "generic",
        "environment": "test",
        "event": "bq.table.updated",
        "info": "Some helpful descriptive text",
        "bq": {
            "dataset": "samples",
            "project": "bigquery-public-data",
            "table": "shakespeare"
        }
    })
    # When you publish a message, the client returns a future.
    api_future = client.publish(
        environ["OUTPUT_TOPIC"],
        data=message.encode('utf-8')
    )
    api_future.add_done_callback(get_callback(api_future, message, ref))

    # Keep the main thread from exiting while the message future
    # gets resolved in the background.
    while api_future.running():
        sleep(0.5)
        print("Published {} message(s).".format(ref["num_messages"]))


def handler(event):
    """Parses event payload, extracts data from BigQuery table, writes to GCS"""
    json_data = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(json_data)

    if "table" in data:
        bq_extract_table(data)
        pub(data)
        return 'ok'

    if "view" in data:
        bq_extract_view(data)
        pub(data)
        return 'ok'

    raise Exception("Invalid payload: no 'view' or 'table' field in payload")


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
        LOGGER.debug("%s: HOT START", RELEASE_STRING)
        handler(event)
        sleep(1)
    except Exception:
        for error in sys.exc_info():
            LOGGER.error("%s", error)
        LOGGER.debug(event)
        LOGGER.debug(context)
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
