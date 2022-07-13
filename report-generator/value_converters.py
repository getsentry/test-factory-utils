"""
Contains value converters
Value converters convert values based on a spec
"""
import datetime
from typing import Callable, Any
from dateutil.parser import parse

from report_spec import ConverterSpec


def _datetime_converter_generator(spec: ConverterSpec):
    def converter(val):
        return parse(val).astimezone(datetime.timezone.utc)

    return converter


def ident_generator(spec):
    def ident(val):
        return val

    return ident


_converter_generator = {
    "datetime": _datetime_converter_generator,
}


def get_converter(spec: ConverterSpec) -> Callable[[Any], Any]:
    gen = _converter_generator.get(spec.type, ident_generator)
    return gen(spec)
