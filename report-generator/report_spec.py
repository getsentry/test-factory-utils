from dataclasses import dataclass
from typing import Any, List, Mapping, Optional, Tuple, Union

import jmespath
from jmespath.parser import ParsedResult

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


@dataclass
class ValueExtractorSpec:
    name: Optional[str] = None
    path: Optional[str] = None
    value: Optional[Any] = None
    compiled_path: Optional[ParsedResult] = None

    @staticmethod
    def from_dict(data) -> "ValueExtractorSpec":
        path = data.get("path")
        value = data.get("value")
        converter_name = data.get("converter_name")
        name = data.get("name")

        return ValueExtractorSpec(path=path, value=value, name=name)

    # check if this is a full extractor spec or only just a reference (and must be resolved before usage)
    def is_reference(self):
        return self.path is None and self.value is None

    def load_reference(self, reference: "ValueExtractorSpec"):
        self.path = reference.path
        self.value = reference.value


def make_value(value: Any, name: Optional[str] = None) -> ValueExtractorSpec:
    """returns a value extractor spec with a fixed value"""
    return ValueExtractorSpec(value=value, name=name)


def make_label(label: str, name: Optional[str] = None) -> ValueExtractorSpec:
    """returns a value extractor that extracts a label value"""
    path = f"metadata.labels[?name=='{label}'].value|[0]"
    compile_path = jmespath.compile(path)
    return ValueExtractorSpec(path=path, compiled_path=compile_path, name=name)


def make_measure(
    measure: str, attribute: str, name=Optional[str]
) -> ValueExtractorSpec:
    """returns an extractor that extracts a measurement"""
    path = f'results.measurements."{measure}"."{attribute}"'
    compile_path = jmespath.compile(path)
    return ValueExtractorSpec(path=path, compiled_path=compile_path, name=name)


def extractor_from_path(
    path: str, name:str
) -> ValueExtractorSpec:
    compile_path = jmespath.compile(path)
    return ValueExtractorSpec(path=path, compiled_path=compile_path, name=name)


@dataclass
class RowExtractorSpec:
    accepts_null: bool = False
    columns: List[ValueExtractorSpec] = None

    def __post_init__(self):
        if self.columns is None:
            self.columns = []

    @staticmethod
    def from_dict(data) -> "RowExtractorSpec":
        accepts_null = data.get("accepts_null", False)
        columns_raw = data.get("columns", [])
        columns = [
            ValueExtractorSpec.from_dict(column_raw) for column_raw in columns_raw
        ]
        return RowExtractorSpec(accepts_null=accepts_null, columns=columns)

    def consolidate(self, global_extractors: Mapping[str, ValueExtractorSpec]):
        for column in self.columns:
            if column.is_reference():
                ref_extractor = global_extractors.get(column.name)
                if ref_extractor is not None:
                    column.load_reference(ref_extractor)


def generate_extractors(
    labels: List[str],
    measurement_name: str,
    aggregations: List[Union[str, Tuple[str, str]]]) -> List[RowExtractorSpec]:
    extractors = []
    for measurement in aggregations:
        if isinstance(measurement, str):
            measurement = (measurement, measurement)
        columns = []
        for label in labels:
            columns.append(make_label(label, name=label))
        columns.append(make_value(measurement[1], name="measurement"))
        columns.append(make_measure(measurement_name, measurement[0], name="value"))
        extractors.append(RowExtractorSpec(accepts_null=False, columns=columns))
    return extractors


@dataclass
class DataFrameSpec:
    name: str
    columns: List[str]
    extractors: List[RowExtractorSpec]
    # None or one of  the pandas types specified as a string: "float, int, str, datetime[ns/ms/s...],timestamp[ns/ms...] ; only necessary for datetime
    column_types: Optional[List[Optional[str]]] = None
    dataframe_sort: Optional[
        List[str]
    ] = None  # sort the dataframe by column (use it if you can't use mongo sort), use -column to sort descending
    unique_columns: Optional[List[str]] = None

    @staticmethod
    def from_dict(data) -> "DataFrameSpec":
        name = data.get("name")
        columns = data.get("columns", [])
        extractors_raw = data.get("extractors", [])
        extractors = [
            RowExtractorSpec.from_dict(extractor_raw)
            for extractor_raw in extractors_raw
        ]
        column_types = data.get("column_types", None)
        dataframe_sort = data.get("dataframe_sort", None)
        unique_columns = data.get("unique_columns", None)
        return DataFrameSpec(
            name=name,
            columns=columns,
            extractors=extractors,
            column_types=column_types,
            dataframe_sort=dataframe_sort,
            unique_columns=unique_columns,
        )

    # consolidates the extractors with globally defined extractors
    def consolidate(self, global_extractors: Mapping[str, ValueExtractorSpec]):
        for extractor in self.extractors:
            extractor.consolidate(global_extractors)

    def validate(self) -> bool:
        return True  # todo implement
