import os
from datetime import timedelta
from dateutil import parser

import click
import yaml
from influxdb_client import InfluxDBClient

from influx_stats import get_stats_with_static_profile, TestingProfile, Report, TestRun
from util import parse_timedelta
from formatters import get_formatter, OutputFormat

# Suitable for use with port forwarding, e.g. "sentry-kube kubectl port-forward service/influxdb 8087:80"
INFLUX_URL = "http://localhost:8087/"

MIN_REQUIREMENTS_MESSAGE = "Either multistage or at least two parameters from (start, stop, duration) must be specified."


@click.command()
@click.option("--start", "-s", default=None, help="The start datetime of the test")
@click.option("--end", "-e", default=None, help="The stop date time of the test")
@click.option("--duration", "-d", default=None, help="The test duration e.g. 2d4h3m2s")
@click.option(
    "--url", "-u", default=None, help="Url InfluxDb, if None $INFLUX_URL will be used"
)
@click.option(
    "--token",
    "-t",
    default=None,
    help="Access token for InfluxDb, if None $INFLUX_TOKEN will be used",
)
@click.option("--org", "-o", default="sentry", help="Organization used in InfluxDb")
@click.option(
    "--report-file-input",
    "-r",
    default=None,
    help="Name of the input file containing a report generated by load-starter. Stats collector will be "
    "run on each test run in the report. See load-starter doc for details",
)
@click.option(
    "--query-file-input",
    "-q",
    default=None,
    help="Name of the input file containing query specifications",
)
@click.option(
    "--format",
    "-f",
    default="text",
    type=click.Choice([format.value for format in OutputFormat]),
    help="Select the output format",
)
@click.option(
    "--out",
    "-O",
    default=None,
    help="File name for output, if not specified stdout will be used",
)
@click.option(
    "--profile",
    "-p",
    type=click.Choice(TestingProfile.values()),
    help="Testing profile",
)
def main(
    start,
    end,
    duration,
    token,
    url,
    org,
    report_file_input,
    query_file_input,
    format,
    out,
    profile,
):
    if query_file_input and profile:
        raise click.UsageError("You specified both query file and profile, exiting!")

    start_time = None
    if start is not None:
        start_time = parser.parse(start)

    end_time = None
    if end is not None:
        end_time = parser.parse(end)

    if token is None:
        token = os.getenv("INFLUX_TOKEN")
        if not token:
            raise click.UsageError(
                "INFLUX_TOKEN not provided.\n"
                "Set INFLUX_TOKEN environment variable or provide --token command line argument"
            )

    if url is None:
        url = os.getenv("INFLUX_URL")
        if url is None:
            url = INFLUX_URL

    if report_file_input:
        report = load_report_from_load_starter(report_file_input)
    else:
        # No input files provided, take the start/end times from CLI
        if start_time is None and end_time is None:
            raise click.UsageError(MIN_REQUIREMENTS_MESSAGE)

        if start_time is None or end_time is None:
            if duration is None:
                raise click.UsageError(MIN_REQUIREMENTS_MESSAGE)
            else:
                duration_interval = parse_timedelta(duration)
                assert duration_interval, "Invalid duration"
            if start_time is None:
                assert end_time is not None
                start_time = end_time - duration_interval
            else:
                end_time = start_time + duration_interval
        report = Report(
            start_time=start_time,
            end_time=end_time,
            test_runs=[
                TestRun(
                    start_time=start_time,
                    end_time=end_time,
                    duration=end_time - start_time,
                    name="CLI report",
                    description="CLI report",
                    runner="unknown",
                    spec={},
                    metrics=[],
                )
            ],
        )

    client = InfluxDBClient(url=url, token=token, org=org)

    stats = get_stats_with_static_profile(
        report=report,
        profile=profile,
        client=client,
    )

    ### Format and output the results
    formatter = get_formatter(format)
    result = formatter.format(stats)
    if out is not None:
        with open(out, "wt") as o:
            print(result, file=o)
        print(f"Result written to: {out}")
        text_formatter = get_formatter(OutputFormat.TEXT)
        print(text_formatter.format(stats))
    else:
        print(result)


def load_report_from_load_starter(file_name: str) -> Report:
    with open(file_name, "r") as f:
        doc = yaml.load(f, Loader=yaml.Loader)

    test_runs = []

    for raw_test_run in doc["testRuns"]:
        test_info = raw_test_run["runInfo"]
        name = test_info.get("name")
        description = test_info.get("description")
        runner = test_info.get("runner")
        duration = parse_timedelta(test_info.get("duration"))
        assert duration, "Invalid duration"
        spec = test_info.get("spec")
        start_time = raw_test_run["startTime"]
        if type(start_time) == str:
            start_time = parser.parse(start_time)
        end_time = raw_test_run["endTime"]
        if type(end_time) == str:
            end_time = parser.parse(end_time)

        # If the testing period is big enough, cut off the start and end
        CUTOFF_SECONDS = 30
        # A two-minutes-long test will already benefit from this
        CUTOFF_MIN_DURATION_SECONDS = 115
        if end_time - start_time >= timedelta(seconds=CUTOFF_MIN_DURATION_SECONDS):
            end_time = end_time - timedelta(seconds=CUTOFF_SECONDS)
            start_time = start_time + timedelta(seconds=CUTOFF_SECONDS)

        test_run = TestRun(
            start_time=start_time,
            end_time=end_time,
            name=name,
            description=description,
            duration=duration,
            runner=runner,
            spec=spec,
            metrics=[],
        )
        test_runs.append(test_run)

    start_time = doc["startTime"]
    if type(start_time) == str:
        start_time = parser.parse(start_time)
    end_time = doc["endTime"]
    if type(end_time) == str:
        end_time = parser.parse(end_time)

    return Report(start_time=start_time, end_time=end_time, test_runs=test_runs)


if __name__ == "__main__":
    main()
