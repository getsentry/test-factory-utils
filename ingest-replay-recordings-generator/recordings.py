from typing import Mapping, Any
import zlib
import random
import time

from message_types import XSMALL_MESSAGE, SMALL_MESSAGE, MEDIUM_MESSAGE, LARGE_MESSAGE

def _get_message_size():
    n = random.randint(0, 100)
    if n < 50:
        # 236 bytes compressed
        return XSMALL_MESSAGE
    if n < 80:
        # 2KB compressed
        return SMALL_MESSAGE
    if n < 95:
        # 25KB compressed
        return MEDIUM_MESSAGE
    if n <= 100:
        # 162KB compressed
        return LARGE_MESSAGE

def generate_message(
    replay_id: str,
    segment_id: int,
    settings: Mapping[str, Any]
):
    message = zlib.compress(_get_message_size())
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
