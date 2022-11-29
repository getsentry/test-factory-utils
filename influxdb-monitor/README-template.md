---
layout: page
title: influxdb-monitor
permalink: /influxdb-monitor/
---

influxdb-monitor is used to monitor a metric in InfluxDB.

An example usage of this application is to wait for a Kafka consumer to consume all messages from a topic.
Of course, some agent must send the corresponding consumer lag metric to InfluxDB beforehand.

The program will run until one of the following conditions is met:
* The metric becomes 0
* The metric is not found after the last 5 sequential checks
* The metric does not change within the last 3 sequential checks

The following is the output of the program's help command:

```
{{ .Usage}}
```
