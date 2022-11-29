---
layout: page
title: influxdb-monitor
permalink: /influxdb-monitor/
---

influxdb-monitor is used to monitor a metric in InfluxDB.

An example usage of this application is to wait for a Kafka consumer to consume all messages from a topic.
Of course, some agent must send metrics about the consumer lag to InfluxDB beforehand.

The program will run until one of the following conditions is met:
* The metric becomes 0
* The metric is not found after the last 5 sequential checks
* The metric does not change within the last 3 sequential checks

The following is the output of the program's help command:

```
Usage:
  influxdb-monitor [flags]
  influxdb-monitor [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  help        Help about any command
  update-docs Update the documentation

Flags:
  -b, --bucket-name string      Bucket where the metric is stored (default "statsd")
      --dry-run                 dry-run mode
  -f, --filter strings          Measurement filters (0 or more) in the format: filter-name=filter-value
  -x, --influxdb-token string   InfluxDB access token
  -u, --influxdb-url string     InfluxDB URL (default "http://localhost:8086")
  -m, --measurement string      Name of the measurement (metric) (default "kafka_consumer_lag")
  -o, --organisation string     InfluxDB organisation id

Use "influxdb-monitor [command] --help" for more information about a command.

```
