from typing import Callable, Mapping, Any, List, Optional
import random
import zlib
import time

# def generate_payload(size=None):
#     """Generates a bytes JSON string with entries equal to size"""
#     if not size:
#         # this will always give a message between 53 bytes and 1MB
#         size = random.randint(1,49900) 
#     message_dict = []
#     for _ in range(size):
#         message_dict.append({"hello": "world"})
#     message = str(message_dict)
#     return bytes(message, 'utf-8')

def generate_chunked_message(
    replay_id: int,
    segment_id: int,
    chunk_index: int,
    num_chunks: int,
    settings: Mapping[str, Any]
):
    message = zlib.compress(settings["message"]) if settings["compressed"] else settings["message"]
    return [
        {
            "payload": f'{{"segment_id":{segment_id}}}\n' + message,
            "replay_id": replay_id,
            "project_id": settings["project_id"],
            "id": replay_id,
            "chunk_index": chunk_index,
            "type": "replay_recording_chunk",
            "org_id": settings["org_id"],
            "received": time.time(),
            "retention_days": 30,
            "key_id": 123,
        },
        {
            "type": "replay_recording",
            "replay_id": replay_id,
            "replay_recording": {
                "chunks": num_chunks,
                "id": replay_id,
            },
            "project_id": settings["project_id"],
            "org_id": settings["org_id"],
            "received": time.time(),
            "retention_days": 30,
        },
    ]

def generate_nonchunked_message(
    replay_id: int,
    segment_id: int,
    settings: Mapping[str, Any]
):
    message = zlib.compress(settings["message"]) if settings["compressed"] else settings["message"]
    return [{
        "type": "replay_recording_not_chunked",
        "replay_id": replay_id,
        "org_id": settings["org_id"],
        "key_id": 123,
        "project_id": settings["project_id"],
        "received": time.time(),
        "retention_days": 30,
        "payload": f'{{"segment_id":{segment_id}}}\n' + message,
    }]

def generate_message(
    send_chunked_recording: bool,
    replay_id: int,
    segment_id: int,
    settings: Mapping[str, Any],
    chunk_index=0,
    num_chunks=1
) -> List:
    if send_chunked_recording:
        return generate_chunked_message(
            replay_id=replay_id,
            segment_id=segment_id,
            settings=settings, 
            chunk_index=chunk_index,
            num_chunks=num_chunks
        )
    else:
        return generate_nonchunked_message(
            replay_id=replay_id,
            segment_id=segment_id,
            settings=settings
        )
