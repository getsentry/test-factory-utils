"""
This script copies production data into the local mongo db instance
It copies the production data using the mongodb production database

In order to access the production mongodb you need to proxy into it

     kubectl port-forward service/mongodb-report-store 27000:27017

Then you can connect to the remote mongodb at 27000 and to the local mongodb at 27017

"""
import jmespath

from mongo_const import REPORT_COLLECTION, SDK_REPORT_COLLECTION
from pymongo import MongoClient
from collections import namedtuple

REMOTE_PORT = 27000

#Paths = namedtuple('paths', ["test_name", "display_name", "base_test"])


def get_test_path() :
    test_name = "metadata.labels[?name=='test_name'].value|[0]"
    tn = jmespath.compile(test_name)
    # display_name = "metadata.labels[?name=='displayName'].value|[0]"
    # dn = jmespath.compile(display_name)
    # base_test = "metadata.labels[?name=='baseTest'].value|[0]"
    # bt = jmespath.compile(base_test)
    # return Paths(test_name=tn, display_name=dn, base_test=bt)
    return tn

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

        i = 0
        for doc in remote_collection.find():
            if (i + 1) % 100 == 0:
                print(f"Copy doc {i + 1}")
            del doc["_id"]
            del doc["raw"]
            #set_javascript_sdk_fields_additional_info(doc)
            local_collection.insert_one(doc)
            i += 1


def set_javascript_sdk_fields_additional_info(doc):
    tn_path = get_test_path()
    test_name = tn_path.search(doc)

    labels = doc.get("metadata", {}).get("labels", None)

    if labels is not None:
        if test_name == "test-run-node-app-test.sh":
            labels.append({"name": "displayName", "value": "Instrumented"})
            labels.append({"name": "baseTest", "value": "false"})
        elif test_name == "test-run-node-app-baseline.sh":
            labels.append({"name": "displayName", "value": "Base"})
            labels.append({"name": "baseTest", "value": "true"})



if __name__ == "__main__":
    main()
