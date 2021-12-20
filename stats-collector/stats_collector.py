import io
from typing import Sequence
import os

from dateutil import parser
import click

import util
from influx_stats import get_stats, MetricSummary

@click.command()
@click.option('--start', '-s', default=None, help='The start datetime of the test')
@click.option('--end', '-e', default=None, help='The stop date time of the test')
@click.option('--duration', '-d', default=None, help='The test duration e.g. 2d4h3m2s')
@click.option('--url', '-u', default=None, help="Url InfluxDb, if None $INFLUX_URL will be used")
@click.option('--token', '-t', default=None, help="Access token for InfluxDb, if None $INFLUX_TOKEN will be used")
@click.option("--org", '-o', default="sentry", help="Organization used in InfluxDb")
def main(start, end, duration, token, url, org):
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
            raise click.UsageError("Missing auth token either use --token or INFLUX_TOKEN env var")

    if url is None:
        url = os.getenv("INFLUX_URL")
        if url is None:
            raise click.UsageError("Missing InfluxDb URL eiter use --rul or INFLUX_URL env var")

    # we have a valid start & stop time
    stats = get_stats(
        start_time=start_time,
        end_time=end_time,
        url=url,
        token=token,
        org=org,
    )

    formatter = TextFormatter(stats)
    print(formatter.format())


class TextFormatter:
    def __init__(self, stats: Sequence[MetricSummary]):
        self.stats = stats

    def format(self) -> str:
        output = io.StringIO()
        for stat in self.stats:
            print(f"{stat.name}", file=output)
            for metric_value in stat.values:
                params = ", ".join(metric_value.attributes)
                s = "{:>16} -> {}".format(params,metric_value.value)
                print(s, file=output)
            print("-" * 32, file=output)
        ret_val = output.getvalue()
        output.close()
        return ret_val


if __name__ == '__main__':
    main()
