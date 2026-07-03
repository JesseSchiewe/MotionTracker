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
    cooldown_scope_key: str | None = None
    enabled: bool = True
    match: dict[str, Any] = field(default_factory=dict)
    _last_trigger_ms_by_scope: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def should_fire(self, event: MotionEvent) -> bool:
        if not self.enabled or event.name != self.event_name:
            return False
        for key, value in self.match.items():
            if event.payload.get(key) != value:
                return False
        scope = self._scope_value(event)
        last_trigger_ms = self._last_trigger_ms_by_scope.get(scope, -10_000_000)
        if event.timestamp_ms - last_trigger_ms < self.cooldown_ms:
            return False
        self._last_trigger_ms_by_scope[scope] = event.timestamp_ms
        return True

    def _scope_value(self, event: MotionEvent) -> str:
        if not self.cooldown_scope_key:
            return "*"
        value = event.payload.get(self.cooldown_scope_key)
        if value is None:
            return "*"
        return str(value)


class RuleEngine:
    def __init__(self, rules: list[Rule], output: OutputTarget) -> None:
        self.rules = rules
        self.output = output

    def handle(self, event: MotionEvent) -> None:
        for rule in self.rules:
            if rule.should_fire(event):
                self.output.trigger(rule.action, event)
