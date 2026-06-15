from __future__ import annotations

import hashlib
import json
from typing import Any

KNOWN_EVENT_ID_KEYS = (
    "event_id",
    "eventId",
    "external_event_id",
    "externalEventId",
    "id",
    "message_id",
)


def extract_external_event_id(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in KNOWN_EVENT_ID_KEYS:
        value = payload.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def build_idempotency_key(vendor: str, payload: Any, external_event_id: str | None) -> str:
    if external_event_id:
        return f"external:{vendor}:{external_event_id}"
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"payload:{vendor}:{digest}"
