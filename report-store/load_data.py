#!/usr/bin/env python3
import json
import glob
import sys

import requests

SERVER_ENDPOINT = "http://127.0.0.1:5000/api/report"


def process_file(name):
    print(f">>> Processing file: {name}...")
    with open(name) as f:
        raw = json.load(f)

    name = raw["metadata"]["name"]
    obj = {
        "apiVersion": "0.1",
        "metadata": {},
        "name": name,
        "raw": raw,
        "results": {},
    }

    print("Sending to the server...")

    server_endpoint = SERVER_ENDPOINT
    result = requests.post(server_endpoint, json=obj)
    result.raise_for_status()
    print(result)
    print("Response text:", result.text)


def load_data_from_prod(prod_uri, local_uri):
    resp = requests.get(f"{prod_uri}/api/reports")

    if not resp.ok:
        print("Failed to get requests from prod server")
        sys.exit(1)

    docs = resp.json()

    for doc in docs:
        result = requests.post(f"{local_uri}/api/report", json=doc)
        del doc["_id"]
        if resp.ok:
            print(f"doc with name: {doc['name']}")
        else:
            print(f"ERROR upserting doc with name: {doc['name']}")


def main():
    data_files = glob.glob("data/*.json")

    for file in data_files:
        process_file(file)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--prod":
        # to load data from the server you need to first get a proxy that is not auth protected to the server
        #  something like:
        # kubectl port-forward service/report-store 8087:80
        load_data_from_prod(
            prod_uri="http://localhost:8087", local_uri="http://127.0.0.1:5001"
        )
    else:
        main()
