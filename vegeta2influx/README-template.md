---
layout: page
title: vegeta2influx
permalink: /vegeta2influx/
---

`vegata-2-influx` is a command line utility that converts vegeta generated request metrics into InfluxDB points,
it uses the influxdb-client library to add the metrics to InfluxDB.

Here's the current usage:

```
{{ .Usage }}
```

## Building

To build the tool:

```shell
make build
```

To run:

```shell
go run .
```

