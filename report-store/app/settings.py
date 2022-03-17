import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/main")
SENTRY_DSN = os.environ.get("SENTRY_DSN")

S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "admin")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "password")
S3_BUCKET = os.environ.get("S3_BUCKET", "my-bucket")
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "localhost:9001")
