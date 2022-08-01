"""
Contains value converters
Value converters convert values based on a spec
"""
import datetime
from typing import Callable, Any
from dateutil.parser import parse


def datetime_converter(val):
    return parse(val).astimezone(datetime.timezone.utc)


def ident(val):
    return val


_converter_generator = {
    "datetime": datetime_converter,
}


def get_converter(name: str) -> Callable[[Any], Any]:
    return _converter_generator.get(name, ident)
