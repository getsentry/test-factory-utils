import io
from datetime import timedelta
from typing import Sequence, List
import os
import json

from dateutil import parser
from influx_stats import get_stats, Stage, StageType, StageStep
import click
import yaml

from util import to_optional_datetime, parse_timedelta

# INFLUX_URL = 'http://localhost:8086/'  # this is local
# INFLUX_URL = 'https://influxdb.testa.getsentry.net/'  # this needs gcloud auth
INFLUX_URL = 'http://localhost:8087/'  # this needs port forwarding sentry-kube kubectl port-forward service/influxdb 8087:80


@click.command()
@click.option('--start', '-s', default=None, help='The start datetime of the test')
@click.option('--end', '-e', default=None, help='The stop date time of the test')
@click.option('--duration', '-d', default=None, help='The test duration e.g. 2d4h3m2s')
@click.option('--url', '-u', default=None, help="Url InfluxDb, if None $INFLUX_URL will be used")
@click.option('--token', '-t', default=None, help="Access token for InfluxDb, if None $INFLUX_TOKEN will be used")
@click.option("--org", '-o', default="sentry", help="Organization used in InfluxDb")
@click.option("--multistage", "-m", default=None, help="File name for multistage run result. Will generate multistage result")
@click.option("--format", '-f', default="text", type=click.Choice(["text", "json", "yaml"]), help="Select the output req_format")
@click.option("--out", '-O', default=None, help="File name for output, if not specified stdout will be used")
def main(start, end, duration, token, url, org, multistage, format, out):
    """Simple program that greets NAME for a total of COUNT times."""

    start_time = None
    if start is not None:
        start_time = parser.parse(start)

    end_time = None
    if end is not None:
        end_time = parser.parse(end)

    min_requirements_message = "Either multistage or at least two parameters from (start, stop, duration) must be specified."

    if multistage is None:
        if start_time is None and end_time is None:
            raise click.UsageError(min_requirements_message)

        if start_time is None or end_time is None:
            if duration is None:
                raise click.UsageError(min_requirements_message)
            else:
                duration_interval = parse_timedelta(duration)
            if start_time is None:
                assert end_time is not None
                start_time = end_time - duration_interval
            else:
                end_time = start_time + duration_interval
        stages = [

            Stage(
                type=StageType.static,
                name="legacy",
                steps=[
                    StageStep(
                        start_time=start_time,
                        end_time=end_time,
                        metrics=[],
                        users=None,
                    )
                ]
            )
        ]

    else:
        stages = get_stages_from_report(multistage)

    if token is None:
        token = os.getenv("INFLUX_TOKEN")
        if not token:
            raise click.UsageError("INFLUX_TOKEN not provided.\n"
                                   "Set INFLUX_TOKEN environment variable or provide --token command line argument")

    if url is None:
        url = os.getenv("INFLUX_URL")
        if url is None:
            url = INFLUX_URL

    # we have a valid start & stop time
    stats = get_stats(
        stages,
        url=url,
        token=token,
        org=org,
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
def get_stages_from_report(multi_report_file_name: str) -> List[Stage]:
    with open(multi_report_file_name, "r") as f:
        ret_val = yaml.load(f, Loader=yaml.Loader)

    # convert startTime, endTime to date
    reports = ret_val["stageReports"]
    ret_val = []
    for report in reports:
        name = report.get("name")
        t = report.get("stageType")
        stage_type = StageType.from_str(t)

        steps = []
        for step in report["steps"]:
            start_time = step["startTime"]
            if type(start_time) == str:
                start_time = parser.parse(start_time)
            end_time = step["endTime"]
            if type(end_time) == str:
                end_time = parser.parse(end_time)
            users = step.get("users")
            if end_time - start_time > timedelta(minutes=2):
                end_time = end_time - timedelta(minutes=1)
                start_time = start_time + timedelta(minutes=1)

            stage_step = StageStep(start_time=start_time, end_time=end_time, users=users, metrics=[])
            steps.append(stage_step)
        stage = Stage(name=name, type=stage_type, steps=steps)
        ret_val.append(stage)
    return ret_val


def get_formatter(req_format: str):
    if req_format == "text":
        return TextFormatter()
    elif req_format == "json":
        return JsonFormatter()
    elif req_format == "yaml":
        return YamlFormatter()
    else:
        return TextFormatter()


class TextFormatter:
    def format(self, stages: Sequence[Stage]) -> str:
        output = io.StringIO()
        base_indent = "  "
        for stage in stages:
            level = 0
            print(f"\nStage {stage.name} of type: {stage.type.value}", file=output)

            for step in stage.steps:
                level = 1
                indent = base_indent * level
                print(f"\n{indent}Step start:{to_optional_datetime(step.start_time)} end:{to_optional_datetime(step.end_time)} users:{step.users}", file=output)
                for stat in step.metrics:
                    level = 3
                    indent = base_indent * level
                    print(f"{indent}{stat.name}", file=output)
                    for metric_value in stat.values:
                        params = ", ".join(metric_value.attributes)
                        if metric_value.value is not None:
                            s = "{}{:>16} -> {:.2f}".format(indent, params, metric_value.value)
                        else:
                            s = "{}{:>16} -> Empty".format(indent, params)
                        print(s, file=output)
                    print(f"{indent}" + "-" * 32, file=output)
        ret_val = output.getvalue()
        output.close()
        return ret_val


class JsonFormatter:
    def format(self, stages: Sequence[Stage]) -> str:
        result = [stage.to_dict() for stage in stages]
        return json.dumps(result, indent=2)


class YamlFormatter:
    def format(self, stages: Sequence[Stage]) -> str:
        result = [stage.to_dict() for stage in stages]
        return yaml.dump(result, indent=2, default_flow_style=False)


if __name__ == '__main__':
    main()
