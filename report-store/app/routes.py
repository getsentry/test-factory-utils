import datetime
import tarfile
from io import BytesIO

from flask import request, jsonify, redirect, send_file
from minio import Minio

from app import app
from app.models import Report, MetadataTree, NameValuePair, ResultsTree
from app.settings import S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY, S3_BUCKET

client = Minio(
    S3_ENDPOINT, access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY, secure=False
)


@app.route("/")
def root():
    return redirect("/ui/")


@app.route("/ui/", defaults={"path": ""})
@app.route("/ui/<path:path>")
def the_app(path):
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

    report.apiVersion = content.get("apiVersion", "unknown")
    report.raw = content.get("raw")

    ### Fill metadata
    report.metadata.timeUpdated = now
    metadata_raw = content.get("metadata", {})
    labels_raw = metadata_raw.get("labels", [])
    labels_map = dict()
    # Deduplicate and sanitize labels first
    for label_entry in labels_raw:
        name, value = label_entry.get("name", ""), label_entry.get("value", "")
        if not name:
            continue
        if not value:
            value = ""
        labels_map[str(name)] = str(value)
    # Add to the object
    report.metadata.labels = [
        NameValuePair(name=key, value=value) for key, value in labels_map.items()
    ]

    ### Fill results
    results_raw = content.get("results", {})
    report.results = ResultsTree.from_dict(results_raw)

    ### Fill context
    report.context = content.get("context")

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

    include_full = args.get("full", "0").lower() in {"1", "true", "yes"}
    if not include_full:
        queryset = queryset.exclude("raw")

    page = int(args.get("page", 1))
    # The limit is quite big because mostly we're doing client side pagination
    # at the moment.
    limit = int(args.get("limit", 100))

    results = (
        queryset.order_by("-metadata.timeCreated")
        .paginate(page=page, per_page=limit)
        .items
    )

    # HACK: sort to have newest first, but if the reports are "close enough" (meaning that reports are produces
    # by the same Argo workflow) -- then sort by name.
    results = sorted(
        results,
        key=lambda report: (-int(report.metadata.timeCreated.timestamp()), report.name),
    )

    return jsonify(results)


@app.route("/api/artifact/<report_id>/<artifact_id>", methods=["GET"])
def get_artifact(report_id, artifact_id):
    """
    Return an uncompressed artifact.
    """

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
    response_bytes = BytesIO(res.read())
    res.close()
    res.release_conn()

    with tarfile.open(fileobj=response_bytes, mode="r:gz") as tar:
        members = tar.getmembers()

        # FIXME we don't support compressed directories at the moment
        if len(members) != 1:
            return "only single file artifacts are supported\n", 400

        compressed_file = members[0]

        data = tar.extractfile(compressed_file).read().decode("utf8")
        file_name = compressed_file.name

    result = {
        "data": data,
        "artifact_id": artifact_id,
        "bucket_key": bucket_key,
        "basename": file_name,
    }

    return jsonify(result)
