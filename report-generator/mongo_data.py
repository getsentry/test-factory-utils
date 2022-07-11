"""
Testing data extraction from MongoDb
"""
from typing import Optional

import jmespath
import pandas as pd
import pymongo

from report_spec import DataFrameSpec
from value_converters import get_converter


def get_db():
    client = pymongo.MongoClient("localhost", 27017)
    return client.main


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
