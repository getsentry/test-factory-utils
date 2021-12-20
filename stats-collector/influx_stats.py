from typing import Generator, List, Sequence, Callable, Any, Optional
from datetime import datetime

from influxdb_client import QueryApi, InfluxDBClient
from util import load_flux_file, to_flux_datetime
from dataclasses import dataclass


@dataclass
class MetricValue:
    """
    A single value extracted from a metric e.g. "average event_processing_time"
    A Metric Summary contains a list of MetricValue
    """
    value: float
    attributes: List[str]


@dataclass
class MetricSummary:
    """
    Contains the extracted summaries for a metric
    """
    name: str
    values: List[MetricValue]


def event_accepted_stats(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("events_accepted.flux")
    funcs = ['max', 'median']

    for func in funcs:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "windowPeriod": "10s",
            "func": func,
        })

        r = query_api.query(code)

        yield MetricValue(value=get_scalar_from_result(r), attributes=[func])


def event_processing_time(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("event_processing_time.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "quantile": quantile,
        })

        r = query_api.query(code)

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


def kafka_messages_produced(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("kafka_messages.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "quantile": quantile,
         })

        r = query_api.query(code)

        def session_selector(row): return row["event_type"] == "session"

        yield MetricValue(value=get_scalar_from_result(r, condition=session_selector), attributes=["session", q_name])

        def metric_selector(row): return row["event_type"] == "metric"

        yield MetricValue(value=get_scalar_from_result(r, condition=metric_selector), attributes=["metric", q_name])


def requests_per_second_locust(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("total_requests_locust.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "quantile": quantile,
        })

        r = query_api.query(code)

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])

def cpu_usage(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("cpu_usage.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "quantile": quantile,
        })

        r = query_api.query(code)

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])

def memory_usage(start: str, stop: str, query_api: QueryApi) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("memory_usage.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(**{
            "start": start,
            "stop": stop,
            "quantile": quantile,
        })

        r = query_api.query(code)

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


def get_scalar_from_result(result, column: str = "_value", condition: Optional[Callable[[Any], bool]] = None) -> Optional[float]:
    for table in result:
        for record in table:
            if condition is None:
                # no condition first would do:
                return record[column]
            elif condition(record):
                return record[column]
    # nothing matched
    return None


stats_functions = [
    ("events accepted", event_accepted_stats),
    ("event processing time (ms)", event_processing_time),
    ("received events/s kafka", kafka_messages_produced),
    ("request per second (locust POV)",requests_per_second_locust),
    ("cpu usage (nanocores)", cpu_usage),
    ("memory_usage (Mb)", memory_usage),
]


def get_stats(start_time: datetime, end_time: datetime, url: str, token: str, org: str) -> Sequence[MetricSummary]:
    start = to_flux_datetime(start_time)
    stop = to_flux_datetime(end_time)

    client = InfluxDBClient(
        url=url,
        token=token,
        org=org
    )
    query_api = client.query_api()

    results = []
    for metric_name, generator in stats_functions:
        summary = MetricSummary(name=metric_name, values=[])
        results.append(summary)
        for result in generator(start=start, stop=stop, query_api=query_api):
            summary.values.append(result)
    return results
