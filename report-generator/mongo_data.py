"""
Testing data extraction from MongoDb
"""
from typing import Optional, List, Any

import jmespath
import pandas as pd
import pymongo

from report_spec import DataFrameSpec, DocStreamSpec
from value_converters import get_converter


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


def labels_to_filter(labels):
    if len(labels) > 0:
        return {
            "$and": [{"metadata.labels": {"$elemMatch": {"name": name, "value": value}}} for name, value in labels]
        }
    else:
        return {}


def get_docs(db, labels) -> List[Any]:
    """
    Returns the mongo documents extracted for the particular label
    """
    mongo_filter = labels_to_filter(labels)
    mongo_sort = [("metadata.timeUpdated", pymongo.ASCENDING)]
    collection = db["sdk_report"]

    # for now materialize the cursor so we can reuse the collection in multiple
    # extractions
    coll = [c for c in collection.find(mongo_filter, {}).sort(mongo_sort)]
    return coll
