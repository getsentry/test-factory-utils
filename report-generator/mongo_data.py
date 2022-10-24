"""
Testing data extraction from MongoDb
"""
import datetime
from dataclasses import dataclass
from functools import cache
from typing import Any, List, Optional, Tuple, Mapping

import jmespath
import pandas as pd
import pymongo
from dateutil.parser import parse
from jmespath.parser import ParsedResult
from report_spec import DataFrameSpec
from utils import get_at


@dataclass
class AggregationInfo:
    id: str
    name: Optional[str] = None
    description: Optional[str] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if type(other) != AggregationInfo:
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.description == other.description
        )


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
        if self.id != other.id:
            return False
        if self.name != other.name:
            return False
        if self.description != other.description:
            return False
        if self.unit != other.unit:
            return False
        if self.bigger_is_better != other.bigger_is_better:
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
            argo["creationTimestamp"] = datetime_converter(
                argo.get("creationTimestamp")
            )
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
    """
    Extracts measurement definitions (MeasurementInfo) from a list of documents by looking at all the
    measurements and augmenting them with any available metadata about the measurement.
    At the end we should get a list of measurements and the aggregations associated with the measurements from
    all the documents. If there are different definitions (i.e. names or descriptions) for a measurement or a
    aggregation then the last definition wins.
    """

    # {"id": set("aggregation_id")}
    measurements_raw = {}

    # { "id": {
    #       "name": str,
    #       "unit": str,
    #       "description": str ,
    #       aggregations: { "id": {"name":str, "description":str}}
    #       }
    # }
    measurements_meta_raw = {}
    for doc in docs:
        # add to global measurements_raw dictionary  all the measurements and the aggregations present in the current doc
        measurements = get_at(doc, "results.measurements")
        if measurements is not None:
            for _id, measurement in measurements.items():
                if _id not in measurements_raw:
                    measurements_raw[_id] = set()
                for aggregation in measurement.keys():
                    measurements_raw[_id].add(aggregation)

        # add to  global measurements_meta_raw dictionary all the measurements metadata present in the current doc
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

                bigger_is_better = measurement_meta.get("bigger_is_better")
                if bigger_is_better is not None:
                    curr_meta["bigger_is_better"] = bigger_is_better

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


    # now we have the raw measurements and potentially meta-data for them, augment measurements with the metadata
    ret_val = _join_measurements_info(measurements_raw, measurements_meta_raw)
    return ret_val


def _join_measurements_info(measurements_raw: Mapping[str, Any], measurements_meta_raw: Mapping[str, Any]) -> List[MeasurementInfo]:
    """
    Consolidates two dictionaries containing measurements information
    extracted from measurement data and measurement metadata into a list of MeasurementInfo

    measurements_raw: a dictionary of measurement_id to a set of aggregation_ids for the measurement
        eg: {"cpu_usage": set("mean","q0.5", "quantile-0.9"), "ram_usage": set("mean","q0.5", "max")}

    measurements_meta_raw: a dictionary of measurement_id to a dictionary with measurement metadata
        eg: { "cpu_usage": {"name": "CPU usage", "description": "...", "unit": "nanocores",
                             "aggregations":{ "mean": {"name": "Mean", "description: "Mean..."}}
                            },
             "ram_usage": {....}
        }
    """
    ret_val = []

    if measurements_raw is None:
        return ret_val

    if measurements_meta_raw is None:
        measurements_meta_raw = {}

    for _id, measurement_raw in measurements_raw.items():
        meta = measurements_meta_raw.get(_id)
        measurement_name = _id
        measurement_description = None
        unit = None
        aggregations_meta = {}
        bigger_is_better = False

        if meta is not None:
            # augment measurement with metadata information
            measurement_name = meta.get("name", _id)
            measurement_description = meta.get("description")
            unit = meta.get("unit")

            bigger_is_better = meta.get("bigger_is_better", False)
            aggregations_meta = meta.get("aggregations", {})

        aggregations = []
        for aggregation_id in measurement_raw:
            aggregation_name = aggregation_id
            aggregation_description = None
            if meta is not None:
                # augment aggregation with metadata information
                aggregation_meta = aggregations_meta.get(aggregation_id, {})
                name = aggregation_meta.get("name")
                if name is not None:
                    aggregation_name = name
                aggregation_description = aggregation_meta.get("description")

            aggregations.append(
                AggregationInfo(
                    id=aggregation_id,
                    name=aggregation_name,
                    description=aggregation_description,
                )
            )

        ret_val.append(
            MeasurementInfo(
                _id,
                name=measurement_name,
                description=measurement_description,
                unit=unit,
                bigger_is_better=bigger_is_better,
                aggregations=sorted(aggregations, key=lambda agg: agg.id),
            )
        )

    return ret_val
