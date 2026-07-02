"""Webhook output adapter for forwarding detector events to external apps."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from motion_tracker.engine.events import MotionEvent


@dataclass(slots=True)
class WebhookEventSink:
    url: str
    timeout_seconds: float = 0.5

    def publish(self, event: MotionEvent) -> None:
        normalized_payload = dict(event.payload)
        if "tracking_id" in normalized_payload:
            tracking_id = normalized_payload.get("tracking_id")
            if tracking_id is not None:
                normalized_payload["tracking_id"] = str(tracking_id)
        if "tracking_ids" in normalized_payload:
            tracking_ids = normalized_payload.get("tracking_ids")
            if isinstance(tracking_ids, list):
                normalized_payload["tracking_ids"] = [str(item) for item in tracking_ids if item is not None]

        payload: dict[str, Any] = {
            "event_name": event.name,
            "timestamp_ms": event.timestamp_ms,
            "payload": normalized_payload,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=self.url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    print(f"Webhook returned HTTP {status} for event {event.name}")
        except error.URLError as exc:
            print(f"Webhook send failed for event {event.name}: {exc}")
