from dataclasses import dataclass
from typing import List

import datapane as dp

from sdk_performance_datasets import get_cpu_usage, get_ram_usage
from sdk_performance_graphs import trend_plot


def main():
    cpu_usage = get_cpu_usage()
    ram_usage = get_ram_usage()

    report = dp.Report(
        trends_page(cpu_usage, ram_usage),
        last_release_page(cpu_usage, ram_usage),
    )

    report.save("sdk_performance.html", open=True, formatting=dp.ReportFormatting(width=dp.ReportWidth.MEDIUM))


@dataclass
class LastTwo:
    name: str
    current: float
    previous: float


def get_last_two(dataframe, measurements) -> List[LastTwo]:
    ret_val = []
    for measurement in measurements:
        last_two = dataframe[dataframe['measurement'].isin([measurement])].tail(2)['value'].tolist()
        ret_val.append(LastTwo(name=measurement, current=last_two[1], previous=last_two[0]))
    return ret_val


def last_release_page(cpu_usage, ram_usage):
    intro = """
# Last Release

Last release stats
    
"""
    cpu_intro = "## Cpu Usage"
    mem_intro = "## Memory Usage"

    measurements = ["mean", "q05", "q09", "max"]

    memory_points = get_last_two(ram_usage, measurements)
    cpu_points = get_last_two(cpu_usage, measurements)

    memory_widgets = []

    for measurement in memory_points:
        memory_widgets.append(big_number(
            heading=measurement.name,
            current=measurement.current,
            previous=measurement.previous,
            bigger_is_better=False))

    cpu_widgets = []
    for measurement in cpu_points:
        cpu_widgets.append(big_number(
            heading=measurement.name,
            current=measurement.current,
            previous=measurement.previous,
            bigger_is_better=False))

    return dp.Page(
        title="Last Release",
        blocks=[
            intro,
            cpu_intro,
            dp.Group(columns=2, blocks=memory_widgets),
            mem_intro,
            dp.Group(columns=2, blocks=cpu_widgets),
        ]
    )


def trends_page(cpu_usage, ram_usage):
    text = """
# SKD Trends
SDK evolution.
        """

    cpu_usage_plot = trend_plot(cpu_usage, x="commit_date", y="value", time_series="measurement", title="cpu usage")
    ram_usage_plot = trend_plot(ram_usage, x="commit_date", y="value", time_series="measurement", title="mem_usage")

    return dp.Page(
        title="Trends",
        blocks=[
            text,
            dp.Plot(cpu_usage_plot),
            dp.DataTable(cpu_usage),
            dp.Plot(ram_usage_plot),
            dp.DataTable(ram_usage)
        ]
    )


def big_number(heading, current, previous, bigger_is_better):
    if previous != 0:
        change = (current - previous) / previous * 100
        change_str = f"{change:.{2}}%"
    else:
        change = current
        change_str = f"{change:.{2}}"

    if (bigger_is_better and change >= 0) or (not bigger_is_better and change <= 0):
        positive_intent = True
    else:
        positive_intent = False

    upward_change = current >= previous

    current = f"{current:.{4}}"
    previous = f"{previous:.{4}}"

    return dp.BigNumber(
        heading=heading,
        value=current,
        change=change_str,
        prev_value=previous,
        is_positive_intent=positive_intent,
        is_upward_change=upward_change
    )


if __name__ == '__main__':
    main()
