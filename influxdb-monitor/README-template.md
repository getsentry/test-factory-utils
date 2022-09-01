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
{{ .Usage}}
```
