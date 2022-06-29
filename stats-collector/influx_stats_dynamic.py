import yaml
from datetime import datetime
from typing import List, Optional, Dict, Union
from dataclasses import dataclass

from influxdb_client import InfluxDBClient


from report import Report, MetricSummary, MetricValue
from util import get_scalar_from_result, to_flux_datetime


@dataclass
class MetricQueryArgs:
    quantiles: List[Union[str, float]]
    filters: Dict[str, str]

    @staticmethod
    def from_dict(d: dict) -> "MetricQuery":
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
        for requested_quantile in self.args.quantiles:
            if type(requested_quantile) == str:
                assert requested_quantile in ["min", "max", "median", "mean"]
                quantile_statement = f"{requested_quantile}()"
            elif type(requested_quantile) == float:
                assert 0.0 <= requested_quantile <= 1.0
                quantile_statement = f"quantile(q: {requested_quantile})"
            else:
                raise ValueError(f"Invalid quantile type: {requested_quantile}")

            query = self.flux_query.format(
                bucket="statsd",
                start=start,
                stop=stop,
                quantile=quantile_statement,
                filters=filter_statement,
            )
            yield query, [f"quantile-{str(requested_quantile)}"]


@dataclass
class DynamicProfile:
    metrics = Dict[str, MetricQuery]

    @staticmethod
    def load(path: str) -> "DynamicProfile":
        with open(path, "r") as f:
            data = f.read()
        return DynamicProfile.loads(data)

    @staticmethod
    def loads(s: str) -> "DynamicProfile":
        raw = yaml.safe_load(s)
        res = DynamicProfile()
        metrics_dict = {}

        metrics_raw = raw.get("metrics", {})
        assert type(metrics_raw) is dict

        for metric_key, metric_dict in metrics_raw.items():
            metrics_dict[metric_key] = MetricQuery.from_dict(metric_dict)

        res.metrics = metrics_dict

        return res


def extend_report_with_query_file(
    report: Report, query_file: str, client: InfluxDBClient, flux_filters: List[str]
):
    # Process filters
    processed_filters: Dict[str, str] = {}
    for filter_str in flux_filters:
        parts = filter_str.strip().split("=")
        if len(parts) != 2:
            raise ValueError(f"Invalid filter: {filter_str}")
        processed_filters[parts[0]] = parts[1]

    prof = DynamicProfile.load(query_file)

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
                print(">>> Processing query:")
                print(query)

                r = query_api.query(query)
                result = get_scalar_from_result(r)

                print(f"Result: {result}\n\n")
                summary.values.append(MetricValue(value=result, attributes=attrs))

        test_run.metrics = metrics

        print(test_run)
