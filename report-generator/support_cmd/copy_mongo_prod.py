"""
This script copies production data into the local mongo db instance
It copies the production data using the mongodb production database

In order to access the production mongodb you need to proxy into it

     kubectl port-forward service/mongodb-report-store 27000:27017

Then you can connect to the remote mongodb at 27000 and to the local mongodb at 27017

"""
from pymongo import MongoClient
from mongo_const import SDK_REPORT_COLLECTION, REPORT_COLLECTION
REMOTE_PORT = 27000


def main():
    local_client = MongoClient("localhost", 27017)
    local_db = local_client.main
    remote_client = MongoClient("localhost", REMOTE_PORT)
    remote_db = remote_client.main

    for collection in [SDK_REPORT_COLLECTION, REPORT_COLLECTION]:
        print("copying collection:", collection)
        # clear previous content
        local_db.drop_collection(collection)
        local_collection = local_db[collection]
        remote_collection = remote_db[collection]

        for doc in remote_collection.find():
            local_collection.insert_one(doc)


if __name__ == '__main__':
    main()

