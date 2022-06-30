"""
Test datapane as report generator for performance tests

all data: test + measurment

SELECT tr.id AS tid, started, ended, type, attr1, attr2, attr3, attr4, attr5, attr6,
       m.id AS mid , name, label1, label2, label3,label4, value
FROM test_run AS tr
INNER JOIN measurement AS m
ON tr.id = m.test_run_id

"""
from dataclasses import dataclass
from enum import Enum
from typing import Sequence, List, Optional

import pandas as pd
import datapane as dp
import altair as alt

# from mysql_data import get_sdk_size
from mongo_data import get_sdk_size


def main():
    report = get_report()
    report.save("sdk_performance.html", open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.MEDIUM))


def get_report():
    return dp.Report(
        sdk_size(),
        latest_releases()
    )


def sdk_size():
    text = """
# SKD Size

Sdk size evolution.
    """
    sdk_vals = get_sdk_size()

    return dp.Page(title="SDK Size", blocks=[
        text,
        dp.Plot(get_sdk_trend_plot(sdk_vals)),
        dp.DataTable(sdk_vals)
    ])


def get_sdk_trend_plot(sdk_vals):
    all_points = alt.Chart(sdk_vals)

    all_dots = all_points.encode(
        x="started",
        y="value",
        tooltip="version",
        color="measurement",
        shape=alt.Shape("measurement"),
    ).mark_point(size=10, opacity=0.5)

    trend_line = all_points.encode(
        x="started",
        y="value",
        color=alt.Color("measurement", legend=None)
    ).mark_line(size=1, opacity=0.3)

    minor_releases = last_minor_releases(sdk_vals)

    last_chart = alt.Chart(sdk_vals[sdk_vals["version"].isin(minor_releases)])

    last_points = last_chart.encode(
        x="started",
        y="value",
    ).mark_point(size=55, opacity=1.0).encode(
        shape="measurement",
        color="measurement"
    )

    last_text = last_chart.mark_text(
        align='center',
        baseline='line-bottom',
        dy=-10
    ).encode(
        x="started",
        y="value",
        text='version'
    )

    line = (alt.Chart(pd.DataFrame({'y': [8000000]})).
            mark_rule(size=1, strokeDash=[4, 4], color="red", opacity=0.5).
            encode(y='y'))

    warn_text = alt.Chart(pd.DataFrame({'y': [8000000]})).mark_text(text="too much", align="center", opacity=1, baseline="line-bottom", dx=-350, fontSize=14).encode(y="y")

    return alt.layer(
        all_dots,
        trend_line,
        line,
        warn_text,
        last_points,
        last_text,
    ).properties(
        width=850,
        height=400
    ).interactive()


@dataclass
class Version:
    major: int
    minor: int
    patch: int

    def __lt__(self, other):
        if isinstance(other, Version):
            if self.major != other.major:
                return self.major < other.major
            else:
                if self.minor != other.minor:
                    return self.minor < other.minor
                else:
                    return self.patch < other.patch

        return False

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"


def get_versions(version_strings: Sequence[str]) -> List[Version]:
    """
    Returns the sorted versions (from low to high) with duplicates removed
    """

    def to_version(ver_str: str):
        try:
            s = ver_str.split(".")

            return Version(int(s[0]), int(s[1]), int(s[2]))
        except:
            return None

    ret_val = []
    for vs in version_strings:
        ver = to_version(vs)
        if ver is not None:
            ret_val.append(ver)

    ret_val.sort()
    idx = 0
    while idx + 1 < len(ret_val):
        if ret_val[idx] == ret_val[idx + 1]:
            del ret_val[idx + 1]
        else:
            idx += 1

    return ret_val


class VersionLevel(Enum):
    Major = 0
    Minor = 1
    Patch = 2


def get_previous(v: Version, vs: Sequence[Version], level: VersionLevel):
    candidate = None
    if level == VersionLevel.Major:
        def test(v, elm):
            return v.major > elm.major
    elif level == VersionLevel.Minor:
        def test(v, elm):
            return v.major == elm.major and v.minor > elm.minor
    elif level == VersionLevel.Patch:
        def test(v, elm):
            return v.major == elm.major and v.minor == elm.minor and v.patch > elm.patch
    else:
        def test(v, elm):
            return False

    for elm in vs:
        if test(v, elm):
            if candidate is None or candidate < elm:
                candidate = elm

    return candidate


def get_latest_release(vs: Sequence[Version]) -> Optional[Version]:
    candidate = None
    for v in vs:
        if candidate is None or candidate < v:
            candidate = v
    return candidate


def latest_releases():
    text = """
    # Latest Releases
    
This page compares the current release with the previous and with
the previous minor and previous major releases.
    """
    return dp.Page(title="Latest Releases", blocks=[
        text,
    ])


def last_minor_releases(frame):
    ver_dict = {}
    for version in frame["version"]:
        ver, patch = split_version(version)
        if ver is None:
            continue  # skip invalid versions
        current = ver_dict.get(ver, 0)
        if patch > current:
            ver_dict[ver] = patch

    return {f"{k}.{v}" for k, v in ver_dict.items()}


def split_version(release: str):
    r = release.split(".")
    try:
        patch = int(r[2])
        return f"{r[0]}.{r[1]}", int(r[2])
    except:
        return None, None


if __name__ == '__main__':
    main()
