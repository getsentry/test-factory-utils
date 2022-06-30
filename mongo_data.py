"""
Testing data extraction from MongoDb
"""
import pandas as pd
import pymongo
from utils import get_at
from mongo_const import SDK_REPORT_TEST


def get_collection():
    client = pymongo.MongoClient("localhost", 27017)
    db = client.main
    test_collection = db[SDK_REPORT_TEST]
    return test_collection


def get_version(labels):
    versions = filter(lambda x: x.get("name") == "version", labels)
    versions = list(versions)
    if len(versions) > 0:
        return versions[0].get("value")
    return None


def main():
    sdk_size= get_sdk_size()
    print(sdk_size)


def get_sdk_size():
    sizes = []
    col = get_collection()
    for doc in col.find().sort([("context.argo.creationTimestamp", pymongo.ASCENDING)]):
        labels = get_at(doc, "metadata.labels")
        version = get_version(labels)
        started = get_at(doc, "metadata.commitDate")
        full_val = get_at(doc, "results.measurements.sdk_size.full")
        min_val = get_at(doc, "results.measurements.sdk_size.min")

        sizes.append(get_measurement(version,started, "full", full_val))
        sizes.append(get_measurement(version,started, "min", min_val))
    df = pd.DataFrame(sizes)
    return df


def get_measurement(version, started, measurement, val):
    return {"started": started, "version": version, "measurement": measurement, "value": val}


if __name__ == '__main__':
    main()
