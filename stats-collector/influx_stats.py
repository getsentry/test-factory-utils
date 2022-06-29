from typing import Generator, List, Sequence, Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from functools import partial

from influxdb_client import QueryApi, InfluxDBClient
from util import (
    load_flux_file,
    to_flux_datetime,
    to_optional_datetime,
    pretty_timedelta,
)
from dataclasses import dataclass
from enum import Enum, unique


@unique
class TestingProfile(Enum):
    RELAY = "relay"
    METRICS_INDEXER = "metrics-indexer"
    SNUBA_METRICS_CONSUMER = "snuba-metrics-consumer"

    @staticmethod
    def values():
        return [profile.value for profile in TestingProfile]


@dataclass
class MetricValue:
    """
    A single value extracted from a metric e.g. "average event_processing_time"
    A Metric Summary contains a list of MetricValue
    """

    value: float
    attributes: List[str]

    def to_dict(self):
        return {
            "value": self.value,
            "attributes": [val for val in self.attributes],
        }


@dataclass
class MetricSummary:
    """
    Contains the extracted summaries for a metric
    """

    name: str
    values: List[MetricValue]

    def to_dict(self):
        return {"name": self.name, "values": [value.to_dict() for value in self.values]}


@dataclass
class TestRun:
    start_time: datetime
    end_time: datetime
    name: Optional[str]
    description: Optional[str]
    duration: timedelta
    runner: Optional[str]
    spec: Dict[str, Any]
    metrics: List[MetricSummary]

    def to_dict(self):
        ret_val = {
            "startTime": to_optional_datetime(self.start_time),
            "endTime": to_optional_datetime(self.end_time),
            "duration": pretty_timedelta(self.duration),
            "metrics": [metric.to_dict() for metric in self.metrics],
            "spec": self.spec,
        }

        if self.name:
            ret_val["name"] = self.name
        if self.description:
            ret_val["description"] = self.name
        if self.runner:
            ret_val["runner"] = self.runner

        return ret_val


@dataclass
class Report:
    start_time: datetime
    end_time: datetime
    test_runs: List[TestRun]

    def to_dict(self):
        return {
            "startTime": to_optional_datetime(self.start_time),
            "endTime": to_optional_datetime(self.end_time),
            "testRuns": [test_run.to_dict() for test_run in self.test_runs],
        }


def event_accepted_stats(
    start: str, stop: str, query_api: QueryApi
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("events_accepted.flux")
    funcs = ["median", "max"]

    for func in funcs:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "windowPeriod": "10s",
                "func": func,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[func])


def event_processing_time(
    start: str, stop: str, query_api: QueryApi
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("event_processing_time.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def kafka_messages_produced(
    start: str, stop: str, query_api: QueryApi
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("kafka_messages.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
            }
        )

        r = query_api.query(code)

        def session_selector(row):
            return row["event_type"] == "session"

        yield MetricValue(
            value=_get_scalar_from_result(r, condition=session_selector),
            attributes=["session", q_name],
        )

        def metric_selector(row):
            return row["event_type"] == "metric"

        yield MetricValue(
            value=_get_scalar_from_result(r, condition=metric_selector),
            attributes=["metric", q_name],
        )


def requests_per_second_locust(
    start: str, stop: str, query_api: QueryApi
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("total_requests_locust.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def cpu_usage(
    start: str, stop: str, query_api: QueryApi, container_name: str
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("cpu_usage.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
                "container_name": container_name,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def memory_usage(
    start: str, stop: str, query_api: QueryApi, container_name: str
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("memory_usage.flux")
    quantiles = [(0.5, "median"), (0.9, "0.9"), (0.99, "0.99"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
                "container_name": container_name,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def event_queue_size(
    start: str, stop: str, query_api: QueryApi
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("event_queue_size.flux")
    quantiles = [(0.5, "median"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def kafka_consumer_processing_rate(
    start: str,
    stop: str,
    query_api: QueryApi,
    consumer_group: str,
) -> Generator[MetricSummary, None, None]:
    template = load_flux_file("kafka_consumer_processing_rate.flux")
    quantiles = [(0.5, "median"), (1.0, "max")]

    for quantile, q_name in quantiles:
        code = template.format(
            **{
                "start": start,
                "stop": stop,
                "quantile": quantile,
                "consumer_group": consumer_group,
            }
        )

        r = query_api.query(code)

        yield MetricValue(value=_get_scalar_from_result(r), attributes=[q_name])


def _get_scalar_from_result(
    result, column: str = "_value", condition: Optional[Callable[[Any], bool]] = None
) -> Optional[float]:
    for table in result:
        for record in table:
            if condition is None:
                # no condition first would do:
                return record[column]
            elif condition(record):
                return record[column]
    # nothing matched
    return None


STATIC_TEST_PROFILES = {
    TestingProfile.RELAY.value: {
        "stats_functions": [
            ("events accepted", event_accepted_stats),
            ("events queue size max", event_queue_size),
            ("received events/s kafka", kafka_messages_produced),
            ("request per second (locust POV)", requests_per_second_locust),
            ("cpu usage (cores)", partial(cpu_usage, container_name="relay")),
            ("memory_usage (Mb)", partial(memory_usage, container_name="relay")),
        ]
    },
    TestingProfile.METRICS_INDEXER.value: {
        "stats_functions": [
            (
                "messages processed by consumer (/s)",
                partial(
                    kafka_consumer_processing_rate,
                    consumer_group="ingest-metrics-consumer",
                ),
            ),
            (
                "cpu usage (cores)",
                partial(cpu_usage, container_name="ingest-metrics-consumer"),
            ),
            (
                "memory_usage (Mb)",
                partial(memory_usage, container_name="ingest-metrics-consumer"),
            ),
        ]
    },
}


def get_stats_with_static_profile(
    report: Report, profile: str, client: InfluxDBClient
) -> Report:
    if profile not in STATIC_TEST_PROFILES:
        raise ValueError(f"No stats found for the profile: {profile}", profile)

    stats_functions = STATIC_TEST_PROFILES[profile]["stats_functions"]

    query_api = client.query_api()

    for test_run in report.test_runs:
        start = to_flux_datetime(test_run.start_time)
        stop = to_flux_datetime(test_run.end_time)

        metrics = []
        for metric_name, generator in stats_functions:
            summary = MetricSummary(name=metric_name, values=[])
            metrics.append(summary)
            for result in generator(start=start, stop=stop, query_api=query_api):
                summary.values.append(result)
        test_run.metrics = metrics
    return report
