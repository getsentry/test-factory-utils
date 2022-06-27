from collections.abc import Mapping, Sequence
from typing import Any, List, Union


def get_at(obj, *args, **kwargs) -> Any:
    """


    """
    path = []
    for arg in args:
        if isinstance(arg, int):
            path += arg
        if isinstance(arg, str):
            ps = arg.split(".")
            path += ps

    default = kwargs.get("default")

    return get_at_path(obj, path, default)


def get_at_path(obj, path: List[Union[str,int]], default) -> Any:
    """

    """
    if path is None or len(path) == 0:
        return obj

    first = path[0]
    rest = path[1:]

    next_obj = _navigate(obj, first, default)

    if next_obj is default:
        return default

    get_at_path(next_obj, rest, default)


def _navigate(obj, idx: Union[str, int], default):
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(idx, default=default)
    if isinstance(obj, Sequence):
        try:
            idx = int(idx)
            if idx < len(obj):
                return obj[idx]
            return default
        except:
            return default

    return default
