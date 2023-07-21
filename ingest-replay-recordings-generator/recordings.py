from typing import Callable, Mapping, Any, List, Optional
import random
import zlib
import time


def generate_message(
    replay_id: int,
    segment_id: int,
    settings: Mapping[str, Any]
):
    message = zlib.compress(settings["message"]) if settings["compressed"] else settings["message"]
    return {
        "type": "replay_recording_not_chunked",
        "replay_id": replay_id,
        "org_id": settings["org_id"],
        "key_id": 123,
        "project_id": settings["project_id"],
        "received": int(time.time()),
        "retention_days": 30,
        "payload": f'{{"segment_id":{segment_id}}}\n' + message,
    }
