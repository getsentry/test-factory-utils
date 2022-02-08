import datetime
import json
from typing import Mapping, Any, Optional
import time

import click
from confluent_kafka import Producer
from yaml import load, dump, Dumper, Loader

from metrics import generate_metric
from util import parse_timedelta


@click.command()
@click.option(
    "--num-messages",
    "-n",
    default="",
    help="The number of messages to send to the kafka queue",
)
@click.option(
    "--settings-file", "-f", default=None, help="The settings file name (json or yaml)"
)
@click.option(
    "--topic-name", "-t", default=None, help="The name of the ingest metrics topic"
)
@click.option(
    "--broker",
    "-b",
    default=None,
    help="the kafka broker address and port (e.g. localhost:9092)",
)
@click.option(
    "--repeatable",
    "-r",
    is_flag=True,
    help="Should it generate a repeatable load or use a random generator (default: random)",
)
@click.option(
    "--timestamp",
    type=int,
    help="Timestamp reference to use. If exactly repeatable tests are desired then a timestamp ref can be used",
)
@click.option(
    "--spread",
    "-s",
    help="Time spread from timestamp backward, (e.g. 1w2d3h4m5s 1 week 2 days 3 hours 4 minutes 5 seconds)",
)
@click.option("--org", "-o", type=int, help="organisation id")
@click.option("--project", "-p", type=int, help="project id")
@click.option("--releases", default="", help="number of releases to generate")
@click.option(
    "--col-min",
    type=int,
    help="min number of items in collections (sets & distributions)",
)
@click.option(
    "--col-max",
    type=int,
    help="max number of items in collections (sets & distributions)",
)
@click.option("--environments", default="", help="number of environments to generate")
@click.option("--dry-run", is_flag=True, help="if set only prints the settings")
def main(**kwargs):
    """
    Populates the ingest-metrics kafka topic with messages
    """
    settings = get_settings(**kwargs)

    print("Settings:")
    print(settings)

    if kwargs["dry_run"]:
        return

    producer = get_kafka_producer(settings)

    print("Sending data...")
    send_metrics(producer, settings)

    print("Done!")


def send_metrics(producer, settings):
    topic_name = settings["topic_name"]
    for metric in generate_metrics(settings):
        producer.produce(topic_name, json.dumps(metric))
        producer.poll(0)

    producer.flush()


def generate_metrics(settings):
    num_messages = settings["num_messages"]

    for idx in range(num_messages):
        yield generate_metric(idx, settings)


def get_settings(
    num_messages: Optional[str],
    settings_file: Optional[str],
    topic_name: Optional[str],
    broker: Optional[str],
    repeatable: bool,
    org: Optional[int],
    project: Optional[int],
    timestamp: Optional[int],
    spread: Optional[str],
    releases: Optional[str],
    environments: Optional[str],
    col_min: Optional[int],
    col_max: Optional[int],
    dry_run: bool
):
    # default settings
    settings = {
        "num_messages": 100,
        "topic_name": "ingest-metrics",
        "repeatable": False,
        "spread": "2m",
        "releases": 1,
        "environments": 1,
        "col_min": 1,
        "col_max": 1,
        "kafka": {},
        "metric_types": {},
    }

    if settings_file is not None:
        try:
            with open(settings_file, "rt") as f:
                settings.update(load(f, Loader=Loader))
        except:
            raise click.UsageError(f"Could not parse settings file {settings_file}")

    if topic_name is not None:
        settings["topic_name"] = topic_name

    if repeatable:
        settings["repeatable"] = True

    if broker is not None:
        settings["kafka"]["bootstrap.servers"] = broker

    if org is not None:
        settings["org"] = org

    if project is not None:
        settings["projects"] = [project]

    if settings["kafka"].get("bootstrap.servers") is None:
        raise click.UsageError(
            f"Kafka broker was not specified, to specify either use --broker argument or set [kafka][bootstrap.servers] in the settings file"
        )

    if settings.get("org") is None:
        raise click.UsageError(
            f"Organization was not specified, to specify either use --org argument or set [org] in the settings file"
        )

    if settings.get("projects") is None:
        raise click.UsageError(
            f"projects not specified, to specify either use --project argument or set [project] array in the settings file"
        )

    if timestamp is not None:
        settings["timestamp"] = timestamp
    else:
        settings["timestamp"] = int(time.time()) - 1  # now(ish)

    # num_messages, environment and releases may be set to a string value (when started from kubernetes) like 'default'
    # if set in the command line to anything that can't be converted to an integer just ignore it
    for name, value in (("num_messages", num_messages), ("releases", releases), ("environments", environments)):
        if value is not None:
            try:
                settings[name] = int(value)
            except ValueError:
                pass  # ignore non integer command line args

    if col_min is not None:
        settings["col_min"] = col_min

    if col_max is not None:
        settings["col_max"] = col_max

    if spread is not None:
        settings["spread"] = spread

    time_delta = parse_timedelta(settings["spread"])
    if time_delta is None:
        time_delta = datetime.timedelta(minutes=1)

    settings["time_delta"] = time_delta

    settings["dry_run"] = dry_run

    _calculate_metrics_distribution(settings)
    return settings


def _calculate_metrics_distribution(settings):
    """
    Creates a helper array that has precalculated distributions for various metric types

    Example:
    If original metric types relative distributions are: { "metric-1": 3, "metric-2": 1, "metric-3": 5 }
    The calculated metric distribution will be: dist= [ ("metric-1", 3), ("metric-2", 4), ("metric-3": 9)]
    Use the array like this:
    idx = random.randint(1, dist[len(dist)-1][1])
    for d in dist:
        if idx <= d[1]:
            return d[0]
    return None
    """
    dist = []
    count = 0
    for k, v in settings["metric_types"].items():
        count += v
        dist.append((k, count))

    settings["metric_distribution"] = dist


def get_fake_kafka_producer(settings):
    """
    A fake producer that just dumps to console (for testing)
    """

    class FakeProducer:
        def __init__(self, settings):
            pass

        def produce(self, topic_name, message):
            print(message)

        def flush(self):
            print("Flushing !!! ")

    return FakeProducer(settings)


def get_kafka_producer(settings):
    """
    Returns a kafka producer configured with the
    settings found in the settings["kafka"] sub-object

    At a minimum the settings should contain:
        bootstrap.server: host-name:port-number
    """
    kafka_settings = settings["kafka"]
    return Producer(kafka_settings)


if __name__ == "__main__":
    main()
