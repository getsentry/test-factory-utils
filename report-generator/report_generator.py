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
@click.option(
    "--filters",
    "-f", multiple=True,
    type=(str, str),
    help="(labelName,labelValue) pairs to use as filter, will the labels present in `metadata.labels` "
)
@click.option(
    "--git-sha",
    "-s",
    envvar="REFERENCE_SHA",
    required=True,
    help="the git sha of the version of interest, (OBSOLETE) use -c git-sha option for newer implementations",
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
@click.option(
    "--custom",
    "-c",
    multiple=True,
    type=(str, str),
    help="report specific (name,value) parameters. The specific report deals with them appropriately"
)
def main(mongo_url, bucket_name, report_name, filters, git_sha, no_upload, report_file_name, custom):
    db = get_db(mongo_url)

    filters_dict = {k: v for (k, v) in filters}

    custom_options_dict = {k: v for (k, v) in custom}
    if git_sha is not None:
        custom_options_dict["git-sha"] = git_sha

    module = importlib.import_module(report_file_name)
    module.generate_report(db, report_name, filters_dict, custom_options_dict)

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
