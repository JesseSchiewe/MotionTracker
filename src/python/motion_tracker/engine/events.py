"""Event bus and event payloads for detector outputs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class MotionEvent:
    name: str
    timestamp_ms: int
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[MotionEvent], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[[MotionEvent], None]) -> None:
        self._listeners[event_name].append(callback)

    def publish(self, event: MotionEvent) -> None:
        for callback in self._listeners[event.name]:
            callback(event)
