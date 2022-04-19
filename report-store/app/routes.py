import datetime
import os
import tarfile

from flask import request, jsonify, redirect, send_from_directory, send_file
from minio import Minio

from app import app
from app.models import Report, MetadataTree

from app.settings import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET

client = Minio(
    S3_ENDPOINT, access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY, secure=False
)


@app.route("/", methods=["GET"])
def the_app():
    return send_file("../compiled-ui/index.html")


@app.route("/healthz", methods=["GET"])
def healthcheck():
    return "ok\n"


@app.route("/api/report", methods=["POST"])
def store_report():
    print(request)
    print(request.headers)

    content = request.get_json()
    if not content:
        return "invalid data: empty object\n", 400

    name = content.get("name")
    if not name:
        return "invalid data: no name field\n", 400

    # Do an upsert
    # TODO: any better way to do it?
    report = Report.objects(name=name).first()
    response_str = "updated\n"
    now = datetime.datetime.utcnow()
    if not report:
        report = Report(name=name, metadata=MetadataTree(timeCreated=now))
        response_str = "added\n"

    report.metadata.timeUpdated = now
    report.apiVersion = content.get("apiVersion", "unknown")
    report.raw = content.get("raw")
    report.context = content.get("context")
    report.results = content.get("results")

    report.save()

    return response_str


@app.route("/api/report/<report_id>", methods=["GET"])
def get_report(report_id):
    report = Report.objects.get_or_404(name=report_id)
    return jsonify(report.to_dict())


@app.route("/api/reports", methods=["GET"])
def get_report_list():
    args = request.args
    search_query = args.get("search")

    queryset = Report.objects
    if search_query:
        # Do the filtering
        pass

    page = int(args.get("page", 1))
    limit = int(args.get("limit", 10))

    results = queryset.paginate(page=page, per_page=limit).items

    return jsonify(results)


@app.route("/api/artifact/<report_id>/<artifact_id>", methods=["GET"])
def get_artifact(report_id, artifact_id):

    # TODO memoize
    report = Report.objects.get_or_404(name=report_id)

    artifact_list = list(
        report.raw.get("status", {}).get("outputs", {}).get("artifacts", [])
    )

    entry = list(filter(lambda x: x["name"] == artifact_id, artifact_list))

    if not entry:
        return "Artifact not found\n", 404

    bucket_key = entry[0]["s3"]["key"]

    # TODO memoize (bucket_key is globally unique)
    res = client.get_object(S3_BUCKET, bucket_key)

    tar = tarfile.open(fileobj=res)
    members = tar.getmembers()

    # FIXME we don't support compressed directories at the moment
    assert len(members) == 1

    data = tar.extractfile(members[0]).read().decode("utf8")

    result = {
        "data": data,
        "artifact_id": artifact_id,
        "bucket_key": bucket_key,
        "basename": os.path.basename(bucket_key),
    }

    return jsonify(result)
