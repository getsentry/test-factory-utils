# load-starter

`load-starter` is a command line utility that controls test runs and notifies about results.

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
{{ .ExampleReport }}
```

## Dry-run Mode

Dry-run mode can be used to see what the tool does with the given configuration, without actually sending any requests or reports.

Example:

```
./load-starter --dry-run --config config.example.yaml --report report.yaml
```



