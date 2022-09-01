---
layout: page
title: vegeta2influx
permalink: /vegeta2influx/
---

`vegata-2-influx` is a command line utility that converts vegeta generated request metrics into InfluxDB points,
it uses the influxdb-client library to add the metrics to InfluxDB.

Here's the current usage:

```
Usage:
  vegeta2influx [flags]
  vegeta2influx [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  help        Help about any command
  update-docs Update the documentation

Flags:
  -b, --bucket-name string      Bucket where the metric is stored (default "vegeta")
  -c, --color                   Use color (only for console output).
  -d, --dry-run                 dry-run mode
  -x, --influxdb-token string   InfluxDB access token
  -u, --influxdb-url string     InfluxDB URL (default "http://localhost:8086")
  -i, --input string            File name to use for input, default <stdin>
  -l, --log string              Log level: trace, info, warn, (error), fatal, panic (default "info")
  -m, --measurement string      Name of the measurement (metric) (default "request")
  -o, --organisation string     InfluxDB organisation id
  -t, --tags stringArray        Additional tags -t name=value -t n2=v2

Use "vegeta2influx [command] --help" for more information about a command.

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

