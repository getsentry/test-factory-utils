#!/usr/bin/env python3
import json
import glob

import requests

SERVER_ENDPOINT = "http://127.0.0.1:5050/api/report"


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


def main():

    data_files = glob.glob("data/*.json")

    for file in data_files:
        process_file(file)


if __name__ == "__main__":
    main()
