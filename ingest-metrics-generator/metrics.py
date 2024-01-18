from typing import Callable, Mapping, Any, List, Optional
import random
import string


def generate_metric(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    metric_type = _get_metric_type(idx, settings) or ""
    generator = _get_metric_generator(metric_type)

    return generator(idx, settings)


def _get_metric_type(idx: int, settings: Mapping[str, Any]) -> Optional[str]:
    dist = settings["metric_distribution"]

    if len(dist) == 0:
        return None

    max_val = dist[-1][1]

    if is_repeatable(settings):
        i = idx % max_val
    else:
        i = random.randint(1, max_val)

    for name, val in dist:
        if i <= val:
            return name

    return None


def _get_metric_generator(
    metric_type: str,
) -> Callable[[int, Mapping[str, Any]], Mapping[str, Any]]:
    return {
        "session": session_metric_generator,
        "user": user_metric_generator,
        "session.error": session_error_metric_generator,
        "session.duration": session_duration_metric_generator,
    }.get(metric_type, default_metric_generator)


def is_repeatable(settings) -> bool:
    return settings["repeatable"]


def get_bin_encoding_len(settings) -> Optional[int]:
    return settings.get("bin_encoding_len")


def _get_org_id(idx: int, settings: Mapping[str, Any]) -> int:
    # only one org no choice
    return settings["org"]


def _get_project_id(idx: int, settings: Mapping[str, Any]) -> int:
    projects = settings["projects"]

    if is_repeatable(settings):
        proj_idx = idx % len(projects)
    else:
        proj_idx = random.randint(0, len(projects) - 1)
    return projects[proj_idx]


def _get_timestamp(idx: int, settings: Mapping[str, Any]) -> int:
    base_seconds = int(settings["time_delta"].total_seconds())
    num_messages = settings["num_messages"]
    if is_repeatable(settings):
        step = max(1, int(base_seconds / num_messages))
        offset = step * idx
    else:
        offset = random.randint(0, base_seconds)
    timestamp = settings["timestamp"] - offset
    return timestamp


def _get_num_elements_in_collection(idx: int, settings: Mapping[str, Any]) -> int:
    col_range = abs(settings["col_max"] - settings["col_min"]) + 1

    num_messages = settings["num_messages"]

    if is_repeatable(settings):
        step = max(1, int(col_range / num_messages))
        offset = step * idx % col_range
    else:
        offset = random.randint(0, col_range - 1)

    return settings["col_min"] + offset


def _get_set(idx: int, settings: Mapping[str, Any]) -> List[int]:
    num_elms = _get_num_elements_in_collection(idx, settings)

    if is_repeatable(settings):
        return [idx + i for i in range(num_elms)]
    else:
        return [random.randint(1, 9999) for i in range(num_elms)]


def _get_distribution(idx: int, settings: Mapping[str, Any]) -> List[float]:
    num_elms = _get_num_elements_in_collection(idx, settings)

    if bin_encoding_len := get_bin_encoding_len(settings):
        return "".join(
            [
                random.choice(string.ascii_letters)
                for _ in range(num_elms * bin_encoding_len)
            ]
        )

    if is_repeatable(settings):
        return [(idx + i) * 5 + 0.1 for i in range(num_elms)]
    return [random.random() * 999 for i in range(num_elms)]


def _get_tag_num_with_unique_rate(
    idx: int, settings: Mapping[str, Any], num_predefined: int, unique_rate: float
) -> int:
    """
    Return a tag number (id) based on the provided inputs.

    If "unique_rate" is 0, we only return ids in the range specified by "num_predefined".

    If "unique_rate" is a positive number between 0.0 and 1.0, it defines the sampling rate for
    "unique ids per message", and "num_predefined" defines a space of "non-unique" messages and used
    as a fallback.

    For example: if "unique_rate" is 0.25 and "num_predefined" is 300, (approximately) every fourth returned
    id will be a new, unique id never seen before. All other returned ids will be in the range [1, 300].

    """
    assert 0.0 <= unique_rate <= 1.0
    assert num_predefined > 0

    tag_num = 0

    # Shift to distinguish between unique and predefined values
    shift = 1000 + num_predefined

    if unique_rate > 0:
        if is_repeatable(settings):
            scale_param = 1000
            if idx % scale_param + 1 <= scale_param * unique_rate:
                tag_num = idx + shift
        else:
            if random.random() < unique_rate:
                tag_num = idx + shift

    # Process the case when the unique rate is 0 (i.e., no unique tags needed), or as a
    # fallback if sampling didn't succeed.
    if tag_num == 0:
        if is_repeatable(settings):
            tag_num = idx % num_predefined + 1
        else:
            tag_num = random.randint(1, num_predefined)

    return tag_num


def _get_release(idx: int, settings: Mapping[str, Any]) -> str:
    releases = settings["releases"]
    rate = settings["releases_unique_rate"]

    rel_num = _get_tag_num_with_unique_rate(idx, settings, releases, rate)

    return f"v{rel_num}.1.1"


def _get_environment(idx: int, settings: Mapping[str, Any]) -> str:
    environments = settings["environments"]
    rate = settings["environments_unique_rate"]

    env_num = _get_tag_num_with_unique_rate(idx, settings, environments, rate)

    return f"env-{env_num}"


def _get_tags(idx: int, settings: Mapping[str, Any]) -> Mapping[str, str]:
    tags = {
        "environment": _get_environment(idx, settings),
        "release": _get_release(idx, settings),
    }

    num = settings["num_extra_tags"]
    predefined_values = settings["extra_tags_values"]
    rate = settings["extra_tags_unique_rate"]

    for i in range(num):
        value = _get_tag_num_with_unique_rate(
            idx * num + i, settings, predefined_values, rate
        )
        tags[f"extra-tag-{i}"] = f"extra-value-{value}"

    return tags


def default_metric_generator(
    idx: int, settings: Mapping[str, Any]
) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "name": "c:sessions/default@none",
        "unit": "",
        "type": "c",
        "value": idx,
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
        },
        "retention_days": 90,
    }


def session_metric_generator(
    idx: int, settings: Mapping[str, Any]
) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "name": "c:sessions/session@none",
        "unit": "",
        "type": "c",
        "value": float(idx),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "init",  # maybe cycle through all available statuses
        },
        "retention_days": 90,
    }


def user_metric_generator(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "name": "s:sessions/user@none",
        "unit": "",
        "type": "s",
        "value": _get_set(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "init",  # maybe cycle through all available statuses
        },
        "retention_days": 90,
    }


def session_error_metric_generator(
    idx: int, settings: Mapping[str, Any]
) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "name": "s:sessions/error@none",
        "unit": "",
        "type": "s",
        "value": _get_set(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "errored_preaggr",  # maybe cycle through all available statuses
        },
        "retention_days": 90,
    }


def session_duration_metric_generator(
    idx: int, settings: Mapping[str, Any]
) -> Mapping[str, Any]:
    return {
        "org_id": _get_org_id(idx, settings),
        "project_id": 1,
        "name": "d:sessions/duration@second",
        "unit": "s",
        "type": "d",
        "value": _get_distribution(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "tags": {
            **_get_tags(idx, settings),
            "session.status": "exited",  # maybe cycle through all available statuses
        },
        "retention_days": 90,
    }
