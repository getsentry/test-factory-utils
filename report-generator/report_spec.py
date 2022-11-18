from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Union
from abc import ABC, abstractmethod
import jmespath
from jmespath.parser import ParsedResult

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class ValueExtractorSpec(ABC):
    @abstractmethod
    def extract_value(self, document):
        """
        Extracts a value from a document or none if not available
        """
        pass

    @abstractmethod
    def getName(self) -> str:
        """
        Returns the name for the colum
        """


@dataclass
class ConstValueExtractor(ValueExtractorSpec):
    """
    ConstValueExtractor returns a constant value regardless of the document passed
    It is used to create a column with a constant value
    """
    value: Any
    name: Optional[str] = None
    compiled_path: Optional[ParsedResult] = None

    def extract_value(self, document):
        return self.value

    def getName(self):
        return self.name


@dataclass
class PathValueExtractor(ValueExtractorSpec):
    """
    PathValueExtractorSpec defines how a value (e.g. a cell in a DataFrame) is computed from a JSON (mongo) document.

    A value extractor has:
    - a name (typically representing the column name inside a DataFrame)
    - a path to the data to be extracted form a document
    - a compile_path is the cached value of the compiling a path, it is created for path as an optimization,
    after the first extraction from a document ( subsequent Value extractions from other documents will use
    the compiled path)
    """
    path: str
    name: Optional[str] = None
    compiled_path: Optional[ParsedResult] = None

    def extract_value(self, document):
        if self.compiled_path is None:
            self.compiled_path = jmespath.compile(
                self.path
            )
        return self.compiled_path.search(document)

    def getName(self):
        return self.name


@dataclass
class OrValueExtractor(ValueExtractorSpec):
    """
    OrValueExtractor aggregates multiple value extractors.
    It will try all value extractors in order the first non None
    value will be returned or None if all extractors return none
    """
    extractors: Optional[List[ValueExtractorSpec]] = None
    name: Optional[str] = None

    def extract_value(self, document):
        if self.extractors is None:
            return None
        for extractor in self.extractors:
            value = extractor.extract_value(document)
            if value is not None:
                return value
        return None

    def getName(self) -> str:
        return self.name


@dataclass
class BooleanExtractor(ValueExtractorSpec):
    """
    Converts the value from an extractor to boolean
    """

    # the root extractor whose value is going to be converted to bool
    extractor: ValueExtractorSpec
    # what should it return when the root extractor returns None
    none_value: Optional[bool] = None

    def getName(self) -> str:
        return self.extractor.getName()

    def extract_value(self, document):
        value = self.extractor.extract_value(document)
        if value is None:
            return self.none_value

        if type(value) == bool:
            return value
        elif type(value) == str:
            value = value.lower()
            if value == "false" or value == "no" or value == "0" or value == "":
                return False
            return True
        elif type(value) == int:
            return value != 0
        return True


def make_value(value: Any, name: Optional[str] = None) -> ValueExtractorSpec:
    """returns a value extractor spec with a fixed value"""
    return ConstValueExtractor(value=value, name=name)


def make_label(label: str, name: Optional[str] = None) -> ValueExtractorSpec:
    """returns a value extractor that extracts a label value"""
    path = f"metadata.labels[?name=='{label}'].value|[0]"
    compile_path = jmespath.compile(path)
    if name is None:
        name = label
    return PathValueExtractor(path=path, compiled_path=compile_path, name=name)


def make_measure(
    measure: str, attribute: str, name=Optional[str]
) -> ValueExtractorSpec:
    """returns an extractor that extracts a measurement"""
    path = f'results.measurements."{measure}"."{attribute}"'
    compile_path = jmespath.compile(path)
    return PathValueExtractor(path=path, compiled_path=compile_path, name=name)


def extractor_from_path(
    path: str, name: str
) -> ValueExtractorSpec:
    """returns an extractor that extracts from the specified path"""
    compile_path = jmespath.compile(path)
    return PathValueExtractor(path=path, compiled_path=compile_path, name=name)


def boolean_extractor(extractor: ValueExtractorSpec, none_value=None):
    """returns a ll"""
    return BooleanExtractor(extractor=extractor, none_value=none_value)


def or_extractor(extractors: List[ValueExtractorSpec], name=None):
    """
    Delegates to the OrValueExtractor constructor
    Added for symetry with other extractor constructor functions
    """
    return OrValueExtractor(extractors=extractors, name=name)


@dataclass
class RowExtractorSpec:
    """
    Represents a list of ValueExtractors that create a row (e.g. a row in a DataFrame)
    A DataFrameSpec will use one or more RowExtractorSpecs to transform documents into DataFrames.
    For each RowExtractorSpec a new row may  be created (see below) from each document.

    A RowExtractorSpec can be configured to either generate rows with missing values (when extractors return
    None) or not to generate Rows if any of the extractors return None.
    """
    accepts_null: bool = False
    columns: List[ValueExtractorSpec] = None

    def __post_init__(self):
        if self.columns is None:
            self.columns = []

    def extract_row(self, document) -> Optional[List[Any]]:
        """
        Extracts a row from a document
        returns the row if extraction was possible or None if not.
        """
        if self.columns is None:
            return None
        ret_val = []
        for col_extractor in self.columns:
            val = col_extractor.extract_value(document)
            if val is None and not self.accepts_null:
                # all column extractors must return non None give up
                return None
            ret_val.append(val)
        return ret_val


def generate_extractors(
    labels: List[str],
    measurement_name: str,
    aggregations: List[Union[str, Tuple[str, str]]],
    extra=Optional[List[ValueExtractorSpec]],
) -> List[RowExtractorSpec]:
    """
    Creates a list of RowExtractors for a measurement and a list of aggregations.
    """
    extractors = []
    for measurement in aggregations:
        if isinstance(measurement, str):
            measurement = (measurement, measurement)
        columns = []
        for label in labels:
            columns.append(make_label(label, name=label))
        columns.append(make_value(measurement[1], name="measurement"))
        columns.append(make_measure(measurement_name, measurement[0], name="value"))
        if extra is not None and len(extra) > 0:
            columns.extend(extra)
        extractors.append(RowExtractorSpec(accepts_null=False, columns=columns))
    return extractors


@dataclass
class DataFrameSpec:
    """
    Contains the recipe of how to turn JSON documents into datasets.
    Each document will generate up to len(extractors) rows.
    """
    name: str
    columns: List[str]
    extractors: List[RowExtractorSpec]
    # None or one of  the pandas types specified as a string: "float, int, str, datetime[ns/ms/s...],timestamp[ns/ms...] ; only necessary for datetime
    column_types: Optional[List[Optional[str]]] = None
    dataframe_sort: Optional[
        List[str]
    ] = None  # sort the dataframe by column (use it if you can't use mongo sort), use -column to sort descending
    unique_columns: Optional[List[str]] = None
