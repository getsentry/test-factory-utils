from typing import Mapping, Any
import zlib
import time


def generate_message(
    replay_id: int,
    segment_id: int,
    settings: Mapping[str, Any]
):
    bytes_msg = bytes(settings["message"], "utf-8")
    message = zlib.compress(bytes_msg) if settings["compressed"] else bytes_msg
    return {
        "type": "replay_recording_not_chunked",
        "replay_id": replay_id,
        "org_id": settings["org_id"],
        "key_id": 123,
        "project_id": settings["project_id"],
        "received": int(time.time()),
        "retention_days": 30,
        "payload": f'{{"segment_id":{segment_id}}}\n'.encode() + message,
    }
