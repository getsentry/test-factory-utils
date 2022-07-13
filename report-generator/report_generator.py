from typing import Mapping, List, Tuple
from datetime import datetime

import datapane as dp

from google.cloud import storage
import click

from mongo_data import get_db, get_docs
import jmespath

from sdk_performance_datasets import get_cpu_usage, get_ram_usage
from report_generator_graphs import trend_plot


@click.command()
@click.option("--mongo-db", "-m", "mongo_url", envvar='MONGO_DB', required=True, help="url of mongo db (something like: 'mongodb://mongo-server/27017')")
@click.option("--gcs-bucket-name", "-b", 'bucket_name', envvar='GCS_BUCKET_NAME', default="sentry-testing-bucket-test-sdk-reports", help="GCS bucket name for saving the report")
@click.option("--report-name", "-r", envvar="REPORT_NAME", default="report.html", help="path to the name of the report file")
@click.option("--filters", "-f", multiple=True, type=(str, str))
@click.option("--git-sha", "-s", envvar="REFERENCE_SHA", required=True, help="the git sha of the version of interest")
def main(mongo_url, bucket_name, report_name, filters, git_sha):
    db = get_db(mongo_url)

    trend_filters = [*filters, ("is_default_branch", "1")]
    current_filters = [*filters, ("commit_sha", git_sha)]

    trend_docs = get_docs(db, trend_filters)
    current_docs = get_docs(db, current_filters)

    # we only need the last doc
    current_docs = current_docs[-1:]

    cpu_usage_trend = get_cpu_usage(trend_docs)
    cpu_usage_current = get_cpu_usage(current_docs)

    ram_usage_trend = get_ram_usage(trend_docs)
    ram_usage_current = get_ram_usage(current_docs)

    report = dp.Report(
        about_page(filters, git_sha, current_docs),
        trends_page(cpu_usage_trend, ram_usage_trend),
        last_release_page(cpu_usage_trend, cpu_usage_current, ram_usage_trend, ram_usage_current),
    )

    environment = "unknown-environment"
    platform = "unknown-platform"

    for key,value in filters:
        if key == 'environment':
            environment = value
        if key == 'platform':
            platform = value

    report.save(report_name, formatting=dp.ReportFormatting(width=dp.ReportWidth.MEDIUM))
    upload_to_gcs(report_name, environment, platform, bucket_name)


def upload_to_gcs(file_name, environment, platform, bucket_name):
    date_s = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    blob_file_name = f"{platform}/{environment}/sdk_report_{date_s}.html"
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_file_name)

    with open(file_name, "rb") as my_file:
        blob.upload_from_file(my_file, content_type="text/html")
    print(f"Uploaded to GCS at: https://storage.cloud.google.com/{bucket_name}/{blob_file_name}")


def get_last(dataframe, measurements) -> Mapping[str, float]:
    ret_val = {}
    for measurement in measurements:
        vals = dataframe[dataframe['measurement'].isin([measurement])]
        if len(vals) > 0:
            ret_val[measurement] = vals.iloc[-1].value
    return ret_val


def about_page(filters: List[Tuple[str, str]], git_sha: str, current_docs):
    if len(current_docs) == 0:
        current_doc_info = f"Test for commit:'{git_sha}' not found"
    else:
        current_doc = current_docs[-1]
        commit_date = jmespath.search("metadata.labels[?name=='commit_date'].value|[0]", current_doc)
        run_date = jmespath.search("context.run.startTimestamp", current_doc)
        current_doc_info = f"""
**commit:** '{git_sha}'

**commit date:** '{commit_date}'

**ran at:** '{run_date}'
                
"""

    filters_used = ""
    for name, value in filters:
        filters_used += f"**{name}**='{value}'\n\n"

    content = f"""
# About SDK report

## Filters used:
{filters_used}

## Current document info:
{current_doc_info}
"""
    return dp.Page(
        title="About",
        blocks=[content]
    )


def last_release_page(cpu_usage_trend, cpu_usage_current, ram_usage_trend, ram_usage_current):
    intro = """
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
        memory_widgets.append(big_number(
            heading=measurement,
            current=memory_current.get(measurement),
            previous=memory_trend.get(measurement),
            bigger_is_better=False))

        cpu_widgets.append(big_number(
            heading=measurement,
            current=cpu_current.get(measurement),
            previous=cpu_trend.get(measurement),
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
            is_upward_change=upward_change
        )
    else:
        return dp.BigNumber(heading=heading,
                            value=f"{current:.{4}}" if current is not None else "No Value",
                            prev_value=f"{previous:.{4}}" if previous is not None else "No Value",
                            )


if __name__ == '__main__':
    main()
