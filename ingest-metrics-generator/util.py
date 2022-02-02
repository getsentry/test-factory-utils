import re
from datetime import timedelta
from typing import Optional


TIMEDELTA_REGEX = (
    r"(?P<minus>-)?"
    r"((?P<weeks>\d+)w)?"
    r"((?P<days>\d+)d)?"
    r"((?P<hours>\d+)h)?"
    r"((?P<minutes>\d+)m)?"
    r"((?P<seconds>\d+)s)?"
)
TIMEDELTA_PATTERN = re.compile(TIMEDELTA_REGEX, re.IGNORECASE)


def parse_timedelta(delta: Optional[str]) -> Optional[timedelta]:
    """Parses a human readable timedelta (3d5h19m2s) into a datetime.timedelta.
    Delta includes:
    * - (for negative deltas)
    * Xw weeks
    * Xd days
    * Xh hours
    * Xm minutes
    * Xs seconds

    >>> parse_timedelta("2s")
    datetime.timedelta(0, 2)
    >>> parse_timedelta("1h1s")
    datetime.timedelta(0, 3601)
    >>> parse_timedelta("1d1s")
    datetime.timedelta(1, 1)
    >>> parse_timedelta("2w17s")
    datetime.timedelta(14, 17)
    >>> parse_timedelta("-1s") + parse_timedelta("2s")
    datetime.timedelta(0, 1)
    """
    if delta is None:
        return None
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        groups = match.groupdict()
        sign = -1 if groups.pop("minus", None) else 1
        parts = {k: int(v) for k, v in groups.items() if v}
        return timedelta(**parts) * sign
    return None
