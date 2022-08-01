import pandas as pd

from mongo_data import to_data_frame
from report_spec import DataFrameSpec, RowExtractorSpec, ValueExtractorSpec


def get_data_frame(docs, spec: DataFrameSpec) -> pd.DataFrame:
    ret_val = to_data_frame(docs, spec)
    # TODO duplicate removal should become part of the spec
    ret_val.drop_duplicates(subset=["commit_count", "measurement"], inplace=True, keep='last')
    return ret_val
