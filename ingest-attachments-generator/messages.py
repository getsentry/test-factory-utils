import json
import random
from typing import Mapping, Any, Optional
import uuid

import msgpack


def generate_attachment_payload(settings: Mapping[str, Any]) -> bytes:
    # TODO: Make min/max size configurable?
    payload = "".join([chr(random.randint(0, 255)) for _ in range(1000)]).encode("utf-8")
    return payload


def generate_event_messages(idx: int, settings: Mapping[str, Any], payload: bytes):
    event_id = _get_event_id(idx, settings)
    attachment_id = _get_attachment_id(idx, settings)
    project_id = _get_project_id(idx, settings)

    chunk_headers = {
        "event_id": event_id,
        "project_id": project_id,
        "id": attachment_id,
        "chunk_index": 0,  # TODO: Split file into multiple chunks?
    }

    yield _create_msgpack_wrapper("attachment_chunk", chunk_headers, payload)

    event = {
        "type": "default",
        "event_id": event_id,
        "project": project_id,
        "timestamp": _get_timestamp(idx, settings),
        "platform": "other",
    }

    event_headers = {
        "start_time": _get_start_time(idx, settings),
        "event_id": event_id,
        "project_id": project_id,
        "remote_addr": None,
        "attachments": [{
            "id": attachment_id,
            "name": "test.txt",
            "content_type": "text/plain",
            "attachment_type": "event.attachment",
            "chunks": 1,
            "size": 1000,
            "rate_limited": False,
        }],
    }

    event_payload = json.dumps(event).encode("utf-8")
    yield _create_msgpack_wrapper("event", event_headers, event_payload)


def _create_msgpack_wrapper(ty: str, headers: Mapping[str, Any], payload: Optional[bytes]) -> bytes:
    message = {**headers, "type": ty}

    if payload is not None:
        message["payload"] = payload

    return msgpack.packb(message)


def _get_project_id(idx: int, settings: Mapping[str, Any]) -> int:
    projects = settings["projects"]

    proj_idx = random.randint(0, len(projects) - 1)
    return projects[proj_idx]


def _get_event_id(idx: int, settings: Mapping[str, Any]) -> str:
    return uuid.uuid4().hex


def _get_attachment_id(idx: int, settings: Mapping[str, Any]) -> str:
    return uuid.uuid4().hex


def _get_timestamp(idx: int, settings: Mapping[str, Any]) -> int:
    base_seconds = int(settings["time_delta"].total_seconds())
    offset = random.randint(0, base_seconds)
    timestamp = settings["timestamp"] - offset
    return timestamp


def _get_start_time(idx: int, settings: Mapping[str, Any]) -> int:
    return settings["timestamp"]
