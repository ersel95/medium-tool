"""SSE (Server-Sent Events) stream helpers."""

from __future__ import annotations

import json
from typing import Any


def sse_event(event: str, data: Any = None) -> dict:
    """Create an SSE event dict for sse-starlette."""
    payload: dict[str, str] = {"event": event}
    if data is not None:
        payload["data"] = json.dumps(data, default=str)
    else:
        payload["data"] = ""
    return payload
