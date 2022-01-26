from typing import Callable, Mapping, Any, List
import random
import math


def generate_metric(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": 1,
        "project_id": 1,
        "name": "sentry.sessions.session",
        "unit": "",
        "type": "c",
        "value": 9441.0,
        "timestamp": 1643113620,
        "tags": {
            "environment": "environment-1",
            "release": "r-1.0.2",
            "session.status": "init"
        },
        "metric_types": {
            "session": 1,
            "user": 1,
            "session.error": 1,
            "session.duration": 1
        }
    }


def get_metric_generator(metric_type: str) -> Callable[[int, int, Mapping[str, Any]], Mapping[str, Any]]:
    return {
        "session": session_metric_generator,
        "user": user_metric_generator,
        "session.error": session_error_metric_generator,
        "session.duration": session_duration_metric_generator,
    }.get(metric_type, default_metric_generator)


def is_repeatable(settings) -> bool:
    return settings["repeatable"]


def _get_org_id(idx: int, settings: Mapping[str, Any]) -> int:
    # only one org no choice
    return settings["org"]


def _get_project_id(idx: int, settings: Mapping[str, Any]) -> int:
    projects = settings["project"]

    if is_repeatable(settings):
        proj_idx = idx % len(projects)
    else:
        proj_idx = random.randint(0, len(projects) - 1)
    return projects[proj_idx]


def _get_timestamp(idx: int, settings: Mapping[str, Any]) -> int:
    base = settings["time_delta"]
    base_seconds = int(settings["time_delta"].total_seconds())
    num_messages = settings["num_messages"]
    if is_repeatable(settings):
        step = max(1, int(base_seconds / num_messages))
        offset = step * idx
    else:
        offset = random.randint(0, base_seconds)
    timestamp = settings["timestamp"] - offset
    return timestamp


def _get_num_elments_in_collection(idx: int, settings: Mapping[str, Any]) -> List[int]:
    col_range = abs(settings["col_max"] - settings["col_min"])
    num_messages = settings["num_messages"]

    if is_repeatable(settings):
        step = max(1, int(col_range / num_messages))
        offset = step * idx
    else:
        offset = random.randint(0, col_range)

    return settings["col_min"] + offset


def _get_set(idx: int, settings: Mapping[str, Any]) -> List[int]:
    num_elms = _get_num_elments_in_collection(idx, settings)

    if is_repeatable(settings):
        return [idx + i for i in num_elms]
    else:
        return [random.randint(1, 9999) for i in num_elms]


def _get_distribution(idx: int, settings: Mapping[str, Any]) -> List[float]:
    num_elms = _get_num_elments_in_collection(idx, settings)

    if is_repeatable(settings):
        return [(idx + i) * 5 + 0.1 for i in num_elms]
    else:
        return [random.random() * 999 for i in num_elms]


def _get_release(idx: int, settings: Mapping[str, Any]) -> str:
    releases = settings["releases"]

    if is_repeatable(settings):
        rel_num = idx % releases + 1
    else:
        rel_num = random.randint(1, releases)
    return f"v{rel_num}.1.1"


def _get_environment(idx: int, settings: Mapping[str, Any]) -> str:
    environments = settings["environments"]
    if is_repeatable(settings):
        rel_num = idx % environments + 1
    else:
        rel_num = random.randint(1, environments)
    return f"env-{rel_num}"


def _get_tags(idx: int, settings: Mapping[str, Any]) -> Mapping[str, str]:
    return {
        "environment": _get_environment(idx, settings),
        "release": _get_release(idx, settings)
    }


def default_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "name": "default",
        "unit": "",
        "type": "c",
        "value": idx,
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "init"
        }
    }


def session_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": 1,
        "name": "sentry.sessions.session",
        "unit": "",
        "type": "c",
        "value": float(idx),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "init"
        }
    }


def user_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": 1,
        "project_id": 1,
        "name": "sentry.sessions.user",
        "unit": "",
        "type": "s",
        "value": _get_set(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "init"
        }
    }


def session_error_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": 1,
        "name": "sentry.sessions.session.error",
        "unit": "",
        "type": "s",
        "value": _get_set(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "errored_preaggr"
        }
    }


def session_duration_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": 1,
        "name": "sentry.sessions.session.error",
        "unit": "ms",
        "type": "d",
        "value": _get_distribution(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "errored_preaggr"
        }
    }
