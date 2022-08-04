"""
Testing data extraction from MongoDb
"""
from functools import cache
from typing import Optional, List, Any
from dateutil.parser import parse
import datetime

import jmespath
import pandas as pd
import pymongo
from jmespath.parser import ParsedResult

from report_spec import DataFrameSpec


def get_db(mongo_url):
    client = pymongo.MongoClient(mongo_url)
    return client.main


def to_data_frame(docs, spec: DataFrameSpec) -> Optional[pd.DataFrame]:
    column_values = [[] for x in spec.columns]

    for doc in docs:
        for extractor in spec.extractors:
            bad_sample = False
            temp_row = []
            for value_extractor in extractor.columns:
                if value_extractor.path is not None:
                    if value_extractor.compiled_path is None:
                        value_extractor.compiled_path = jmespath.compile(
                            value_extractor.path
                        )
                    value = value_extractor.compiled_path.search(doc)
                else:
                    value = value_extractor.value
                if not extractor.accepts_null and value is None:
                    bad_sample = True
                    break
                temp_row.append(value)
            if bad_sample:
                continue
            # if we are here we have successfully extracted meaningful values for all columns, add the row
            for idx, value in enumerate(temp_row):
                column_values[idx].append(value)
    vals = {}
    for idx in range(len(spec.columns)):
        vals[spec.columns[idx]] = column_values[idx]
    df = pd.DataFrame(vals)
    # finally do any explicit column conversions if specified
    if spec.column_types is not None:
        for idx, data_type in spec.column_types:
            if data_type is not None:
                # we have an explicit column type conversion
                column_name = spec.columns[idx]
                df[column_name] = df[column_name].astype(data_type)
    if spec.dataframe_sort is not None:
        columns = []
        sort_order = []
        for column in spec.dataframe_sort:
            ascending = True
            if column.startswith("-"):
                ascending = False
                column = column[1:]
            columns.append(column)
            sort_order.append(ascending)
        df.sort_values(by=columns, inplace=True, ascending=sort_order)
    return df


def labels_to_filter(labels):
    if len(labels) > 0:
        return {
            "$and": [
                {"metadata.labels": {"$elemMatch": {"name": name, "value": value}}}
                for name, value in labels
            ]
        }
    else:
        return {}


def get_docs(db, labels) -> List[Any]:
    """
    Returns the mongo documents extracted for the particular label
    """
    mongo_filter = labels_to_filter(labels)
    # get the tests in the reverse order of their run so that we can get to the last run tests first
    # we will discard the test results for old runs of the same test
    mongo_sort = [("metadata.timeUpdated", pymongo.DESCENDING)]
    collection = db["sdk_report"]

    # materialize the cursor so that we can reuse the collection in multiple extractions
    coll = []
    doc_identity = {}
    for doc in collection.find(mongo_filter, sort=mongo_sort):
        ident = get_test_id(doc)
        if ident not in doc_identity:
            doc_identity[ident] = True
            doc = fix_test_types(doc)
            coll.append(doc)

    # put them back in the order of their run
    coll.reverse()
    return coll


def fix_test_types(doc):
    """
    Converts test document types for known entries (mostly string to date)
    """

    metadata = doc.get("metadata")
    if metadata is not None:
        labels = metadata.get("labels")
        if labels is not None:
            for label in labels:
                name = label.get("name")
                if name == "commit_date":
                    label["value"] = datetime_converter(label.get("value"))
                elif name == "commit_count":
                    label["value"] = int_converter(label.get("value"))
    context = doc.get("context")
    if context is not None:
        argo = context.get("argo")
        if argo is not None:
            argo["creationTimestamp"] = datetime_converter(argo.get("creationTimestamp"))
            argo["startTimestamp"] = datetime_converter(argo.get("startTimestamp"))
        run = context.get("run")
        if run is not None:
            run["endTimestamp"] = datetime_converter(run.get("endTimestamp"))
            run["startTimestamp"] = datetime_converter(run.get("endTimestamp"))
            run["stageStartTimestamp"] = datetime_converter(run.get("endTimestamp"))
            run["stageEndTimestamp"] = datetime_converter(run.get("stageEndTimestamp"))
    return doc


def get_test_id(doc):
    """
    Returns the unique identity of the test so that we can detect tests that run more than once.
    """
    return tuple((id_path.search(doc) or "-" for id_path in _identity_paths()))


@cache
def _get_paths_for_conversion():
    """
    Returns compiled-paths, converter-function tuples for test documents
    """
    paths_to_convert = [
        ("metadata.labels[?name=='commit_date'].value|[0]", datetime_converter),
        ("metadata.labels[?name=='commit_count'].value|[0]", datetime_converter),
        ("metadata.context.argo.creationTimestamp", datetime_converter),
        ("metadata.context.argo.startTimestamp", datetime_converter),
        ("metadata.context.run.startTimestamp", datetime_converter),
        ("metadata.context.run.endTimestamp", datetime_converter),
        ("metadata.context.run.stageStartTimestamp", datetime_converter),
        ("metadata.context.run.stageEndTimestamp", datetime_converter),
    ]

    return [(jmespath.compile(path), converter) for path, converter in paths_to_convert]




@cache
def _identity_paths() -> List[ParsedResult]:
    labels = [
        "commit_sha",
        "runner",
        "workflowName",
        "templateName",
        "platform",
        "test_name",
        "environment",
    ]
    path = "metadata.labels[?name=='{}'].value|[0]"
    return [jmespath.compile(path.format(label)) for label in labels]


def datetime_converter(val):
    if type(val) == datetime.datetime:
        return val
    try:
        return parse(val).astimezone(datetime.timezone.utc)
    except Exception:
        return None


def int_converter(val):
    try:
        return int(val)
    except ValueError:
        return 0
