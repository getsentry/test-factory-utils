import io
import json
from enum import Enum, unique

import yaml

from influx_stats import Report
from util import to_optional_datetime


@unique
class OutputFormat(Enum):
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


class TextFormatter:
    def format(self, report: Report) -> str:
        output = io.StringIO()
        base_indent = "  "
        for test_run in report.test_runs:
            level = 0
            print(f"\nTest run {test_run.name} ", file=output)
            level = 1
            indent = base_indent * level
            print(
                f"\n{indent} start:{to_optional_datetime(test_run.start_time)} end:{to_optional_datetime(test_run.end_time)}",
                file=output,
            )

            print(f"\n{indent}spec:", file=output)
            level = 2
            indent = base_indent * level
            spec = yaml.dump(test_run.spec, indent=2, default_flow_style=False)
            spec = spec.replace("\n", f"\n{indent}")
            print(f"\n{indent}{spec}", file=output)

            for stat in test_run.metrics:
                level = 3
                indent = base_indent * level
                print(f"{indent}{stat.name}", file=output)
                for metric_value in stat.values:
                    params = ", ".join(metric_value.attributes)
                    if metric_value.value is not None:
                        s = "{}{:>16} -> {:.2f}".format(
                            indent, params, metric_value.value
                        )
                    else:
                        s = "{}{:>16} -> Empty".format(indent, params)
                    print(s, file=output)
                print(f"{indent}" + "-" * 32, file=output)
        ret_val = output.getvalue()
        output.close()
        return ret_val


class JsonFormatter:
    def format(self, report: Report) -> str:
        result = report.to_dict()
        return json.dumps(result, indent=2)


class YamlFormatter:
    def format(self, report: Report) -> str:
        result = report.to_dict()
        return yaml.dump(result, indent=2, default_flow_style=False)


def get_formatter(req_format: str):
    if req_format == OutputFormat.TEXT.value:
        return TextFormatter()
    elif req_format == OutputFormat.JSON.value:
        return JsonFormatter()
    elif req_format == OutputFormat.YAML.value:
        return YamlFormatter()
    else:
        return TextFormatter()
