import pandas as pd

from mongo_data import to_data_frame
from report_spec import (
    DataFrameSpec,
    RowExtractorSpec,
    ValueExtractorSpec,
    ConverterSpec,
)


def get_ram_usage(docs) -> pd.DataFrame:
    spec = DataFrameSpec(
        dataframe_sort="commit_count",
        columns=["commit_date", "commit_count", "measurement", "value"],
        extractors=[
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="mean"),
                    ValueExtractorSpec(
                        path='results.measurements.ram_usage."quantile-mean"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="q05"),
                    ValueExtractorSpec(
                        path='results.measurements.ram_usage."quantile-0.5"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="q09"),
                    ValueExtractorSpec(
                        path='results.measurements.ram_usage."quantile-0.9"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="max"),
                    ValueExtractorSpec(
                        path='results.measurements.ram_usage."quantile-1.0"'
                    ),
                ],
            ),
        ],
    )
    ret_val = to_data_frame(docs, spec)
    ret_val.drop_duplicates(
        subset=["commit_count", "measurement"], inplace=True, keep="last"
    )
    return ret_val


def get_cpu_usage(docs) -> pd.DataFrame:
    spec = DataFrameSpec(
        dataframe_sort="commit_count",
        columns=["commit_date", "commit_count", "measurement", "value"],
        extractors=[
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="mean"),
                    ValueExtractorSpec(
                        path='results.measurements.cpu_usage."quantile-mean"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="q05"),
                    ValueExtractorSpec(
                        path='results.measurements.cpu_usage."quantile-0.5"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="q09"),
                    ValueExtractorSpec(
                        path='results.measurements.cpu_usage."quantile-0.9"'
                    ),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_date'].value|[0]",
                        converter=ConverterSpec(type="datetime"),
                    ),
                    ValueExtractorSpec(
                        path="metadata.labels[?name=='commit_count'].value|[0]"
                    ),
                    ValueExtractorSpec(value="max"),
                    ValueExtractorSpec(
                        path='results.measurements.cpu_usage."quantile-1.0"'
                    ),
                ],
            ),
        ],
    )
    ret_val = to_data_frame(docs, spec)
    ret_val.drop_duplicates(
        subset=["commit_count", "measurement"], inplace=True, keep="last"
    )
    return ret_val
