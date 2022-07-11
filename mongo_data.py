"""
Testing data extraction from MongoDb
"""
from typing import Optional

import jmespath
import pandas as pd
import pymongo

from report_spec import DataFrameSpec, RowExtractorSpec, ValueExtractorSpec, ConverterSpec
from utils import get_at
from mongo_const import SDK_REPORT_TEST
from value_converters import get_converter


def get_db():
    client = pymongo.MongoClient("localhost", 27017)
    return client.main


def get_collection():
    db = get_db()
    test_collection = db[SDK_REPORT_TEST]
    return test_collection


def get_version(labels):
    versions = filter(lambda x: x.get("name") == "version", labels)
    versions = list(versions)
    if len(versions) > 0:
        return versions[0].get("value")
    return None


def main():
    sdk_size = get_sdk_size()
    print(sdk_size)


def to_data_frame(coll_it, spec: DataFrameSpec) -> Optional[pd.DataFrame]:
    column_values = [[] for x in spec.columns]

    for doc in coll_it:
        for extractor in spec.extractors:
            bad_sample = False
            temp_row = []
            for value_extractor in extractor.columns:
                if value_extractor.path is not None:
                    if value_extractor.compiledPath is None:
                        value_extractor.compiledPath = jmespath.compile(value_extractor.path)
                    value = value_extractor.compiledPath.search(doc)
                    if value_extractor.converter is not None:
                        converter = value_extractor.converter
                        if converter.func is None:
                            converter.func = get_converter(converter)
                        value = converter.func(value)
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
        column = spec.dataframe_sort
        ascending = True
        if spec.dataframe_sort.startswith("-"):
            ascending = False
            column = column[1:]
        df.sort_values(by=[column], inplace=True, ascending=ascending)
    return df


def load_data_frame(db, spec: DataFrameSpec) -> Optional[pd.DataFrame]:
    if not spec.validate():
        return None

    collection = db[spec.mongo_collection]

    query = spec.mongo_filter if spec.mongo_filter is not None else {}
    projection = spec.mongo_projection if spec.mongo_projection is not None else {}

    it = collection.find(query, projection)
    if spec.mongo_sort:
        it = it.sort(spec.mongo_sort)
    return to_data_frame(it, spec)


def fix_doc_dates(doc):
    pass


def get_sdk_size():
    spec = DataFrameSpec(
        mongo_collection="sdk_report2",
        mongo_filter={},
        mongo_projection={},
        mongo_sort=[("metadata.timeUpdated", pymongo.ASCENDING)],
        columns=["started", "version", "measurement", "value"],
        extractors=[
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="metadata.labels[?name=='commit_date'].value|[0]", converter=ConverterSpec(type="datetime")),
                    ValueExtractorSpec(path="metadata.labels[?name=='version'].value|[0]"),
                    ValueExtractorSpec(value="mean"),
                    ValueExtractorSpec(path='results.measurements.cpu_usage."quantile-mean"'),
                ]
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="metadata.labels[?name=='commit_date'].value|[0]", converter=ConverterSpec(type="datetime")),
                    ValueExtractorSpec(path="metadata.labels[?name=='version'].value|[0]"),
                    ValueExtractorSpec(value="q05"),
                    ValueExtractorSpec(path='results.measurements.cpu_usage."quantile-0.5"'),
                ]
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="metadata.labels[?name=='commit_date'].value|[0]", converter=ConverterSpec(type="datetime")),
                    ValueExtractorSpec(path="metadata.labels[?name=='version'].value|[0]"),
                    ValueExtractorSpec(value="q09"),
                    ValueExtractorSpec(path='results.measurements.cpu_usage."quantile-0.9"'),
                ]
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="metadata.labels[?name=='commit_date'].value|[0]", converter=ConverterSpec(type="datetime")),
                    ValueExtractorSpec(path="metadata.labels[?name=='version'].value|[0]"),
                    ValueExtractorSpec(value="max"),
                    ValueExtractorSpec(path='results.measurements.cpu_usage."quantile-1.0"'),
                ]
            ),
        ],
    )
    return load_data_frame(get_db(), spec)


def get_sdk_size_old():
    sizes = []
    col = get_collection()
    for doc in col.find().sort([("context.argo.creationTimestamp", pymongo.ASCENDING)]):
        labels = get_at(doc, "metadata..labels")
        version = get_version(labels)
        started = get_at(doc, "metadata..commitDate")
        full_val = get_at(doc, "results..measurements..sdk_size..full")
        min_val = get_at(doc, "results..measurements..sdk_size..min")

        sizes.append(get_measurement(version, started, "full", full_val))
        sizes.append(get_measurement(version, started, "min", min_val))
    df = pd.DataFrame(sizes)
    return df


def get_performance_data():
    measurements = []
    col = get_collection()
    for doc in col.find().sort([("context.argo.creationTimestamp", pymongo.ASCENDING)]):
        labels = get_at(doc, "metadata..labels")
        version = get_version(labels)
        started = get_at(doc, "metadata..commitDate")
        cpu = get_at(doc, "results..measurements..cpu usage (cores)")
        memory = get_at(doc, "results..measurements..memory_usage (Mb)")
        num_messages = get_at(doc, "results..measurements..messages processed by consumer (/s)")

        perf_data = {
            "version": version,
            "started": started,
            "cpu": cpu,
            "memory": memory,
            "num_messages": num_messages
        }
        measurements.append(perf_data)
    return measurements


def get_measurement(version, started, measurement, val):
    return {"started": started, "version": version, "measurement": measurement, "value": val}


if __name__ == '__main__':
    main()
