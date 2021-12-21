import io
from typing import Sequence
import os
import json

from dateutil import parser
import click

import util
from influx_stats import get_stats, MetricSummary

INFLUX_TOKEN = "JM4AJhWwUcAFLXv4b3MP_odVqCj07ssqu7Sp2FG_KJO-H0qjxFVlAIJxlmWIlIOxXC3wG1rFA0bZRV59X_tHcQ=="  # local admin token
INFLUX_TOKEN = "kOcdxZtSCrPtUNrNUwedanLj1K35uA_Unopv782_BVALznr60s5CkajiXOwSr21klYqWN7g46WZdTlziYmUfdw=="  # test server admin token

INFLUX_URL = 'http://localhost:8086/'  # this is local
INFLUX_URL = 'https://influxdb.testa.getsentry.net/'  # this needs gcloud auth
INFLUX_URL = 'http://localhost:8087/'  # this needs port forwarding sentry-kube kubectl port-forward service/influxdb 8087:80



@click.command()
@click.option('--start', '-s', default=None, help='The start datetime of the test')
@click.option('--end', '-e', default=None, help='The stop date time of the test')
@click.option('--duration', '-d', default=None, help='The test duration e.g. 2d4h3m2s')
@click.option('--url', '-u', default=None, help="Url InfluxDb, if None $INFLUX_URL will be used")
@click.option('--token', '-t', default=None, help="Access token for InfluxDb, if None $INFLUX_TOKEN will be used")
@click.option("--org", '-o', default="sentry", help="Organization used in InfluxDb")
@click.option("--format", '-f', default="text", type=click.Choice(["text", "json"]), help="Select the output req_format")
def main(start, end, duration, token, url, org, format):
    """Simple program that greets NAME for a total of COUNT times."""

    start_time = None
    if start is not None:
        start_time = parser.parse(start)

    end_time = None
    if end is not None:
        end_time = parser.parse(end)

    min_requirements_message = "At least two parameters from start, stop and duration must be specified"

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
        start_time=start_time,
        end_time=end_time,
        url=url,
        token=token,
        org=org,
    )

    formatter = get_formatter(format)
    print(formatter.format(stats))


def get_formatter(req_format: str):
    if req_format == "text":
        return TextFormatter()
    elif req_format == "json":
        return JsonFormatter()
    else:
        return TextFormatter()


class TextFormatter:
    def format(self, stats: Sequence[MetricSummary]) -> str:
        output = io.StringIO()
        for stat in stats:
            print(f"{stat.name}", file=output)
            for metric_value in stat.values:
                params = ", ".join(metric_value.attributes)
                s = "{:>16} -> {:.2f}".format(params, metric_value.value)
                print(s, file=output)
            print("-" * 32, file=output)
        ret_val = output.getvalue()
        output.close()
        return ret_val


class JsonFormatter:
    def format(self, stats: Sequence[MetricSummary]) -> str:
        result = []
        for stat in stats:
            values = []
            elm = {
                "name": stat.name,
                "values": values
            }
            for metric_value in stat.values:
                attributes= [val for val in metric_value.attributes]
                metric_value = {
                    "attributes": attributes,
                    "value": metric_value.value
                }
                values.append(metric_value)
            result.append(elm)
        return json.dumps(result, indent=2)


if __name__ == '__main__':
    main()
