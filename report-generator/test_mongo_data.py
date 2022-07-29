from mongo_data import to_data_frame
from report_spec import DataFrameSpec, ValueExtractorSpec, RowExtractorSpec


def f():
    return 71


def _get_docs():
    return [
        {
            "a": 11,
            "b": 12,
            "f": 13,
        },
        {
            "a": 21,
            "b": 22,
            "f": 23,
        },
        {
            "a": 31,
            "b": 32,
        },
    ]


def test_to_data_frame():
    spec = DataFrameSpec(
        mongo_filter="",
        mongo_collection="",
        mongo_projection="",
        columns=["A", "B", "F", "C"],
        extractors=[
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="a"),
                    ValueExtractorSpec(path="b"),
                    ValueExtractorSpec(path="f"),
                    ValueExtractorSpec(value="direct"),
                ],
            ),
            RowExtractorSpec(
                accepts_null=False,
                columns=[
                    ValueExtractorSpec(path="b"),
                    ValueExtractorSpec(path="a"),
                    ValueExtractorSpec(path="f"),
                    ValueExtractorSpec(value="inverted"),
                ],
            ),
        ],
    )

    result = to_data_frame(_get_docs(), spec)
    tuples = [t for t in result.itertuples(index=False, name=None)]
    assert tuples == [
        (11, 12, 13, "direct"),
        (12, 11, 13, "inverted"),
        (21, 22, 23, "direct"),
        (22, 21, 23, "inverted"),
    ]
