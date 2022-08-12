"""
Testing data extraction from MongoDb
"""
from functools import cache
from typing import Optional, List, Any, Tuple
from dateutil.parser import parse
import datetime

import jmespath
import pandas as pd
import pymongo
from jmespath.parser import ParsedResult

from report_spec import DataFrameSpec
from dataclasses import dataclass

from utils import get_at


@dataclass
class AggregationInfo:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


@dataclass
class MeasurementInfo:
    id: str
    aggregations: List[AggregationInfo]
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    bigger_is_better: bool = False

    def __eq__(self, other):
        if type(other) != MeasurementInfo:
            return False
        if self.id != other.name:
            return False
        return set(self.aggregations) == set(other.aggregations)


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


def get_measurements(docs) -> List[MeasurementInfo]:
    measurements_raw = {}  # {"id": set("aggregation_id")}
    measurements_meta_raw = {}  # { "id": { "name": str, "unit": str, "description": str , aggregations: { "id": {"name":str, "description":str}} }
    for doc in docs:
        measurements = get_at(doc, "results.measurements")
        if measurements is not None:
            for _id, measurement in measurements.items():
                if _id not in measurements_raw:
                    measurements_raw[_id] = set()
                for aggregation in measurement.keys():
                    measurements_raw[_id].add(aggregation)

        meta = get_at(doc, "results._meta.measurements")
        if meta is not None:
            for _id, measurement_meta in meta.items():
                if _id not in measurements_meta_raw:
                    measurements_meta_raw[_id] = {"aggregations": {}}

                curr_meta = measurements_meta_raw[_id]
                curr_aggregations = curr_meta["aggregations"]

                name = measurement_meta.get("name")
                if name is not None:
                    curr_meta["name"] = name

                description = measurement_meta.get("description")
                if description is not None:
                    curr_meta["description"] = description

                unit = measurement_meta.get("unit")
                if unit is not None:
                    curr_meta["unit"] = unit

                aggregations_meta = measurement_meta.get("aggregations", {})
                for aggregation_id, aggregation_meta in aggregations_meta.items():
                    if aggregation_id not in curr_aggregations:
                        curr_aggregations[aggregation_id] = {}

                    current_aggregation = curr_aggregations[aggregation_id]

                    name = aggregation_meta.get("name")
                    if name is not None:
                        current_aggregation["name"] = name

                    description = aggregation_meta.get("description")
                    if description is not None:
                        current_aggregation["description"] = description

                    bigger_is_better = aggregation_meta.get("bigger_is_better")
                    if bigger_is_better is not None:
                        current_aggregation["bigger_is_better"] = bigger_is_better

    # now we have the raw measurements and potentially meat data for them, augment measurements with the metadata
    ret_val = []
    for _id, measurement_raw in measurements_raw.items():
        meta = measurements_meta_raw.get(_id)
        measurement_name = None
        measurement_description = None
        unit = None

        if meta is not None:
            measurement_name = meta.get("name")
            measurement_description = meta.get("description")
            unit = meta.get("unit")

            bigger_is_better = meta.get("bigger_is_better", False)

        aggregations = []
        aggregations_meta = meta.get("aggregations", {})
        for aggregation_id in measurement_raw:
            aggregation_name = aggregation_id
            aggregation_description = None
            if meta is not None:
                aggregation_meta = aggregations_meta.get(aggregation_id, {})
                name = aggregation_meta.get("name")
                if name is not None:
                    aggregation_name = name
                aggregation_description = aggregation_meta.get("description")
            aggregations.append(AggregationInfo(id=aggregation_id, name=aggregation_name, description=aggregation_description))

        ret_val.append(
            MeasurementInfo(_id, name=measurement_name, description=measurement_description, unit=unit, bigger_is_better=bigger_is_better, aggregations=aggregations))

    return ret_val
