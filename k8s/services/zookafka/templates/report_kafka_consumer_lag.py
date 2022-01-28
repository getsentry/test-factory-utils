#!/usr/bin/env python
# This script fetches kafka consumer lag for the given consumer groups, and reports the values as StatsD metrics.
import os
import re
import sys
import socket
import subprocess
from optparse import OptionParser

METRIC_PREFIX = os.environ.get("METRIC_PREFIX", "kafka_consumer.")
BOOTSTRAP_SERVERS = os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092")

STATSD_HOST = os.environ.get("STATSD_HOST", "127.0.0.1")
STATSD_PORT = os.environ.get("STATSD_PORT", 8125)


def parse_result(s):
    results = []
    for line in s.splitlines():
        line = line.strip()
        print(line)
        match = re.match(r"^([\w-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)", line)
        if match:
            results.append(
                {
                    "topic": match.group(1),
                    "partition": int(match.group(2)),
                    "cur_offset": int(match.group(3)),
                    "end_offset": int(match.group(4)),
                    "lag": int(match.group(5)),
                }
            )
        else:
            continue
    return results


def get_consumer_group_info(name):
    command = [
        "kafka-consumer-groups",
        "--bootstrap-server",
        BOOTSTRAP_SERVERS,
        "--group",
        name,
        "--describe",
    ]

    return subprocess.check_output(command)


def send_to_statsd(metric_name, value, tags):
    if METRIC_PREFIX:
        metric_name = METRIC_PREFIX + metric_name

    message = "{}:{}|g".format(metric_name, value)

    # Attach tags
    if tags:
        message += "|#"
        message += ",".join(map(lambda i: "{}:{}".format(i[0], i[1]), tags.items()))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(message), (STATSD_HOST, STATSD_PORT))


def report_metrics(partition_entry):
    tags = {
        "topic": partition_entry["topic"],
        "partition": partition_entry["partition"],
        "group": partition_entry["consumer_group"],
    }
    # cur_offset
    send_to_statsd("cur_offset", partition_entry["cur_offset"], tags)
    send_to_statsd("end_offset", partition_entry["end_offset"], tags)
    send_to_statsd("lag", partition_entry["lag"], tags)


def process_consumer_group(consumer_group):
    print("Processing consumer group: {}".format(consumer_group))
    consumer_group_info = get_consumer_group_info(consumer_group)
    partition_info = parse_result(consumer_group_info)
    for entry in partition_info:
        entry["consumer_group"] = consumer_group
        report_metrics(entry)


def main():
    parser = OptionParser()
    parser.add_option(
        "-c",
        "--consumer-group",
        action="append",
        help="consumer group to get metrics about",
    )

    (options, _) = parser.parse_args()

    consumer_groups = options.consumer_group
    if not consumer_groups:
        print("No consumer groups provided, exiting.")
        sys.exit(1)

    print("Statsd endpoint: {}:{}".format(STATSD_HOST, STATSD_PORT))

    for group in consumer_groups:
        try:
            process_consumer_group(group)
        except Exception as e:
            print("Caught exception, skipping: ")
            print(e)


if __name__ == "__main__":
    main()
