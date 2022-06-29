from typing import List, Any, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass

from util import (
    to_optional_datetime,
    pretty_timedelta,
)


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
