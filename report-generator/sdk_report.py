from dataclasses import dataclass
from typing import List, Mapping, Tuple

import altair as alt
import datapane as dp
import jmespath
import pandas as pd
from mongo_data import MeasurementInfo
from report_generator_support import big_number, get_data_frame, trend_plot
from report_spec import DataFrameSpec, generate_extractors


@dataclass
class MeasurementSeries:
    info: MeasurementInfo
    trend: pd.DataFrame
    current: pd.DataFrame


def generate_report(
    trend_docs, current_doc, measurements: List[MeasurementInfo], filters, commit_sha
):
    measurement_series = []

    for measurement in measurements:
        aggregations_ids = [agg.id for agg in measurement.aggregations]
        extractors = generate_extractors(
            labels=["commit_date", "commit_count", "test_name"],
            measurement_name=measurement.id,
            aggregations=aggregations_ids,
        )
        data_frame_spec = DataFrameSpec(
            name=measurement.id,
            columns=[
                "commit_date",
                "commit_count",
                "test_name",
                "measurement",
                "value",
            ],
            extractors=extractors,
        )

        current_test_frame = get_data_frame([current_doc], data_frame_spec)
        trend_frame = get_data_frame(trend_docs, data_frame_spec)

        measurement_series.append(
            MeasurementSeries(
                info=measurement, trend=trend_frame, current=current_test_frame
            )
        )

    introduction = intro(filters, commit_sha, [current_doc], trend_docs)

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


def get_commit_info(docs):
    if docs is None or len(docs) == 0:
        return None, None, None
    last_doc = docs[-1]
    commit_date = jmespath.search(
        "metadata.labels[?name=='commit_date'].value|[0]", last_doc
    )
    sha = jmespath.search("metadata.labels[?name=='commit_sha'].value|[0]", last_doc)
    run_date = jmespath.search("context.run.startTimestamp", last_doc)
    return commit_date, sha, run_date


def intro(
    filters: List[Tuple[str, str]], git_sha: str, current_docs, trend_docs
) -> str:
    if len(current_docs) == 0:
        current_doc_info = f"Test for commit:'{git_sha}' not found"
    else:
        commit_date, sha, run_date = get_commit_info(current_docs)
        t_commit_date, t_sha, t_run_date = get_commit_info(trend_docs)

        current_doc = current_docs[-1]
        commit_date = jmespath.search(
            "metadata.labels[?name=='commit_date'].value|[0]", current_doc
        )
        run_date = jmespath.search("context.run.startTimestamp", current_doc)

        dashboard_link = jmespath.search("results.data.dashboard_link", current_doc)
        argo_link = jmespath.search("context.argo.workflowUrl", current_doc)
        current_doc_info = f"""
**commit:** '{sha}'

**commit date:** '{commit_date}'

**ran at:** '{run_date}'

## Trend info:

**commit:** '{t_sha}'

**commit date:** '{t_commit_date}'

**ran at:** '{t_run_date}'

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


def last_release_page(description: str, measurement_series: List[MeasurementSeries]):
    intro = f"""
{description}
# Last Release

Last release stats

"""
    blocks = [intro]
    for series in measurement_series:
        info = series.info
        if info.description is not None:
            description = info.description
        else:
            if info.unit is not None:
                description = f"{info.name} in ({info.unit})"
        series_intro = f"## {description}"
        blocks.append(series_intro)
        aggregations_id = [agg.id for agg in info.aggregations]
        trend = get_last(series.trend, aggregations_id)
        current = get_last(series.current, aggregations_id)
        widgets = []
        for aggregation in info.aggregations:
            widgets.append(
                big_number(
                    heading=aggregation.name,
                    current=current.get(aggregation.id),
                    previous=trend.get(aggregation.id),
                    bigger_is_better=info.bigger_is_better,
                )
            )
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
        info = series.info
        description = info.description if info.description is not None else info.name
        if info.unit is not None:
            unit = f"{info.unit}"
        else:
            unit = ""
        blocks.append(f"## {description}\n\n")
        plot = trend_plot(
            series.trend,
            x=alt.X("commit_date:T", axis=alt.Axis(title="Commit Date")),
            y=alt.Y("value:Q", axis=alt.Axis(title=unit)),
            time_series="measurement:N",
            split_by="test_name",
            title=info.name,
        )
        blocks.append(plot)

    return dp.Page(
        title="Trends",
        blocks=blocks,
    )
