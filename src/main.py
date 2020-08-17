"""Extracts a BQ table to GCS bucket"""

# import os
import base64
import json
import logging
import sys
import traceback

from os import environ
from time import sleep

# from google.cloud import storage
from google.cloud import bigquery
from google.cloud import pubsub_v1

import sentry_sdk

# from google.api_core import retry

APP_NAME = "bq-gcs"
APP_VERSION = "1.1.0"
RELEASE_STRING = "{}@{}".format(APP_NAME, APP_VERSION)

sentry_sdk.init(dsn=environ["SENTRY_DSN"], release=RELEASE_STRING)

BUCKET = environ["BUCKET"]
ENTITY = environ["ENTITY"]

if "prod" in environ["ENVIRONMENT"]:
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO
    )
else:
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG
    )

logging.info("%s: COLD", RELEASE_STRING)

# Instantiate client
BQ = bigquery.Client()


def get_dataset_ref(bq):
    """Return a Bigquery Dataset Reference"""
    return bigquery.DatasetReference(bq["project"], bq["dataset"])


def get_dataset_location(bq):
    """Parse payload for dataset location"""
    # Default BQ location to EU, as that's where we prefer our datasets
    location = "EU"
    # ... but the payload knows best
    if "location" in bq:
        location = bq["location"]
    return location


def get_destination_object(bq):
    """Returns a parsed destination GCS URI"""
    return "{}/{}.csv".format(bq["dataset"], bq["table"])


def get_destination_uri(bq):
    """Returns a parsed destination GCS URI"""
    return "gs://{}/{}".format(BUCKET, get_destination_object(bq))


# def write_gcs_file(results, filename):
#     """Create a file.
#
#     The retry_params specified in the open call will override the default
#     retry params for this particular file handle.
#
#     Args:
#     filename: filename.
#     """
#     gcs = storage.Client()
#
#     bucket = gcs.bucket(BUCKET)
#     blob = bucket.blob(filename)
#
#     blob.upload_from_string(results)
#     logging.info("Created")


# def bq_extract_view(bq):
#     """Perform a manual query against the view, write to GCS blob"""
#     query_job = BQ.query("""
#     SELECT * FROM `{}.{}.{}`
#     """.format(
#         bq["project"],
#         bq["dataset"],
#         bq["view"]),
#         location=get_dataset_location(bq)
#     )
#     results = query_job.result()  # Waits for job to complete.
#     logging.debug(type(results))
#     logging.info(results)
#     write_gcs_file(results, get_destination_uri(bq))


def bq_extract_table(bq):
    """Perform the BQ to GCS extract job"""
    extract_job = BQ.extract_table(
        get_dataset_ref(bq).table(bq["table"]),
        get_destination_uri(bq),
        # Location must match that of the source table.
        location=get_dataset_location(bq),
    )
    results = extract_job.result()  # Waits for job to complete.
    pub(results._properties) # <google.cloud.bigquery.job.ExtractJob>


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


def pub(result):
    """Publishes a message to a Pub/Sub topic."""

    # Exit early if output topic is not set
    if not environ["OUTPUT_TOPIC"]:
        logging.info("Skip PubSub, OUTPUT_TOPIC is blank")
        return 'ok'

    info = "BigQuery extract complete in {}ms: {}.{}.{} => {}".format(
        result["statistics"]["totalSlotMs"],
        result["configuration"]["extract"]["sourceTable"]["projectId"],
        result["configuration"]["extract"]["sourceTable"]["datasetId"],
        result["configuration"]["extract"]["sourceTable"]["tableId"],
        ",".join(result["configuration"]["extract"]["destinationUris"])
    )

    logging.info("%s", info)

    message = json.dumps({
        "entity": environ["ENTITY"],
        "environment": environ["ENVIRONMENT"],
        "event": "bq.extract.complete",
        "info": info,
        "result": result
    })

    # Keep track of the number of published messages.
    ref = dict({"num_messages": 0})

    # Initialize a Publisher client.
    client = pubsub_v1.PublisherClient()

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
    """Parses event payload, extract data from BigQuery table, write to GCS"""
    json_data = base64.b64decode(event["data"]).decode("utf-8")
    data = json.loads(json_data)

    if "bq" not in data:
        raise Exception("Invalid payload: no 'bq' field in payload", data)

    if "table" in data["bq"]:
        bq_extract_table(data["bq"])
        return 'ok'

    if "view" in data["bq"]:
        raise Exception("Extracts from BigQuery views not implemented.")
        # bq_extract_view(data["bq"])
        # pub(data["bq"])
        # return 'ok'

    raise Exception(
        "Invalid payload: no 'view' or 'table' field in payload",
        data
    )


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
        logging.debug("%s: HOT START", RELEASE_STRING)
        handler(event)
    except Exception:
        for error in sys.exc_info():
            logging.error("%s", error)
        traceback.print_exc(file=sys.stderr)
        logging.error(event)
        logging.error(context)
        sleep(1)
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
