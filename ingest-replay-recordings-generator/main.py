import datetime
import json
from typing import Mapping, Any, Optional
import time
import random

import click
from confluent_kafka import Producer
from yaml import load, dump, Dumper, Loader

from recordings import generate_message
from readme_generator import generate_readme


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
    "--topic-name", "-t", default=None, help="The name of the ingest replay recordings topic"
)
@click.option(
    "--broker",
    "-b",
    default=None,
    help="Kafka broker address and port (e.g. localhost:9092)",
)
@click.option(
    "--repeatable",
    "-r",
    is_flag=True,
    help="Should it generate a repeatable load or use a random generator (default: random)",
)
@click.option("--org", "-o", type=int, help="organisation id")
@click.option("--project", "-p", type=int, help="project id")
@click.option("--dry-run", is_flag=True, help="if set only prints the settings")
@click.option("--update-docs", is_flag=True,  help="creates a README.md  documentation file")
def main(**kwargs):
    """
    Populates the ingest-replay-recordings kafka topic with messages
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

    print("Sending data...", flush=True)
    send_replay_recordings(producer, settings)

    print("Done!")


def _probability(percentage: int):
    chance = random.randint(0,99)
    return (chance < percentage)


def send_replay_recordings(producer, settings):
    topic_name = settings["topic_name"]
    for recording in generate_replay_recordings(settings):
        producer.produce(topic_name, json.dumps(recording))
        producer.poll(0)
    producer.flush()


def generate_replay_recordings(settings):
    num_messages = settings["num_messages"]
    idx = num_messages
    while idx > 0:
        # send chunked segments 20% of the time
        send_chunked_recording = _probability(20)
        replay_id = num_messages-idx
        idx -= 1

        # since every message is 1 segment, use replay_id as segment_id for now
        yield generate_message(
            send_chunked_recording=send_chunked_recording, 
            replay_id=replay_id,
            segment_id=1,
            settings=settings
        )


def get_settings(
    num_messages: Optional[str],
    settings_file: Optional[str],
    topic_name: Optional[str],
    broker: Optional[str],
    repeatable: bool,
    org: Optional[int],
    project: Optional[int],
    dry_run: bool,
    **kwargs,
):
    # default settings
    settings = {
        "num_messages": 100,
        "topic_name": "ingest-replay-recordings",
        "repeatable": False,
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
        settings["org_id"] = org

    if project is not None:
        settings["project_id"] = [project]

    if settings["kafka"].get("bootstrap.servers") is None:
        raise click.UsageError(
            f"Kafka broker was not specified, to specify either use --broker argument or set [kafka][bootstrap.servers] in the settings file"
        )

    if settings.get("org_id") is None:
        raise click.UsageError(
            f"Organization was not specified, to specify either use --org argument or set [org] in the settings file"
        )

    if settings.get("project_id") is None:
        raise click.UsageError(
            f"project_id not specified, to specify either use --project argument or set [project] array in the settings file"
        )

    # num_messages may be set to a string value (when started from kubernetes) like 'default'
    # if set in the command line to anything that can't be converted to an integer just ignore it
    if num_messages is not None:
        try:
            settings["num_messages"] = int(num_messages)
        except ValueError:
            pass  # ignore non integer command line args

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
