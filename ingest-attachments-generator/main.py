import datetime
from typing import Optional
import time

import click
from confluent_kafka import Producer
from yaml import load, Loader

from messages import generate_event_messages, generate_attachment_payload
from util import parse_timedelta
from readme_generator import generate_readme


@click.command()
@click.option(
    "--num-events",
    "-n",
    default="",
    help="The number of events to send to the kafka queue",
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
    help="Kafka broker address and port (e.g. localhost:9092)",
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
@click.option("--org", "-o", type=int, help="organization id")
@click.option("--project", "-p", type=int, help="project id")
@click.option("--dry-run", is_flag=True, help="if set only prints the settings")
@click.option("--update-docs", is_flag=True,  help="creates a README.md  documentation file")
def main(**kwargs):
    """
    Populates the ingest-metrics kafka topic with messages
    """
    if kwargs["update_docs"]:
        generate_readme()
        return

    settings = get_settings(**kwargs)

    print("Settings:")
    print(settings)

    if kwargs["dry_run"]:
        return

    producer = get_kafka_producer(settings)

    print("Generating attachment data...", flush=True)

    payload = generate_attachment_payload(settings)

    print("Sending data...", flush=True)
    send_messages(producer, settings, payload)

    print("Done!")


def send_messages(producer, settings, payload):
    topic_name = settings["topic_name"]
    num_events = settings["num_events"]

    for idx in range(num_events):
        for message in generate_event_messages(idx, settings, payload):
            producer.produce(topic_name, message)
            producer.poll(0)

    producer.flush()


def get_settings(
    num_events: Optional[str],
    settings_file: Optional[str],
    topic_name: Optional[str],
    broker: Optional[str],
    org: Optional[int],
    project: Optional[int],
    dry_run: bool,
    **kwargs,
):
    # default settings
    settings = {
        "num_events": 100,
        # attachments is the most defensive default, since this topic allows all
        # message types.
        "topic_name": "ingest-attachments",
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

    # num_events may be set to a string value (when started from kubernetes) like 'default'
    # if set in the command line to anything that can't be converted to an integer just ignore it
    for name, value in (
        ("num_events", num_events),
        # NB: Add other numeric settings here
    ):
        if value is not None:
            try:
                settings[name] = int(value)
            except ValueError:
                pass  # ignore non integer command line args

    time_delta = parse_timedelta(settings["spread"])
    if time_delta is None:
        time_delta = datetime.timedelta(minutes=1)

    settings["time_delta"] = time_delta

    settings["dry_run"] = dry_run

    return settings


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