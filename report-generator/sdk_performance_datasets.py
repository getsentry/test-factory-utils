import pandas as pd

from mongo_data import to_data_frame
from report_spec import DataFrameSpec, RowExtractorSpec, ValueExtractorSpec


def get_data_frame(docs, spec: DataFrameSpec) -> pd.DataFrame:
    ret_val = to_data_frame(docs, spec)

    if spec.unique_columns is not None and len (spec.unique_columns) > 0:
        ret_val.drop_duplicates(subset=spec.unique_columns, inplace=True, keep='last')
    return ret_val
