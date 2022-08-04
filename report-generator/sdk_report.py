from dataclasses import dataclass
from typing import Mapping, List, Tuple
import datapane as dp
import jmespath
import pandas as pd

from mongo_data import MeasurementInfo
from report_generator_support import trend_plot, get_data_frame, big_number
from report_spec import DataFrameSpec, generate_extractors


@dataclass
class MeasurementSeries:
    info: MeasurementInfo
    trend: pd.DataFrame
    current: pd.DataFrame


def generate_report(trend_docs, current_doc, measurements: List[MeasurementInfo], filters, commit_sha):
    measurement_series = []

    for measurement in measurements:
        extractors = generate_extractors(
            labels=["commit_date", "commit_count"],
            measurement_name=measurement.name,
            aggregations=measurement.aggregations
        )
        data_frame_spec = DataFrameSpec(
            name=measurement.name,
            columns=["commit_date", "commit_count", "measurement", "value"],
            extractors=extractors,
        )

        current_test_frame = get_data_frame([current_doc], data_frame_spec)
        trend_frame = get_data_frame(trend_docs, data_frame_spec)

        measurement_series.append(MeasurementSeries(info=measurement, trend=trend_frame, current=current_test_frame))

    introduction = intro(filters, commit_sha, [current_doc])

    report = dp.Report(
        last_release_page(introduction, measurement_series),
        trends_page(measurement_series),
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


def intro(filters: List[Tuple[str, str]], git_sha: str, current_docs) -> str:
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
    description: str, measurement_series: List[MeasurementSeries]):
    intro = f"""
{description}
# Last Release

Last release stats

"""
    blocks = [intro]
    for series in measurement_series:
        series_intro = f"## {series.info.name}"
        blocks.append(series_intro)
        trend = get_last(series.trend, series.info.aggregations)
        current = get_last(series.current, series.info.aggregations)
        widgets = []
        for aggregation in series.info.aggregations:
            widgets.append(big_number(heading=aggregation,
                                      current=current.get(aggregation),
                                      previous=trend.get(aggregation),
                                      bigger_is_better=False))  # TODO bigger_is_better should come form metadata
        blocks.append(dp.Group(columns=2, blocks=widgets))

    return dp.Page(
        title="Last Release",
        blocks=blocks,
    )


def trends_page(measurement_series: List[MeasurementSeries]):
    text = f"""
# SDK Trends
SDK evolution.

        """

    blocks = [text]
    for series in measurement_series:
        blocks.append(f"## {series.info.name}\n\n")
        plot = trend_plot(
            series.trend,
            x="commit_date:T",
            y="value:Q",
            time_series="measurement:N",
            title=series.info.name)
        blocks.append(plot)

    return dp.Page(
        title="Trends",
        blocks=blocks,
    )
