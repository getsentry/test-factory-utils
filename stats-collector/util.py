import logging
import re
import pathlib
from dateutil.tz import tzlocal, UTC

from typing import Optional, Callable, Any
from datetime import timedelta, datetime


logger = logging.getLogger(__name__)

TIMEDELTA_REGEX = (
    r"(?P<minus>-)?"
    r"((?P<weeks>\d+)w)?"
    r"((?P<days>\d+)d)?"
    r"((?P<hours>\d+)h)?"
    r"((?P<minutes>\d+)m)?"
    r"((?P<seconds>\d+)s)?"
)
TIMEDELTA_PATTERN = re.compile(TIMEDELTA_REGEX, re.IGNORECASE)


def parse_timedelta(delta: str) -> Optional[timedelta]:
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
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        groups = match.groupdict()
        sign = -1 if groups.pop("minus", None) else 1
        parts = {k: int(v) for k, v in groups.items() if v}
        return timedelta(**parts) * sign
    return None


def pretty_timedelta(delta: timedelta) -> str:
    if delta is None:
        return "NONE"
    retVal = ""
    if delta < timedelta():
        # negative timedelta
        delta = -delta
        retVal += "-"
    weeks = delta.days // 7
    days = delta.days % 7
    hours = delta.seconds // (60 * 60)
    minutes = delta.seconds // 60 % 60
    seconds = delta.seconds % 60
    fraction = delta.microseconds / (10**6)

    if weeks != 0:
        retVal += f"{weeks}w"
    if days != 0:
        retVal += f"{days}d"
    if hours != 0:
        retVal += f"{hours}h"
    if minutes != 0:
        retVal += f"{minutes}w"
    if seconds != 0 or fraction != 0:
        seconds = seconds + fraction
        retVal += f"{seconds}s"
    return retVal


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


def to_optional_datetime(d: Optional[datetime]) -> str:
    if d is not None:
        return to_flux_datetime(d)
    else:
        return ""


def get_scalar_from_result(
    result, column: str = "_value", condition: Optional[Callable[[Any], bool]] = None
) -> Optional[float]:

    tables_num = len(result)

    for table in result:
        record_num = len(table.records)
        for record in table:
            if condition is None or condition(record):
                if tables_num > 1 or record_num > 1:
                    logger.warning(
                        f"Query returned several values (tables: {tables_num}, rows: {record_num})"
                    )
                return record[column]

    # Nothing matched
    return None
