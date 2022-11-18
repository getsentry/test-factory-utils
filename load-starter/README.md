# load-starter

`load-starter` is a command line utility that controls test runs and notifies about results.

Here's the current usage:

```
Usage:
  load-starter --config config.py --report report.yaml  [flags]
  load-starter [command]

Available Commands:
  completion  generate the autocompletion script for the specified shell
  help        Help about any command
  update-docs Update the documentation

Flags:
      --color                         Use color (only for console output).
  -f, --config string                 Path to a skylark configuration file
      --dry-run                       dry-run mode
      --grafana-base string           Grafana base URL
      --grafana-board string          Grafana board id
      --grafana-organisation string   Grafana board id
  -v, --grafana-var stringToString    Grafana dashboard variables with their values (default [])
      --influx-base string            InfluxDB dashboard base URL
      --influx-board string           InfluxDb board id
      --influx-organisation string    InfluxDb organisation id
      --load-server string            Load server endpoint (default "http://go-load-tester.default.svc.cluster.local")
      --log string                    Log level: trace, debug, (info), warn, error, fatal, panic (default "info")
  -r, --report string                 If provided: report will be written here
  -s, --slack-message string          If provided: notification report (simply put, a formatted Slack message) will be written here

Use "load-starter [command] --help" for more information about a command.

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

## Configuration File

To configure the load starter provide the `--config` command line argument

The configuration file is a starlark script.
For details on the starlark language please see [starlark-go](https://github.com/google/starlark-go).

The following custom builtins are available for creating test runs:

```python
duration( val: str)
```

Creates a duration value from a string. For details of the string syntax please see the go documentation
for [func ParseDuration](https://pkg.go.dev/time#ParseDuration).
Examples:

```python
one_sec = duration("1s")
two_hours_four_min = duration("2h4m")
one_ms = duration("1ms")
```

```
set_load_tester_url(url: str)
```
Sets the url of the load tester (will override the `--load-server` CLI parameter) for all tests
that follow the call to `set_load_tester_url`.

Examples:

```python
set_load_tester_url("http://go-load-tester.default.svc.cluster.local")
```

```
add_locust_test(
    duration: Union[duration,str],
    users: int,
    spawn_rate: Optional[int],
    name: Optional[str],
    description: Optional[str],
    url: Optional[str],
    produce_report: Optional[bool]=True,
    )
```
This is an obsolete API. If possible please migrate to Vegeta tests.
Creates a locust load test.

```
add_vegeta_test(
    duration: Union[duration,str],
    test_type: str,
    freq: int,
    per:  Union[duration,str],
    config: Dict[str, Any],
    name: Optional[str],
    description: Optional[str],
    url: Optional[str],
    produce_report: Optional[bool]=True,
    labels:Union[[][]str, Mapping[str,str]]= None
    )
```

Creates a Vegeta load test.

The `freq` and `per` are used to control the intensity of the attack. `freq` represents number of requests sent and
`per` represents the amount of time in which to send the number of requests specified in `freq`, typically `per` is
`"1s"` in which case `freq` represents requests/sec.

The `test_type` controls the type of test (the test types are defined in go-load-tester, see `go-load-tester` for details).

The `config` represents the configuration of the load test and is dependent on the `test_type` see `go-load-tester` documentation
for details on the available test types and the configuration for each test type.

The `produce_report` parameter controls the report generation.By default, each test will create an entry in the final report.
Sometime stages are used to warm up caches or to wait for various queues to empty before a new test is run. Creating report
results for these stages is not useful, they only add noise, and it is better if these stages are ignored and not further
processed by downstream programs. For these cases specify `produce_report=False` for the tests.

The `labels` parameter can be either a dictionary str->str containing label name and value or a two level combination of
arrays or tuples containing the label, in the first position, and one or more values e.g. `[["l1,"v1"]["l2","v2-1","v2-2"]("l3","v3)]`

```
add_run_external( cmd: List[str])
```

Schedules running an external (shell) command.

```python
add_run_external(["ls", "-la", "my-dir"])
```

## Test Report

If `--report FILE` argument is provided, a test report will be generated and written at the end of the run.


Example report:

```yaml
testRuns:
  - runInfo:
      name: 'Session test with Vegeta, on frequency: 100/sec'
      description: Testing transactions with various params
      duration: 2m0s
      runner: vegeta
      spec:
        numMessages: 100
        params:
          maxBreadcrumbs: 25
          maxSpans: 40
          numReleases: 1000
          numUsers: 2000
        per: 1s
        testType: transaction
    startTime: 2022-05-10T16:01:19.816269586Z
    endTime: 2022-05-10T16:03:19.859911674Z
  - runInfo:
      name: 'Session test with Vegeta, on frequency: 200/sec'
      description: Testing transactions with various params
      duration: 2m0s
      runner: vegeta
      spec:
        numMessages: 200
        params:
          maxBreadcrumbs: 25
          maxSpans: 40
          numReleases: 1000
          numUsers: 2000
        per: 1s
        testType: transaction
    startTime: 2022-05-10T16:03:38.226848053Z
    endTime: 2022-05-10T16:05:38.286043691Z
startTime: 2022-05-10T16:00:59.89790197Z
endTime: 2022-05-10T16:07:56.64842927Z

```

## Dry-run Mode

Dry-run mode can be used to see what the tool does with the given configuration, without actually sending any requests or reports.

Example:

```
./load-starter --dry-run --config config.example.yaml --report report.yaml
```



