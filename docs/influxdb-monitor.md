---
layout: page
title: influxdb-monitor
permalink: /influxdb-monitor/
---

influxdb-monitor is used to monitor a metric in InfluxDB.

The typical usage of this application is to wait for a Kafka consumer to consume all messages from a topic,
of course some agent must send metrics about the topic to InfluxDB .

The program will run until one of the following conditions is met:
* the metric becomes 0
* the metric does not change during 5 sequential checks
* the metric is not found during 5 sequential checks

The following is the output of the program's help command:

```
Waits for a condition in InfluxDB to become True or an expiration time

Usage:
  influxdb-monitor [flags]

Flags:
  -b, --bucket-name string      Bucket where the metric is stored (default "statsd")
      --dry-run                 dry-run mode
  -f, --filter strings          Measurement filters (0 or more) in the format: filter-name=filter-value
  -h, --help                    help for influxdb-monitor
  -x, --influxdb-token string   InfluxDB access token
  -u, --influxdb-url string     InfluxDB URL (default "http://localhost:8086")
  -m, --measurement string      Name of the measurement (metric) (default "kafka_consumer_lag")
  -o, --organisation string     InfluxDB organisation id


```
