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

    >>> parse_timedelta("2s") == timedelta(seconds=2)
    True
    >>> parse_timedelta("1h1s")== timedelta(hours=1, seconds=1)
    True
    >>> parse_timedelta("1d1s") == timedelta(days=1, seconds=1)
    True
    >>> parse_timedelta("2w17s") == timedelta(weeks=2, seconds=17)
    True
    >>> parse_timedelta("-1s") + parse_timedelta("2s") == timedelta(seconds=1)
    True
    """
    match = TIMEDELTA_PATTERN.match(delta)
    if match:
        groups = match.groupdict()
        sign = -1 if groups.pop("minus", None) else 1
        parts = {k: int(v) for k, v in groups.items() if v}
        return timedelta(**parts) * sign
    return None


def pretty_timedelta(delta: timedelta) -> str:
    """
    Convert into a human-readable timedelta that is also parsable by
    parse_timedelta and golang time.ParseDuration.

    >>> pretty_timedelta(timedelta(seconds=1))
    '1.0s'
    >>> pretty_timedelta(timedelta(weeks=1, days=1, hours=1, seconds=1, microseconds=1))
    '193h1.000001s'
    """
    if delta is None:
        return "NONE"
    ret_val = ""
    if delta < timedelta():
        # negative timedelta
        delta = -delta
        ret_val += "-"
    hours_from_days = delta.days * 24
    hours_from_seconds = delta.seconds // (60 * 60)
    hours = hours_from_days + hours_from_seconds
    minutes = delta.seconds // 60 % 60
    seconds = delta.seconds % 60
    fraction = delta.microseconds / (10 ** 6)

    if hours != 0:
        ret_val += f"{hours}h"
    if minutes != 0:
        ret_val += f"{minutes}m"
    if seconds != 0 or fraction != 0:
        seconds = seconds + fraction
        ret_val += f"{seconds}s"
    return ret_val


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
