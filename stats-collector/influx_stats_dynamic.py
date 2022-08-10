import logging
import yaml
from datetime import datetime
from typing import List, Optional, Dict, Union, Any
from dataclasses import dataclass

from influxdb_client import InfluxDBClient

from report import Report, MetricSummary, MetricValue
from util import get_scalar_from_result, to_flux_datetime

logger = logging.getLogger(__name__)


@dataclass
class MetricQueryArgs:
    quantiles: List[Union[str, float]]
    filters: Dict[str, str]

    @staticmethod
    def from_dict(d: dict) -> "MetricQueryArgs":
        assert type(d) is dict

        quantiles = d.get("quantiles", [])
        assert type(quantiles) is list

        filters = d.get("filters", {})
        assert type(filters) is dict

        return MetricQueryArgs(quantiles=quantiles, filters=filters)


@dataclass
class MetricQuery:
    flux_query: Optional[str]
    args: MetricQueryArgs

    @staticmethod
    def from_dict(d: dict) -> "MetricQuery":
        assert type(d) is dict

        args = d.get("args", {})
        assert type(args) is dict

        mq_args = MetricQueryArgs.from_dict(args)

        mq = MetricQuery(flux_query=d.get("flux_query"), args=mq_args)
        return mq

    def generate_queries(
        self, start_time: datetime, end_time: datetime, filters: Dict[str, str]
    ):
        start = to_flux_datetime(start_time)
        stop = to_flux_datetime(end_time)

        # Filters
        final_filters = {}
        final_filters.update(self.args.filters)
        final_filters.update(filters)

        if final_filters:
            filters = []
            for key, value in final_filters.items():
                filters.append(f'filter(fn: (r) =>  r["{key}"] == "{value}") ')
            filter_statement = "|> ".join(filters)
        else:
            # No-op operation
            filter_statement = "drop(columns: [])"

        # Quantiles
        for aggregation in self.args.quantiles:
            if type(aggregation) == str:
                assert aggregation in ["min", "max", "median", "mean"]
                quantile_statement = f"{aggregation}()"
                attribute_name = aggregation
            elif type(aggregation) == float:
                assert 0.0 <= aggregation <= 1.0
                quantile_statement = f"quantile(q: {aggregation})"
                attribute_name = f"q{str(aggregation)}"
            else:
                raise ValueError(f"Invalid quantile type: {aggregation}")

            query = self.flux_query.format(
                bucket="statsd",
                start=start,
                stop=stop,
                quantile=quantile_statement,
                filters=filter_statement,
            )
            yield query, [attribute_name]


@dataclass
class DynamicQueryProfile:
    metrics: Dict[str, MetricQuery]
    metadata: Dict[str, Any]  # kept as an opaque dict since we only pass it along to the report

    @staticmethod
    def load(path: str) -> "DynamicQueryProfile":
        """
        Load the profile given the file path
        """
        with open(path, "r") as f:
            data = f.read()
        return DynamicQueryProfile.loads(data)

    @staticmethod
    def loads(s: str) -> "DynamicQueryProfile":
        """
        Load the profile from the given string
        """
        raw = yaml.safe_load(s)
        metrics_dict = {}
        res = DynamicQueryProfile(metrics=metrics_dict, metadata=raw.get("_meta", None))

        metrics_raw = raw.get("metrics", {})
        assert type(metrics_raw) is dict

        for metric_key, metric_dict in metrics_raw.items():
            metrics_dict[metric_key] = MetricQuery.from_dict(metric_dict)

        return res


def extend_report_with_query_file(
    report: Report, query_file: str, client: InfluxDBClient, flux_filters: List[str]
):
    """
    Extend the provided Report with measurements, collected using a query file.

    One query file defines a list of measurements to be queried from InfluxDB, and for every measurement
    you can get more than one aggregated value by specifying a list of aggregations/quantiles.
    """

    # Process filters
    processed_filters: Dict[str, str] = {}
    for filter_str in flux_filters:
        parts = filter_str.strip().split("=")
        if len(parts) != 2:
            raise ValueError(f"Invalid filter: {filter_str}")
        processed_filters[parts[0]] = parts[1]

    prof = DynamicQueryProfile.load(query_file)

    query_api = client.query_api()

    for test_run in report.test_runs:

        metrics = []

        for metric_id, metric_query in prof.metrics.items():
            summary = MetricSummary(name=metric_id, values=[])
            metrics.append(summary)

            for query, attrs in metric_query.generate_queries(
                start_time=test_run.start_time,
                end_time=test_run.end_time,
                filters=processed_filters,
            ):
                logger.debug(f"Processing query:\n{query}")

                r = query_api.query(query)
                result = get_scalar_from_result(r)

                logger.debug(f"Result: {result}\n\n")
                summary.values.append(MetricValue(value=result, attributes=attrs))

        test_run.metrics = metrics
        test_run.metadata = prof.metadata

