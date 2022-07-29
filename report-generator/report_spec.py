from dataclasses import dataclass
from typing import List, Any, Union, Optional, Callable

from yaml import load
from jmespath.parser import ParsedResult

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def read_spec(file_name):
    with open(file_name, mode="r") as f:
        data = load(f, Loader=Loader)
        return ReportSpec.from_dict(data)


@dataclass
class PlotSpec:
    name: str
    caption: str
    responsive: bool
    params: Any


@dataclass
class TextSpec:
    content: str


@dataclass
class TableSpec:
    data_frame: str
    name: str
    label: str
    caption: str


@dataclass
class BigNumberSpec:
    caption: str
    label: str
    name: str
    extractor: str
    data_frame: str
    params: Any


BasicUnits = Union["GroupSpec", TextSpec, PlotSpec, TableSpec, BigNumberSpec]


def dict_to_basic_unit(data):
    ty = data.get("type")
    unit_type = _basic_unit_dispatch.get(ty)

    if unit_type is None:
        return None
    else:
        return unit_type.from_dict(data)


@dataclass
class GroupSpec:
    name: str
    label: str
    columns: int
    content: List[BasicUnits]

    @staticmethod
    def from_dict(data):
        data = data.copy()
        contents_raw = data.get("contents", [])
        data["contents"] = [
            dict_to_basic_unit(element_raw) for element_raw in contents_raw
        ]
        GroupSpec(**data)


@dataclass
class PageSpec:
    title: str
    elements: List[BasicUnits]

    @staticmethod
    def from_dict(data) -> "PageSpec":
        data = data.copy()
        elements_raw = data.get("elements", [])
        data["elements"] = [
            dict_to_basic_unit(element_raw) for element_raw in elements_raw
        ]
        return PageSpec(**data)


@dataclass
class ConverterSpec:
    type: str
    extra: Optional[str] = None
    func: Callable[[Any], Any] = None

    @staticmethod
    def from_dict(data):
        type = data.get("type")
        extra = data.get("extra")
        return ConverterSpec(type=type, extra=extra)


@dataclass
class ValueExtractorSpec:
    path: Optional[str] = None
    value: Optional[Any] = None
    compiledPath: Optional[ParsedResult] = None
    converter: Optional[ConverterSpec] = None

    @staticmethod
    def from_dict(data) -> "ValueExtractorSpec":
        path = data.get("path")
        value = data.get("value")
        converter_dict = data.get("converter")
        converter = None
        if converter_dict is not None:
            converter = ConverterSpec.from_dict(converter_dict)

        # TODO finish implementation
        return ValueExtractorSpec(path=path, value=value, converter=converter)


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


@dataclass
class DocStreamSpec:
    mongo_collection: str
    mongo_filter: Any = None
    mongo_sort: Any = None  # mongo db cursor sort (use it if you can)
    mongo_projection: Any = None

    @staticmethod
    def from_dict(data) -> "DocStreamSpec":
        mongo_collection = data.get("collection")
        mongo_filter = data.get("mongo_filter")
        return DocStreamSpec(
            mongo_collection=mongo_collection, mongo_filter=mongo_filter
        )


@dataclass
class DiffSpec:
    base: DocStreamSpec
    base_doc_filter: str
    current: DocStreamSpec
    current_doc_filter: str


@dataclass
class DataFrameSpec:
    columns: List[str]
    extractors: List[RowExtractorSpec]
    # None or one of  the pandas types specified as a string: "float, int, str, datetime[ns/ms/s...],timestamp[ns/ms...] ; only necessary for datetime
    column_types: Optional[List[Optional[str]]] = None
    dataframe_sort: Optional[
        str
    ] = None  # sort the dataframe by column (use it if you can't use mongo sort), use -column to sort descending

    @staticmethod
    def from_dict(data) -> "DataFrameSpec":
        columns = data.get("columns", [])
        extractors_raw = data.get("extractors", [])
        extractors = [
            RowExtractorSpec.from_dict(extractors_raw)
            for extractor_raw in extractors_raw
        ]
        return DataFrameSpec(columns=columns, extractors=extractors)

    def validate(self) -> bool:
        return True  # todo implement


@dataclass
class ReportSpec:
    pages: List[PageSpec]
    data_frames: List[DataFrameSpec]

    @staticmethod
    def from_dict(data) -> "ReportSpec":
        pages_raw = data.get("pages", [])
        pages = [PageSpec.from_dict(page_raw) for page_raw in pages_raw]
        data_frames_raw = data.get("data_frames", [])
        data_frames = [
            DataFrameSpec.from_dict(data_frame_raw)
            for data_frame_raw in data_frames_raw
        ]
        return ReportSpec(pages=pages, data_frames=data_frames)


_basic_unit_dispatch = {
    "group": GroupSpec,
    "text": TextSpec,
    "plot": PlotSpec,
    "table": TableSpec,
    "bigNumber": BigNumberSpec,
}
