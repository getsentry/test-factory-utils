import re
import pathlib
from dateutil.tz import tzlocal, UTC

from typing import Optional
from datetime import timedelta, datetime

TIMEDELTA_REGEX = (
    r'(?P<minus>-)?'
    r'((?P<weeks>\d+)w)?'
    r'((?P<days>\d+)d)?'
    r'((?P<hours>\d+)h)?'
    r'((?P<minutes>\d+)m)?'
    r'((?P<seconds>\d+)s)?'
)
TIMEDELTA_PATTERN = re.compile(TIMEDELTA_REGEX, re.IGNORECASE)


def parse_timedelta(delta: str) -> Optional[timedelta]:
    """ Parses a human readable timedelta (3d5h19m2s) into a datetime.timedelta.
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
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        groups = match.groupdict()
        sign = -1 if groups.pop("minus", None) else 1
        parts = {k: int(v) for k, v in groups.items() if v}
        return timedelta(**parts) * sign
    return None


def load_flux_file(file_name: str) -> str:
    current_file = pathlib.Path(__file__)
    dir_path = current_file.parent / "flux" / file_name

    content = dir_path.read_text()
    return content

def to_flux_datetime(d: datetime) -> str:
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        # naive tz assume it is local
        d.replace(tzinfo=tzlocal())

    # convert to UTC
    d = d.astimezone(UTC)

    return d.isoformat()[:19] + "Z"