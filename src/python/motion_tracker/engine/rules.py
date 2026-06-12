"""Rule engine that maps detector events to outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from motion_tracker.engine.events import MotionEvent


class OutputTarget(Protocol):
    def trigger(self, action: dict[str, Any], event: MotionEvent) -> None:
        ...


@dataclass(slots=True)
class Rule:
    name: str
    event_name: str
    action: dict[str, Any]
    cooldown_ms: int = 5000
    enabled: bool = True
    match: dict[str, Any] = field(default_factory=dict)
    _last_trigger_ms: int = field(default=-10_000_000, init=False, repr=False)

    def should_fire(self, event: MotionEvent) -> bool:
        if not self.enabled or event.name != self.event_name:
            return False
        for key, value in self.match.items():
            if event.payload.get(key) != value:
                return False
        if event.timestamp_ms - self._last_trigger_ms < self.cooldown_ms:
            return False
        self._last_trigger_ms = event.timestamp_ms
        return True


class RuleEngine:
    def __init__(self, rules: list[Rule], output: OutputTarget) -> None:
        self.rules = rules
        self.output = output

    def handle(self, event: MotionEvent) -> None:
        for rule in self.rules:
            if rule.should_fire(event):
                self.output.trigger(rule.action, event)
