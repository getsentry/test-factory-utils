from typing import Generator
from functools import partial
from enum import Enum, unique

from influxdb_client import QueryApi, InfluxDBClient
from util import load_flux_file, to_flux_datetime, get_scalar_from_result
from report import Report, MetricSummary, MetricValue


@unique
class TestingProfile(Enum):
    RELAY = "relay"
    METRICS_INDEXER = "metrics-indexer"
    SNUBA_METRICS_CONSUMER = "snuba-metrics-consumer"
    ANTI_ABUSE = "anti-abuse"

    @staticmethod
    def values():
        return [profile.value for profile in TestingProfile]


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[func])


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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
            value=get_scalar_from_result(r, condition=session_selector),
            attributes=["session", q_name],
        )

        def metric_selector(row):
            return row["event_type"] == "metric"

        yield MetricValue(
            value=get_scalar_from_result(r, condition=metric_selector),
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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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

        yield MetricValue(value=get_scalar_from_result(r), attributes=[q_name])


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
    TestingProfile.ANTI_ABUSE.value: {
        "stats_functions": [
            ("cpu usage (cores)", partial(cpu_usage, container_name="nginx")),
            ("memory_usage (Mb)", partial(memory_usage, container_name="nginx")),
            ("envoy cpu usage (cores)", partial(cpu_usage, container_name="envoy")),
            ("envoy memory_usage (Mb)", partial(memory_usage, container_name="envoy")),
        ]
    },
}


def extend_report_with_static_profile(
    report: Report, profile: str, client: InfluxDBClient
):
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
