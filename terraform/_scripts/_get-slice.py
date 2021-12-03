#!/usr/bin/env python3
import sys
from pathlib import Path

USAGE = f"""
{sys.argv[0]} PATH [PATH ...]

    This helper script takes a list of files and prints the deduplicated list of Terraform slices where they reside.
    NOTE: the script doesn't check that the files or slices actually exist.
"""


# The test can be run e.g. via "pytest ./_get-slice.py"
def test_basic():
    test_input = [
        "terraform/sentry-st-testing/aaa/foo.tf",
        "terraform/sentry-st-testing/aaa/bar.tf",
        "terraform/sentry-st-testing/bbb/baz.tf",
        "terraform/other-project/bbb/foo.tf",
    ]

    expected_result = [
        "terraform/sentry-st-testing/aaa",
        "terraform/sentry-st-testing/bbb",
        "terraform/other-project/bbb",
    ]
    assert get_slices(test_input) == expected_result


def get_slice_path(path):
    slice_parts = Path(path).parts[:3]
    assert slice_parts
    assert len(slice_parts) == 3
    assert slice_parts[0] == "terraform"
    return str(Path(*slice_parts))


def get_slices(paths):
    modified_slices = set()
    for path in paths:
        modified_slices.add(get_slice_path(path))
    return sorted(modified_slices)


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        print(USAGE)
        sys.exit("No arguments provided.")

    for slice in get_slices(args):
        print(slice)


if __name__ == "__main__":
    main()
