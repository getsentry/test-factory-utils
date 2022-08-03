from typing import Mapping, List, Tuple
import datapane as dp
import jmespath

from sdk_performance_datasets import get_data_frame
from report_generator_graphs import trend_plot
from report_spec import DataFrameSpec, generate_extractors


def generate_report(trend_docs, current_doc, filters, commit_sha):
    measurements = [("quantile-mean", "mean"), ("quantile-05", "q05"), ("quantile-09", "q09"), ("quantile-1.0", "max")]

    cpu_extractors = generate_extractors(
        labels=["commit_date", "commit_count"],
        value_name="cpu_usage",
        measurements=measurements
    )

    cpu_spec = DataFrameSpec(
        name="cpu_usage",
        columns=["commit_date", "commit_count", "measurement", "value"],
        extractors=cpu_extractors
    )

    ram_extractors = generate_extractors(
        labels=["commit_date", "commit_count"],
        value_name="ram_usage",
        measurements=measurements
    )

    ram_spec = DataFrameSpec(
        name="ram_usage",
        columns=["commit_date", "commit_count", "measurement", "value"],
        extractors=ram_extractors)

    cpu_usage_trend = get_data_frame(trend_docs, cpu_spec)
    cpu_usage_current = get_data_frame([current_doc], cpu_spec)

    ram_usage_trend = get_data_frame(trend_docs, ram_spec)
    ram_usage_current = get_data_frame([current_doc], ram_spec)

    introduction = intro(filters, commit_sha, [current_doc])

    report = dp.Report(
        last_release_page(introduction, cpu_usage_trend, cpu_usage_current, ram_usage_trend, ram_usage_current),
        trends_page(cpu_usage_trend, ram_usage_trend),
    )
    return report


def report_description(filters, git_sha):
    filter_description = ", ".join(f"{name}: **{value}**" for name, value in filters)
    return f"SDK report for commit: **{git_sha}** with filters: {filter_description}"


def get_last(dataframe, measurements) -> Mapping[str, float]:
    ret_val = {}
    for measurement in measurements:
        vals = dataframe[dataframe["measurement"].isin([measurement])]
        if len(vals) > 0:
            ret_val[measurement] = vals.iloc[-1].value
    return ret_val


def intro(filters: List[Tuple[str, str]], git_sha: str, current_docs)->str:
    if len(current_docs) == 0:
        current_doc_info = f"Test for commit:'{git_sha}' not found"
    else:
        current_doc = current_docs[-1]
        commit_date = jmespath.search(
            "metadata.labels[?name=='commit_date'].value|[0]", current_doc
        )
        run_date = jmespath.search("context.run.startTimestamp", current_doc)

        dashboard_link = jmespath.search("results.data.dashboard_link", current_doc)
        argo_link = jmespath.search("context.argo.workflowUrl", current_doc)
        current_doc_info = f"""
**commit:** '{git_sha}'

**commit date:** '{commit_date}'

**ran at:** '{run_date}'

## Grafana [dashboard]({dashboard_link})

## Argo [workflow]({argo_link})

"""

    filters_used = ""
    for name, value in filters:
        filters_used += f"**{name}**: '{value}'\n\n"

    content = f"""
# About SDK report

## Filters used:
{filters_used}

## Current document info:
{current_doc_info}
"""
    return content


def last_release_page(
    description: str, cpu_usage_trend, cpu_usage_current, ram_usage_trend, ram_usage_current):
    intro = f"""
{description}
# Last Release

Last release stats

"""
    cpu_intro = "## Cpu Usage"
    mem_intro = "## Memory Usage"

    measurements = ["mean", "q05", "q09", "max"]

    memory_trend = get_last(ram_usage_trend, measurements)
    memory_current = get_last(ram_usage_current, measurements)
    cpu_trend = get_last(cpu_usage_trend, measurements)
    cpu_current = get_last(cpu_usage_current, measurements)

    memory_widgets = []
    cpu_widgets = []

    for measurement in measurements:
        memory_widgets.append(
            big_number(
                heading=measurement,
                current=memory_current.get(measurement),
                previous=memory_trend.get(measurement),
                bigger_is_better=False,
            )
        )

        cpu_widgets.append(
            big_number(
                heading=measurement,
                current=cpu_current.get(measurement),
                previous=cpu_trend.get(measurement),
                bigger_is_better=False,
            )
        )

    return dp.Page(
        title="Last Release",
        blocks=[
            intro,
            cpu_intro,
            dp.Group(columns=2, blocks=memory_widgets),
            mem_intro,
            dp.Group(columns=2, blocks=cpu_widgets),
        ],
    )


def trends_page( cpu_usage, ram_usage):
    text = f"""
# SDK Trends
SDK evolution.

        """

    if cpu_usage.shape[0] == 0:
        cpu_text = "# CPU info \nNo data found."
        cpu_blocks = [dp.Text(cpu_text)]
    else:
        cpu_usage_plot = trend_plot(
            cpu_usage,
            x="commit_date:T",
            y="value:Q",
            time_series="measurement:N",
            title="cpu usage",
        )
        cpu_blocks = [
            dp.Plot(cpu_usage_plot),
            dp.DataTable(cpu_usage),
        ]

    if ram_usage.shape[0] == 0:
        ram_text = "# RAM info \nNo data found."
        ram_blocks = [dp.Text(ram_text)]
    else:
        ram_usage_plot = trend_plot(
            ram_usage,
            x="commit_date:T",
            y="value:Q",
            time_series="measurement:N",
            title="ram usage",
        )
        ram_blocks = [
            dp.Plot(ram_usage_plot),
            dp.DataTable(ram_usage),
        ]

    return dp.Page(
        title="Trends",
        blocks=[
            text,
            *cpu_blocks,
            *ram_blocks,
        ],
    )


def big_number(heading, current, previous, bigger_is_better):
    if previous is not None and current is not None:
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
            is_upward_change=upward_change,
        )
    else:
        return dp.BigNumber(
            heading=heading,
            value=f"{current:.{4}}" if current is not None else "No Value",
            prev_value=f"{previous:.{4}}" if previous is not None else "No Value",
        )

