import os.path

from report_spec import (
    read_spec, ReportSpec, PlotSpec, TextSpec, TableSpec, BigNumberSpec,
    GroupSpec, PageSpec, RowExtractorSpec, DataFrameSpec, ValueExtractorSpec,
)
from tests.test_utils import to_absolute_path


def expected_spec():
    return ReportSpec(
        pages=[
            PageSpec(
                title="page 1",
                elements=[
                    GroupSpec(
                        name="g1",
                        label="l1",
                        columns=3,
                        content=[TextSpec(content="g1-t1")]
                    ),
                    TextSpec(content="some text"),
                    PlotSpec(
                        name="the-plot",
                        caption="the-plot-caption",
                        responsive=True,
                        params={"a": 1}
                    ),
                    TableSpec(
                        caption="the-table-caption",
                        label="the-table-label",
                        name="the-table",
                        data_frame="the-table-data-frame",
                    ),
                    BigNumberSpec(
                        caption="the-big-number-caption",
                        label="the-big-number-label",
                        name="the-big-number",
                        data_frame="the-big-number-data-frame",
                        extractor="the-big-number-extractor",
                        params={"a": 1}
                    )
                ]
            )
        ],
        data_frames=[
            DataFrameSpec(
                name="first-data-frame",
                columns=["c1", "c2", "c3"],
                column_types=["float", "int", "str"],
                dataframe_sort=["c1","c2","-c3"],
                extractors=[
                    RowExtractorSpec(
                        accepts_null=False,
                        columns=[
                            ValueExtractorSpec(
                                path="path1",
                            ),
                            ValueExtractorSpec(
                                value="inline-value1",
                                converter_name="converter1",
                            ),
                            ValueExtractorSpec(
                                name="value-extractor1",
                                path="extractor-path",
                                converter_name="converter2",
                            )
                        ]
                    ),
                    RowExtractorSpec(
                        accepts_null=True,
                        columns=[
                            ValueExtractorSpec(
                                path="path2",
                            ),
                            ValueExtractorSpec(
                                value="inline-value2",
                            ),
                            ValueExtractorSpec(
                                name="value-extractor2",
                                value="v2",
                            )
                        ]
                    ),
                ]
            ),
        ],
        value_extractors=[
            ValueExtractorSpec(
                name="value-extractor1",
                path="extractor-path",
                converter_name="converter2",
            ),
            ValueExtractorSpec(
                name="value-extractor2",
                value="v2"
            ),
        ]
    )


def test_report_spec():
    spec = read_spec(to_absolute_path("../test-fixture/simple-report.yaml"))
    expected = expected_spec()
    assert spec == expected
