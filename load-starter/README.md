# load-starter

`load-starter` is a command line utility that controls test runs and notifies about results.

Here's the current usage:

```
Usage:
  ./load-starter [flags]

Flags:
  -b, --board string          the InfluxDb board id
  -f, --config string         Path to configuration file
      --dry-run               dry-run mode
  -d, --duration duration     the duration to run the program (default 10s)
  -h, --help                  help for app
  -i, --influx string         InfluxDB dashboard base URL (default "http://localhost:8086")
  -l, --locust string         Locust server endpoint (default "http://ingest-load-tester.default.svc.cluster.local")
  -o, --organisation string   the InfluxDb organisation id
  -r, --report string         If provided: report will be written here
  -u, --users int             number of simulated users (default 5)
```

## Building

To build the tool:

```
make build
```

To run:

```
go run .
```

## Configuration File

If provided (via `--config` command line argument), the configuration file will be used to control the test load created by Locust. If the configuration file is NOT provided, command line options will be used to start a simple test of type `static`.

### Test Stages

A test run consists of multiple **stages**.

Each stage has a type, and the currently supported stage types are:

* `static` -- you specify the number of users and duration, and load-starter will tell Locust to run for the specified time.
* `gradual` -- this stage gradually changes the load according to the given starting and ending number of users, duration, and step size.
    Let's assume it receives the following inputs: startUsers=10, endUsers=30, step=5, duration=60s. In this case, first it’ll run with 10 users for 60s, then for 15 for 60s... and finally, for 30 users for 60s; the total running time will be 300 seconds (5 steps).
    Negative step size is supported (e.g. going from 30 users to 10).


Example configuration file may look like this:

```yaml
---
stages:
- type: gradual
  startUsers: 10
  endUsers: 30
  step: 5
  stepDuration: '60s'
- type: static
  users: 40
  duration: '100s'
- type: gradual
  startUsers: 30
  endUsers: 20
  step: -2
  stepDuration: '60s'
```

## Test Report

If `--report FILE` argument is provided, a test report will be generated and written at the end of the run.

For every stage and substage of the run, the report will include start and end timestamps, number of users, and potentially other kinds of metadata.

Example report:

```yaml
stageReports:
- steps:
  - users: 10
    startTime: 2022-01-05T16:50:58.800347Z
    endTime: 2022-01-05T16:51:58.800358Z
  - users: 15
    startTime: 2022-01-05T16:51:58.80036Z
    endTime: 2022-01-05T16:52:58.800365Z
...
  - users: 30
    startTime: 2022-01-05T16:54:58.803081Z
    endTime: 2022-01-05T16:55:58.803085Z
  name: ""
  stageType: gradual
- steps:
  - users: 40
    startTime: 2022-01-05T16:55:58.803626Z
    endTime: 2022-01-05T16:59:58.803636Z
  name: ""
  stageType: static
```
