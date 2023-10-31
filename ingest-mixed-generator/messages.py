import json
import random
from typing import Callable, Mapping, Any, List, Optional
import uuid

import msgpack

def generate_message(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    message_type = _get_message_type(idx, settings) or ""
    generator = _get_message_generator(message_type)

    return generator(idx, settings)


def generate_attachment_payloads(settings: Mapping[str, Any]) -> List[bytes]:
    payloads = []
    # TODO: Make min/max size configurable?
    for _i in range(settings["num_payloads"]):
        payloads.append("".join([chr(random.randint(0, 255)) for _ in range(100)]).encode("utf-8"))
    return payloads


def _get_message_type(idx: int, settings: Mapping[str, Any]) -> Optional[str]:
    types = settings["message_types"]

    if len(types) == 0:
        return None

    i = random.randint(0, len(types) - 1)
    return types[i]


def _get_message_generator(
    message_type: str,
) -> Callable[[int, Mapping[str, Any]], Mapping[str, Any]]:
    return {
        "event": event_message_generator,
        "attachment": attachment_message_generator,
        "attachment_chunk": attachment_chunk_message_generator,
        "user_report": user_report_message_generator,
    }.get(message_type, default_message_generator)


def _create_msgpack_wrapper(ty: str, headers: Mapping[str, Any], payload: Optional[bytes]) -> bytes:
    message = {**headers, "type": ty}

    if payload is not None:
        message["payload"] = payload

    return msgpack.packb(message)


def _get_event_type(idx: int, settings: Mapping[str, Any]) -> str:
    event_types = settings["event_types"]

    event_idx = random.randint(0, len(event_types) - 1)
    return event_types[event_idx]


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


def _get_default_event(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "type": "default",
        "event_id": _get_event_id(idx, settings),
        "project": _get_project_id(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "platform": "other",
    }


def _get_error_event(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "type": "error",
        "event_id": _get_event_id(idx, settings),
        "project": _get_project_id(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "platform": "other",
    }


def _get_transaction_event(idx: int, settings: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "type": "transaction",
        "event_id": _get_event_id(idx, settings),
        "project": _get_project_id(idx, settings),
        "timestamp": _get_timestamp(idx, settings),
        "platform": "other",
    }


def event_message_generator(idx: int, settings: Mapping[str, Any], event_type: Optional[str] = None) -> bytes:
    event_type = event_type or _get_event_type(idx, settings)

    event = {
        "default": _get_default_event,
        "error": _get_error_event,
        "transaction": _get_transaction_event,
    }.get(event_type, _get_default_event)(idx, settings)

    headers = {
        "start_time": _get_start_time(idx, settings),
        "event_id": event["event_id"],
        "project_id": event["project"],
        "remote_addr": None,
        "attachments": [],  # TODO: use attachment chunks here
    }

    payload = json.dumps(event).encode("utf-8")
    return _create_msgpack_wrapper("event", headers, payload)


def attachment_message_generator(idx: int, settings: Mapping[str, Any]) -> bytes:
    headers = {
        "event_id": _get_event_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "attachment": {
            "id": uuid.uuid4().hex,
            "name": "test.txt",
            "content_type": "text/plain",
            "attachment_type": "event.attachment",
            "chunks": 0,  # TODO: Use chunk runs here
            "size": 0,
            "rate_limited": False,
        }
    }

    return _create_msgpack_wrapper("attachment", headers, None)


def attachment_chunk_message_generator(idx: int, settings: Mapping[str, Any]) -> bytes:
    headers = {
        "event_id": _get_event_id(idx, settings),
        "project_id": _get_project_id(idx, settings),
        "id": uuid.uuid4().hex,
        "chunk_index": 0,  # TODO: Create variable runs of chunks
    }

    payload_len = random.randint(100, 10000)
    payload = "".join([chr(random.randint(0, 255)) for _ in range(payload_len)]).encode("utf-8")

    return _create_msgpack_wrapper("attachment_chunk", headers, payload)


def user_report_message_generator(idx: int, settings: Mapping[str, Any]) -> bytes:
    user_report = {
        "event_id": _get_event_id(idx, settings),
        "name": "John Doe",
        "email": "john.doe@example.org",
        "comments": "This is a test comment",
    }

    headers = {
        "project_id": _get_project_id(idx, settings),
        "start_time": _get_start_time(idx, settings),
        "event_id": user_report["event_id"],
    }

    payload = json.dumps(user_report).encode("utf-8")
    return _create_msgpack_wrapper("user_report", headers, payload)


def default_message_generator(idx: int, settings: Mapping[str, Any]) -> bytes:
    return event_message_generator(idx, settings, event_type="default")


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

    yield event_id, _create_msgpack_wrapper("attachment_chunk", chunk_headers, payload)

    attachment_headers = {
        "event_id": event_id,
        "project_id": project_id,
        "attachment": {
            "id": attachment_id,
            "name": "test.txt",
            "content_type": "text/plain",
            "attachment_type": "event.attachment",
            "chunks": 1,
            "size": 100,
            "rate_limited": False,
        }
    }

    yield event_id, _create_msgpack_wrapper("attachment", attachment_headers, None)

