import io
import json
import os
from datetime import timedelta
from dateutil import parser
from enum import Enum, unique

import click
import yaml
from influx_stats import get_stats, TestingProfile, Report, TestRun

from util import to_optional_datetime, parse_timedelta

# Suitable for use with port forwarding, e.g. "sentry-kube kubectl port-forward service/influxdb 8087:80"
INFLUX_URL = "http://localhost:8087/"

MIN_REQUIREMENTS_MESSAGE = "Either multistage or at least two parameters from (start, stop, duration) must be specified."


@unique
class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


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
    required=True,
    help="Testing profile",
)
def main(
    start, end, duration, token, url, org, report_file_input, format, out, profile
):
    start_time = None
    if start is not None:
        start_time = parser.parse(start)

    end_time = None
    if end is not None:
        end_time = parser.parse(end)

    if report_file_input is None:
        if start_time is None and end_time is None:
            raise click.UsageError(MIN_REQUIREMENTS_MESSAGE)

        if start_time is None or end_time is None:
            if duration is None:
                raise click.UsageError(MIN_REQUIREMENTS_MESSAGE)
            else:
                duration_interval = parse_timedelta(duration)
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
    else:
        report = load_report(report_file_input)

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

    # we have a valid start & stop time
    stats = get_stats(
        report=report,
        url=url,
        token=token,
        org=org,
        profile=profile,
    )

    formatter = get_formatter(format)

    result = formatter.format(stats)

    if out is not None:
        with open(out, "wt") as o:
            print(result, file=o)
        print(f"Result written to: {out}")
        text_formatter = TextFormatter()
        print(text_formatter.format(stats))
    else:
        print(result)


# Note just crash if we don't get the proper yaml doc
def load_report(file_name: str) -> Report:
    with open(file_name, "r") as f:
        doc = yaml.load(f, Loader=yaml.Loader)

    test_runs = []

    for raw_test_run in doc["testRuns"]:
        test_info = raw_test_run["runInfo"]
        name = test_info.get("name")
        description = test_info.get("description")
        runner = test_info.get("runner")
        duration = parse_timedelta(test_info.get("duration"))
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


def get_formatter(req_format: str):
    if req_format == OutputFormat.TEXT.value:
        return TextFormatter()
    elif req_format == OutputFormat.JSON.value:
        return JsonFormatter()
    elif req_format == OutputFormat.YAML.value:
        return YamlFormatter()
    else:
        return TextFormatter()


class TextFormatter:
    def format(self, report: Report) -> str:
        output = io.StringIO()
        base_indent = "  "
        for test_run in report.test_runs:
            level = 0
            print(f"\nTest run {test_run.name} ", file=output)
            level = 1
            indent = base_indent * level
            print(
                f"\n{indent} start:{to_optional_datetime(test_run.start_time)} end:{to_optional_datetime(test_run.end_time)}",
                file=output,
            )

            print(f"\n{indent}spec:", file=output)
            level = 2
            indent = base_indent * level
            spec = yaml.dump(test_run.spec, indent=2, default_flow_style=False)
            spec = spec.replace("\n", f"\n{indent}")
            print(f"\n{indent}{spec}", file=output)

            for stat in test_run.metrics:
                level = 3
                indent = base_indent * level
                print(f"{indent}{stat.name}", file=output)
                for metric_value in stat.values:
                    params = ", ".join(metric_value.attributes)
                    if metric_value.value is not None:
                        s = "{}{:>16} -> {:.2f}".format(
                            indent, params, metric_value.value
                        )
                    else:
                        s = "{}{:>16} -> Empty".format(indent, params)
                    print(s, file=output)
                print(f"{indent}" + "-" * 32, file=output)
        ret_val = output.getvalue()
        output.close()
        return ret_val


class JsonFormatter:
    def format(self, report: Report) -> str:
        result = report.to_dict()
        return json.dumps(result, indent=2)


class YamlFormatter:
    def format(self, report: Report) -> str:
        result = report.to_dict()
        return yaml.dump(result, indent=2, default_flow_style=False)


if __name__ == "__main__":
    main()
