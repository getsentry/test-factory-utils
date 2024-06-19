import asyncio
import os

SLEEP_TIME = int(os.environ.get("REQ_SLEEP", 10)) / 1000
RES_STATUS = int(os.environ.get("RES_STATUS", 200))
ECHO_MODE = os.environ.get("ECHO_MODE") == "true"
STATIC_HEADERS = [('content-type', "application/json"), ("content-length", "2")]
STATIC_BODY = b"{}"


async def app(scope, proto):
    await asyncio.sleep(SLEEP_TIME)

    headers = STATIC_HEADERS
    body = STATIC_BODY

    if ECHO_MODE:
        body = (await proto()) or body
        content_type = scope.headers.get("content-type", "application/json")
        headers = [('content-type', content_type), ("content-length", str(len(body)))]

    proto.response_bytes(
        RES_STATUS,
        headers,
        body
    )
