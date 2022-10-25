import importlib

import click
from google.cloud import storage
from mongo_data import get_db, get_docs, get_measurements


@click.command()
@click.option(
    "--mongo-db",
    "-m",
    "mongo_url",
    envvar="MONGO_DB",
    required=True,
    help="url of mongo db (something like: 'mongodb://mongo-server/27017')",
)
@click.option(
    "--gcs-bucket-name",
    "-b",
    "bucket_name",
    envvar="GCS_BUCKET_NAME",
    default="sentry-testing-bucket-test-sdk-reports",
    help="GCS bucket name for saving the report",
)
@click.option(
    "--report-name",
    "-n",
    envvar="REPORT_NAME",
    default="report.html",
    help="path to the name of the report file",
)
@click.option("--filters", "-f", multiple=True, type=(str, str))
@click.option(
    "--git-sha",
    "-s",
    envvar="REFERENCE_SHA",
    required=True,
    help="the git sha of the version of interest",
)
@click.option(
    "--no-upload", is_flag=True, help="if passed will not upload the report to GCS"
)
@click.option(
    "--report",
    "-r",
    "report_file_name",
    required=True,
    help="report generator python file",
)
def main(mongo_url, bucket_name, report_name, filters, git_sha, no_upload, report_file_name):
    db = get_db(mongo_url)

    trend_filters = [*filters, ("is_default_branch", "1")]
    current_filters = [*filters, ("commit_sha", git_sha)]

    trend_docs = get_docs(db, trend_filters)
    current_docs = get_docs(db, current_filters)

    # we only need the last doc
    if len(current_docs) == 0:
        current_doc = None
    else:
        current_doc = current_docs[-1]

    measurements = get_measurements(current_docs)

    module = importlib.import_module(report_file_name)
    module.generate_report(report_name, trend_docs, current_doc, measurements, filters, git_sha)

    if not no_upload:
        upload_to_gcs(report_name, filters, bucket_name, module.get_report_file_name)


def upload_to_gcs(file_name, filters, bucket_name, get_report_file_name):
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob_file_name = get_report_file_name(filters)
    blob = bucket.blob(blob_file_name)

    with open(file_name, "rb") as my_file:
        blob.upload_from_file(my_file, content_type="text/html")
    print(
        f"Uploaded to GCS at: https://storage.cloud.google.com/{bucket_name}/{blob_file_name}"
    )

if __name__ == "__main__":
    main()
