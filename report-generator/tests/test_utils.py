from pathlib import Path

import pytest
from mongo_data import get_test_id


def to_absolute_path(*args):
    tests_dir = Path(__file__).parent
    return Path(tests_dir, *args).resolve()


def _doc1():
    return {
        "metadata": {
            "labels": [
                {"name": "commit_sha", "value": "123"},
                {"name": "runner", "value": "runner1"},
                {"name": "workflowName", "value": "workflow1"},
                {"name": "templateName", "value": "template1"},
                {"name": "platform", "value": "python"},
                {"name": "test_name", "value": "test-123"},
                {"name": "environment", "value": "env1"},
            ]
        }
    }


def _empty_doc():
    return {"metadata": {"labels": []}}


@pytest.mark.parametrize(
    "doc, expected",
    [
        (
            _doc1(),
            ("123", "runner1", "workflow1", "template1", "python", "test-123", "env1"),
        ),
        (_empty_doc(), ("-", "-", "-", "-", "-", "-", "-")),
    ],
)
def test_identity(doc, expected):
    id = get_test_id(doc)
    assert id == expected
