# report-store

A web app used for ingesting, searching, and displaying test reports.

## Local environment

* Create a virtualenv, install base (`requirements.txt`) and dev (`requirements-dev.txt`) dependencies.

* Start Mongo server:

        make mongo-server

    To connect to it via Mongo shell, run:

        make mongo-client

* Start the web server:

        make run

## Load test data

Run this command to upload some test data:

    python load_data.py
