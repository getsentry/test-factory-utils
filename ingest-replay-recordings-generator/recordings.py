from typing import Mapping, Any
import zlib
import time
import uuid


def generate_message(
    segment_id: int,
    settings: Mapping[str, Any]
):
    message = zlib.compress(settings["message"]) if settings["compressed"] else settings["message"]
    return {
        "type": "replay_recording_not_chunked",
        "replay_id": str(uuid.uuid4()).replace("-", ""),
        "org_id": settings["org_id"],
        "key_id": 123,
        "project_id": settings["project_id"],
        "received": int(time.time()),
        "retention_days": 30,
        "payload": f'{{"segment_id":{segment_id}}}\n' + message,
    }
