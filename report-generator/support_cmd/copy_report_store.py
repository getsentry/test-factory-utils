"""
This script copies production data into the local mongo db instance
It copies the production data using the report-store endpoint

In order to access the report-store endpoint you need to proxy into it

     kubectl port-forward service/report-store 5000:80

after that you can get the two collections by calling the /api/reports endpoint
specifying type=regular or type=sdk

localhost:5000/api/reports?type=regular
localhost:5000/api/reports?type=sdk

This will return a list of documents that can be inserted in the local mongodb

"""
import requests
from mongo_const import REPORT_COLLECTION, SDK_REPORT_COLLECTION, URL
from pymongo import MongoClient
from utils import del_at


def main():
    client = MongoClient("localhost", 27017)
    db = client.main

    resp = requests.get(f"{URL}/api/reports?type=regular")

    if resp.status_code != 200:
        print("Could not access reports server")

    docs = resp.json()
    # clear previous content
    db.drop_collection(REPORT_COLLECTION)
    add_docs(db[REPORT_COLLECTION], docs)

    resp = requests.get(f"{URL}/api/reports?type=sdk")

    if resp.status_code != 200:
        print("Could not access reports server")

    docs = resp.json()
    db.drop_collection(SDK_REPORT_COLLECTION)
    add_docs(db[SDK_REPORT_COLLECTION], docs)


def add_docs(collection, docs):
    print(f"handling {len(docs)} documents.")
    for doc in docs:
        del_at(doc, "_id")

    collection.insert_many(docs)


if __name__ == "__main__":
    main()
