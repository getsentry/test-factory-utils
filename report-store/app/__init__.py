import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask
from flask_mongoengine import MongoEngine

from app.settings import SENTRY_DSN, MONGO_URI


def get_app():
    return app


app = Flask(__name__, static_url_path="/", static_folder="../compiled-ui")

app.config.from_envvar("REPORT_STORE_CONFIG", silent=True)

sentry_sdk.init(
    SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0,
)

app.config["MONGODB_SETTINGS"] = {
    "host": MONGO_URI,
}

db = MongoEngine(app=app)

setattr(app, "db", db)

# Import routes
from app import routes as _
