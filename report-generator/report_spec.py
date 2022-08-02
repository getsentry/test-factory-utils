from dataclasses import dataclass
from typing import List, Any, Union, Optional, Callable, Mapping

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

    @staticmethod
    def from_dict(data):
        return PlotSpec(
            name=data.get("name"),
            caption=data.get("caption"),
            responsive=data.get("responsive"),
            params=data.get("params"),
        )


@dataclass
class TextSpec:
    content: str

    @staticmethod
    def from_dict(data):
        return TextSpec(content=data.get("content", ""))


@dataclass
class TableSpec:
    data_frame: str
    name: str
    label: str
    caption: str

    @staticmethod
    def from_dict(data):
        return TableSpec(
            data_frame=data.get("data_frame"),
            name=data.get("name"),
            label=data.get("label"),
            caption=data.get("caption"),
        )


@dataclass
class BigNumberSpec:
    caption: Optional[str]
    label: Optional[str]
    name: Optional[str]
    extractor: Optional[str]
    data_frame: str
    params: Any

    @staticmethod
    def from_dict(data):
        return BigNumberSpec(
            caption=data.get("caption"),
            label=data.get("label"),
            name=data.get("name"),
            extractor=data.get("extractor"),
            data_frame=data.get("data_frame"),
            params=data.get("params"),
        )


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
        contents_raw = data.get("content", [])
        data['content'] = [dict_to_basic_unit(element_raw) for element_raw in contents_raw]
        return GroupSpec(**{k: data.get(k) for k in ['name', 'label', 'columns', 'content']})


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
        return PageSpec(**{k: data.get(k) for k in ['title', 'elements']})


@dataclass
class ValueExtractorSpec:
    name: Optional[str] = None
    path: Optional[str] = None
    value: Optional[Any] = None
    compiled_path: Optional[ParsedResult] = None
    converter_name: Optional[str] = None
    converter: Optional[Callable[[Any], Any]] = None

    @staticmethod
    def from_dict(data) -> "ValueExtractorSpec":
        path = data.get("path")
        value = data.get("value")
        converter_name = data.get("converter_name")
        name = data.get("name")

        return ValueExtractorSpec(path=path, value=value, converter_name=converter_name, name=name)

    # check if this is a full extractor spec or only just a reference (and must be resolved before usage)
    def is_reference(self):
        return self.path is None and self.value is None

    def load_reference(self, reference: "ValueExtractorSpec"):
        self.path = reference.path
        self.value = reference.value
        self.converter_name = reference.converter_name


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

    def consolidate(self, global_extractors:Mapping[str, ValueExtractorSpec]):
        for column in self.columns:
            if column.is_reference():
                ref_extractor = global_extractors.get(column.name)
                if ref_extractor is not None:
                    column.load_reference(ref_extractor)


# TODO RaduW do I still need this?
# @dataclass
# class DocStreamSpec:
#     mongo_collection: str
#     mongo_filter: Any = None
#     mongo_sort: Any = None  # mongo db cursor sort (use it if you can)
#     mongo_projection: Any = None
#
#     @staticmethod
#     def from_dict(data) -> "DocStreamSpec":
#         mongo_collection = data.get("collection")
#         mongo_filter = data.get("mongo_filter")
#         return DocStreamSpec(
#             mongo_collection=mongo_collection, mongo_filter=mongo_filter
#         )
#
#
# @dataclass
# class DiffSpec:
#     base: DocStreamSpec
#     base_doc_filter: str
#     current: DocStreamSpec
#     current_doc_filter: str

@dataclass
class DataFrameSpec:
    name: str
    columns: List[str]
    extractors: List[RowExtractorSpec]
    # None or one of  the pandas types specified as a string: "float, int, str, datetime[ns/ms/s...],timestamp[ns/ms...] ; only necessary for datetime
    column_types: Optional[List[Optional[str]]] = None
    dataframe_sort: Optional[
        List[str
    ]] = None  # sort the dataframe by column (use it if you can't use mongo sort), use -column to sort descending

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
        return DataFrameSpec(name=name, columns=columns, extractors=extractors, column_types=column_types, dataframe_sort=dataframe_sort)

    # consolidates the extractors with globally defined extractors
    def consolidate(self, global_extractors: Mapping[str, ValueExtractorSpec]):
        for extractor in self.extractors:
            extractor.consolidate(global_extractors)

    def validate(self) -> bool:
        return True  # todo implement


@dataclass
class ReportSpec:
    pages: List[PageSpec]
    data_frames: List[DataFrameSpec]
    value_extractors: Optional[List[ValueExtractorSpec]] = None

    @staticmethod
    def from_dict(data) -> "ReportSpec":
        pages_raw = data.get("pages", [])
        pages = [PageSpec.from_dict(page_raw) for page_raw in pages_raw]
        data_frames_raw = data.get("data_frames", [])
        data_frames = [
            DataFrameSpec.from_dict(data_frame_raw)
            for data_frame_raw in data_frames_raw
        ]
        value_extractors_raw = data.get("value_extractors", [])
        value_extractors = [ValueExtractorSpec.from_dict(value_extractor_raw) for value_extractor_raw in value_extractors_raw]

        extractor_map = {extractor.name: extractor for extractor in value_extractors}
        for data_frame in data_frames:
            data_frame.consolidate(extractor_map)

        return ReportSpec(pages=pages, data_frames=data_frames, value_extractors=value_extractors)


_basic_unit_dispatch = {
    "group": GroupSpec,
    "text": TextSpec,
    "plot": PlotSpec,
    "table": TableSpec,
    "bigNumber": BigNumberSpec,
}
