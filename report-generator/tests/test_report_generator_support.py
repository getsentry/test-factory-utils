from typing import Optional
import json
from io import StringIO
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

from report_generator_support import get_data_frame, filter_data_frame
from report_spec import DataFrameSpec, generate_extractors
from mongo_data import fix_test_types


def _current_directory():
    return Path(__file__).parent


def load_docs():
    file_path = _current_directory().joinpath("grouping-test-data.json")
    with open(file_path) as f:
        docs = json.load(f)
    fixed_docs = []
    for doc in docs:
        fixed_docs.append(fix_test_types(doc))
    return fixed_docs


def _get_data_frame_spec(name: str) -> DataFrameSpec:
    aggregations_ids = ["mean", "q0.5", "q0.9", "q1.0"]
    extractors = generate_extractors(
        labels=["commit_date", "commit_count", "test_name"],
        measurement_name=name,
        aggregations=aggregations_ids,
    )
    return DataFrameSpec(
        name=name,
        columns=[
            "commit_date",
            "commit_count",
            "test_name",
            "measurement",
            "value",
        ],
        unique_columns=[
            "commit_date",
            "commit_count",
            "test_name",
            "measurement",
        ],
        extractors=extractors,
    )


def get_value(df: pd.DataFrame, measurement: str, test_name: str) -> Optional[float]:
    selection = filter_data_frame(df, {'measurement': measurement, "test_name": test_name})
    if len(selection) != 1:
        return None  # not unique or non existent
    return selection["value"].iloc[0]


def test_get_data_frame():
    docs = load_docs()
    specs = _get_data_frame_spec("cpu_usage")
    frame = get_data_frame(docs, specs, "latest")
    assert get_value(frame, "mean", "test-run-node-app-baseline.sh") == 0.45
    assert get_value(frame, "q0.5", "test-run-node-app-baseline.sh") == 0.55
    assert get_value(frame, "q0.9", "test-run-node-app-baseline.sh") == 0.95
    assert get_value(frame, "q1.0", "test-run-node-app-baseline.sh") == 1.05
    assert get_value(frame, "mean", "test-run-node-app-test.sh") == 1.45
    assert get_value(frame, "q0.5", "test-run-node-app-test.sh") == 1.55
    assert get_value(frame, "q0.9", "test-run-node-app-test.sh") == 1.95
    assert get_value(frame, "q1.0", "test-run-node-app-test.sh") == 2.05

    frame = get_data_frame(docs, specs, "min")
    assert get_value(frame, "mean", "test-run-node-app-baseline.sh") == 0.4
    assert get_value(frame, "q0.5", "test-run-node-app-baseline.sh") == 0.5
    assert get_value(frame, "q0.9", "test-run-node-app-baseline.sh") == 0.9
    assert get_value(frame, "q1.0", "test-run-node-app-baseline.sh") == 1.0
    assert get_value(frame, "mean", "test-run-node-app-test.sh") == 1.4
    assert get_value(frame, "q0.5", "test-run-node-app-test.sh") == 1.5
    assert get_value(frame, "q0.9", "test-run-node-app-test.sh") == 1.9
    assert get_value(frame, "q1.0", "test-run-node-app-test.sh") == 2.0

    frame = get_data_frame(docs, specs, "max")
    assert get_value(frame, "mean", "test-run-node-app-baseline.sh") == 0.45
    assert get_value(frame, "q0.5", "test-run-node-app-baseline.sh") == 0.55
    assert get_value(frame, "q0.9", "test-run-node-app-baseline.sh") == 0.95
    assert get_value(frame, "q1.0", "test-run-node-app-baseline.sh") == 1.05
    assert get_value(frame, "mean", "test-run-node-app-test.sh") == 1.45
    assert get_value(frame, "q0.5", "test-run-node-app-test.sh") == 1.55
    assert get_value(frame, "q0.9", "test-run-node-app-test.sh") == 1.95
    assert get_value(frame, "q1.0", "test-run-node-app-test.sh") == 2.05

    frame = get_data_frame(docs, specs, "mean")
    assert get_value(frame, "mean", "test-run-node-app-baseline.sh") == pytest.approx(0.425, 0.00001)
    assert get_value(frame, "q0.5", "test-run-node-app-baseline.sh") == pytest.approx(0.525, 0.00001)
    assert get_value(frame, "q0.9", "test-run-node-app-baseline.sh") == pytest.approx(0.925, 0.00001)
    assert get_value(frame, "q1.0", "test-run-node-app-baseline.sh") == pytest.approx(1.025, 0.00001)
    assert get_value(frame, "mean", "test-run-node-app-test.sh") == pytest.approx(1.425, 0.00001)
    assert get_value(frame, "q0.5", "test-run-node-app-test.sh") == pytest.approx(1.525, 0.00001)
    assert get_value(frame, "q0.9", "test-run-node-app-test.sh") == pytest.approx(1.925, 0.00001)
    assert get_value(frame, "q1.0", "test-run-node-app-test.sh") == pytest.approx(2.025, 0.00001)


def test_filter_data_frame():
    raw = """
    a,b,c,value
    a1,b1,c1,1
    a1,b1,c2,2
    a1,b2,c3,3
    a1,b2,c4,4
    a2,b1,c1,5
    a2,b1,c2,6
    a2,b2,c3,7
    a2,b2,c4,8
"""

    raw = raw.replace(" ", "")
    df = pd.read_csv(StringIO(raw), dtype={"a": "string", "b": "string", "c": "string", "value": np.int64})

    data = filter_data_frame(df, {"c": "c1", "a": "a2"})
    assert len(data) == 1
    assert data.iloc[0]["value"] == 5

    data = filter_data_frame(df, {"a": "a1", "b": "b2"})
    assert len(data) == 2
    assert data.iloc[0]["value"] == 3
    assert data.iloc[1]["value"] == 4
    data = filter_data_frame(df, {"a": "a2", "b": "b2", "c":"c3"})
    assert len(data) == 1
    assert data.iloc[0]["value"] == 7
    data = filter_data_frame(df, {"a": "a3"})
    assert len(data) == 0
