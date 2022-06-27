from collections.abc import Mapping, Sequence
from typing import Any, List, Union


def get_at(obj, *args, **kwargs) -> Any:
    """
    Gets the object at the specified path, it traverses dictionaries and arrays

    >>> x = { "a":[{"x":{ "w": [1,2,3]}}], "y": {"x":"abc", "w":123}}
    >>> get_at(x, "a", default="NOPE")
    [{'x': {'w': [1, 2, 3]}}]
    >>> get_at(x, "a", 0, "x.w.0")
    1
    >>> get_at(x, "a", 0, "x.w")
    [1, 2, 3]
    >>> get_at(x, "a", 0, "x")
    {'w': [1, 2, 3]}
    >>> get_at(x, "a.0.x")
    {'w': [1, 2, 3]}
    >>> get_at(x, "a.2.x", default="NOPE")
    'NOPE'
    >>> get_at(x, "a.1.x", default="NOPE")
    'NOPE'
    >>> get_at(x, "a.0.x", default="NOPE")
    {'w': [1, 2, 3]}
    >>> get_at(x, "y", default="NOPE")
    {'x': 'abc', 'w': 123}
    >>> get_at(x, "y","x", default="NOPE")
    'abc'
    >>> get_at(x, "y.x", default="NOPE")
    'abc'
    """
    path = []
    for arg in args:
        if isinstance(arg, int):
            path.append(arg)
        if isinstance(arg, str):
            ps = arg.split(".")
            path += ps

    default = kwargs.get("default")

    return _get_at_path(obj, path, default)


def _get_at_path(obj, path: List[Union[str, int]], default) -> Any:
    """

    """
    if path is None or len(path) == 0:
        return obj

    first = path[0]
    rest = path[1:]

    next_obj = _navigate(obj, first, default)

    if next_obj is default:
        return default

    return _get_at_path(next_obj, rest, default)


def _navigate(obj, idx: Union[str, int], default):
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(idx, default)
    if isinstance(obj, Sequence):
        try:
            idx = int(idx)
            if idx < len(obj):
                return obj[idx]
            return default
        except:
            return default

    return default
