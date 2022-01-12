import io
from typing import Sequence, List
import os
import json

from dateutil import parser
from influx_stats import get_stats, Stage, StageType, StageStep
import click
import yaml

from util import to_optional_datetime

INFLUX_TOKEN = "JM4AJhWwUcAFLXv4b3MP_odVqCj07ssqu7Sp2FG_KJO-H0qjxFVlAIJxlmWIlIOxXC3wG1rFA0bZRV59X_tHcQ=="  # local admin token
# INFLUX_TOKEN = "kOcdxZtSCrPtUNrNUwedanLj1K35uA_Unopv782_BVALznr60s5CkajiXOwSr21klYqWN7g46WZdTlziYmUfdw=="  # test server admin token

INFLUX_URL = 'http://localhost:8086/'  # this is local


# INFLUX_URL = 'https://influxdb.testa.getsentry.net/'  # this needs gcloud auth
# INFLUX_URL = 'http://localhost:8087/'  # this needs port forwarding sentry-kube kubectl port-forward service/influxdb 8087:80


@click.command()
@click.option('--start', '-s', default=None, help='The start datetime of the test')
@click.option('--end', '-e', default=None, help='The stop date time of the test')
@click.option('--duration', '-d', default=None, help='The test duration e.g. 2d4h3m2s')
@click.option('--url', '-u', default=None, help="Url InfluxDb, if None $INFLUX_URL will be used")
@click.option('--token', '-t', default=None, help="Access token for InfluxDb, if None $INFLUX_TOKEN will be used")
@click.option("--org", '-o', default="sentry", help="Organization used in InfluxDb")
@click.option("--multistage", "-m", default=None, help="File name for multistage run result. Will generate multistage result")
@click.option("--format", '-f', default="text", type=click.Choice(["text", "json"]), help="Select the output req_format")
def main(start, end, duration, token, url, org, multistage, format):
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
                duration_interval = util.parse_timedelta(duration)
            if start_time is None:
                assert end_time is not None
                start_time = end_time - duration_interval
            else:
                end_time = start_time + duration_interval
        stages = {
            "stageReports": [
                {
                    "steps": [
                        {
                            "startTime": start_time,
                            "endTime": end_time
                        }
                    ],
                    "name": "",
                    "stageType": "static"
                }
            ]
        }
    else:
        stages = get_stages_from_report(multistage)

    if token is None:
        token = os.getenv("INFLUX_TOKEN")
        if token is None:
            token = INFLUX_TOKEN

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
    print(formatter.format(stats))


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
    else:
        return TextFormatter()


class TextFormatter:
    def format(self, stages: Sequence[Stage]) -> str:
        output = io.StringIO()
        base_indent = "  "
        for stage in stages:
            level = 0
            print(f"Stage {stage.name} of type: {stage.type.value}", file=output)

            for step in stage.steps:
                level = 1
                indent = base_indent * level
                print(f"{indent}Step start:{to_optional_datetime(step.start_time)} end:{to_optional_datetime(step.end_time)} users:{step.users}", file=output)
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


if __name__ == '__main__':
    main()
