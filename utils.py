from collections import abc
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
    path = _to_path(args)
    default = kwargs.get("default")

    return _get_at_path(obj, path, default)


def _to_path(args) -> List[Union[str, int]]:
    path = []
    for arg in args:
        if isinstance(arg, int):
            path.append(arg)
        if isinstance(arg, str):
            ps = arg.split(".")
            path += ps
    return path


def set_at(obj, val, *args) -> bool:
    """
    >>> x = { "a":[{"x":{ "w": [1,2,3]}}], "y": {"x":"abc", "w":123}}
    >>> set_at(x, 12, "x.w")
    True
    >>> get_at(x, "x.w")
    12
    >>> set_at(x, 22, "a", 0, "x.w.0")
    True
    >>> get_at(x, "a.0.x.w")
    [22, 2, 3]
    >>> set_at(x, {"m": "n"}, "y.w")
    True
    >>> get_at(x, "y.w")
    {'m': 'n'}
    """
    path = _to_path(args)
    if len(path) < 1:
        return False

    return _set_at_path(obj, val, path)


def _set_at_path(obj, val, path: List[Union[str, int]]) -> bool:
    if len(path) < 1:
        return False

    first, rest = path[0], path[1:]

    if isinstance(obj, abc.MutableMapping):
        if len(rest) == 0:
            # just set the object
            obj[first] = val
            return True

        sub_obj = obj.get(first)
        if sub_obj is None:
            # no sub object, create one
            obj[first] = _create_new(val, rest)
            return True
        else:
            return _set_at_path(sub_obj, val, rest)
    elif isinstance(obj, abc.MutableSequence):
        try:
            first = int(first)
        except:
            return False  # trying to set a non int index into a sequence

        # ensure enough space in array
        if len(obj) < first + 1:
            obj.extend([None] * (first + 1 - len(obj)))

        if len(rest) == 0:
            obj[first] = val
            return True

        sub_obj = obj[first]
        if sub_obj is None:
            obj[first] = _create_new(val, rest)
            return True
        else:
            return _set_at_path(sub_obj, val, rest)
    return False


def _create_new(val, path):
    if len(path) == 0:
        return val

    first, rest = path[0], path[1:]

    try:
        first = int(first)
    except:
        pass  # tried to see if we have an array index

    if isinstance(first, int):
        ret_val = [None] * (first + 1)
    else:
        ret_val = {}
    ret_val[first] = _create_new(val, rest)
    return ret_val


def append_at(obj, val, *args) -> bool:
    """
    appends val to the speciried path .
    The path must either not exist ( in which case an array [val] is created at the end or the path )
    or be an array (in which case the val is appended to the array).
    """
    sub_obj = get_at(obj, *args)
    if sub_obj is None:
        return set_at(obj, [val], *args)
    elif isinstance(sub_obj, abc.MutableSequence):
        sub_obj.append(val)
        return True
    else:
        return False

def del_at(obj, *args) -> bool:
    """
    >>> x = { "a":[{"x":{ "w": [1,2,3]}}], "y": {"x":"abc", "w":123}}
    >>> del_at(x , "y.w")
    True
    >>> get_at(x , "y.w", default="Nope")
    'Nope'
    >>> del_at(x , "y")
    True
    >>> get_at(x, "y", default="Nope")
    'Nope'
    >>> del_at(x , "y")
    False
    >>> del_at(x, "a.0.x.w")
    True
    >>> get_at(x, "a.0.x")
    {}

    """
    path = _to_path(args)
    if len(path) < 1:
        return False

    sub_obj = _get_at_path(obj, path[:-1], None)
    try:
        if sub_obj is not None and path[-1] in sub_obj:
            del sub_obj[path[-1]]
            return True
    except:
        return False
    return False


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
    if isinstance(obj, abc.Mapping):
        return obj.get(idx, default)
    if isinstance(obj, abc.Sequence):
        try:
            idx = int(idx)
            if idx < len(obj):
                return obj[idx]
            return default
        except:
            return default

    return default
