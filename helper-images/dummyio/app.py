import asyncio
import os

SLEEP_TIME = int(os.environ.get("REQ_SLEEP", 10)) / 1000


async def app(scope, proto):
    body = await proto()
    await asyncio.sleep(SLEEP_TIME)
    content_type = scope.headers.get("content-type", "application/json")
    body = body or b"{}"
    proto.response_bytes(
        200,
        [('content-type', content_type), ("content-length", str(len(body)))],
        body
    )
