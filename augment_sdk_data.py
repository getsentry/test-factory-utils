import random
import datetime
from copy import deepcopy

import pymongo

from utils import del_at, set_at, append_at
from mongo_const import URL, SDK_REPORT_COLLECTION, SDK_REPORT_TEST


def main():
    client = pymongo.MongoClient("localhost", 27017)
    db = client.main
    test_collection = db[SDK_REPORT_TEST]
    original = db[SDK_REPORT_COLLECTION]

    # clean existing docs if any
    test_collection.delete_many({})
    v = version_gen(4, 3)
    size_base = 2_000_000
    d = datetime.datetime(2020, 8, 22, 20, 17, 0, tzinfo=datetime.timezone.utc)
    # we have only 8 docs ( we create more of them)
    doc_iter = original.find().sort([("context.argo.creationTimestamp", pymongo.ASCENDING)])
    docs = [doc for doc in doc_iter]
    for idx in range(12):
        for doc in docs:
            doc = deepcopy(doc)
            next_delta = datetime.timedelta(days=random.randint(5, 17), hours=random.randint(3, 18))
            d += next_delta

            del_at(doc, "_id")
            cpu_usage_base = random.random()
            memory_usage_base = 89 + random.random() * 77
            messages_processed_base = random.randint(72, 87) + random.random() * 6
            size_base += random.randint(500, 60000)
            measurements = {
                "cpu usage (cores)": {
                    "0.9": 0.22 + cpu_usage_base,
                    "0.99": 0.44 + cpu_usage_base,
                    "max": 0.55 + cpu_usage_base,
                    "median": cpu_usage_base,
                },
                "memory_usage (Mb)": {
                    "0.9": memory_usage_base + 6.4,
                    "0.99": memory_usage_base + 12.3,
                    "max": memory_usage_base + 23.7,
                    "median": memory_usage_base
                },
                "messages processed by consumer (/s)": {
                    "max": messages_processed_base + 21,
                    "median": messages_processed_base,
                },
                "sdk_size": {
                    "full": int(size_base * 1.8),
                    "min": int(size_base),
                }
            }
            # note currently we don't save dates it as MongoDb's ISODate but as a string (we probably should, if possible)
            d_text = d.isoformat()[:19] + "Z"
            d_text = d # use a proper date (for our tests)
            set_at(doc, d_text, "context.argo.creationTimestamp")
            set_at(doc, d_text, "context.argo.startTimestamp")
            set_at(doc, d_text, "metadata.timeCreated.$date")
            set_at(doc, d_text, "metadata.timeUpdated.$date")
            set_at(doc, d_text, "metadata.commitDate")
            set_at(doc, d_text, "context.argo.startTimestamp")
            set_at(doc, measurements, "results.measurements")
            version = {"name": "version", "value": next(v)}
            append_at(doc, version, "metadata.labels")

            test_collection.insert_one(doc)


def version_gen(max_min, max_rev):
    v_major = 0
    while True:
        num_minor_versions = random.randint(1, max_min)
        for v_minor in range(num_minor_versions):
            num_patch = random.randint(1, max_rev)
            for v_patch in range(num_patch):
                if v_major == 0 and v_minor == 0 and v_patch == 0:
                    continue
                yield f"{v_major}.{v_minor}.{v_patch}"
        v_major += 1


if __name__ == '__main__':
    main()
