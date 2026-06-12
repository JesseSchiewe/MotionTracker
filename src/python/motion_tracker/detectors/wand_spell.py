"""Detect wand-like spell patterns from hand motion."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from motion_tracker.engine.events import MotionEvent
from motion_tracker.sensor.models import BodyFrame, Joint, JointType
from motion_tracker.utils.geometry import distance_3d


@dataclass(slots=True)
class SpellPattern:
    name: str
    directions: list[str]
    min_distance: float = 0.3
    min_points: int = 6
    similarity_threshold: float = 0.72
    min_span_x: float = 0.0
    min_span_y: float = 0.0
    max_span_x: float | None = None
    max_span_y: float | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "SpellPattern":
        return cls(
            name=str(data["name"]),
            directions=[str(item) for item in data.get("directions", [])],
            min_distance=float(data.get("min_distance", 0.3)),
            min_points=int(data.get("min_points", 6)),
            similarity_threshold=float(data.get("similarity_threshold", 0.72)),
            min_span_x=float(data.get("min_span_x", 0.0)),
            min_span_y=float(data.get("min_span_y", 0.0)),
            max_span_x=(float(data["max_span_x"]) if "max_span_x" in data else None),
            max_span_y=(float(data["max_span_y"]) if "max_span_y" in data else None),
        )


class WandSpellDetector:
    def __init__(
        self,
        patterns: Iterable[SpellPattern],
        history_size: int = 20,
        active_hand: JointType = JointType.HAND_RIGHT,
        refractory_ms: int = 1500,
        min_step: float = 0.03,
    ) -> None:
        self.patterns = list(patterns)
        self.history_size = history_size
        self.active_hand = active_hand
        self.refractory_ms = refractory_ms
        self.min_step = min_step
        self._history: dict[int, deque[Joint]] = defaultdict(lambda: deque(maxlen=self.history_size))
        self._last_emit_ms: dict[int, int] = defaultdict(lambda: -10_000_000)

    def process_frame(self, frame: BodyFrame) -> list[MotionEvent]:
        events: list[MotionEvent] = []
        seen_ids: set[int] = set()

        for body in frame.bodies:
            seen_ids.add(body.tracking_id)
            hand = body.get_joint(self.active_hand)
            if hand is None or not hand.tracked:
                self._history.pop(body.tracking_id, None)
                continue

            history = self._history[body.tracking_id]
            history.append(hand)
            spell = self._match_spell(list(history))
            if spell is None:
                continue
            if frame.timestamp_ms - self._last_emit_ms[body.tracking_id] < self.refractory_ms:
                continue

            self._last_emit_ms[body.tracking_id] = frame.timestamp_ms
            history.clear()
            events.append(
                MotionEvent(
                    name="spell_detected",
                    timestamp_ms=frame.timestamp_ms,
                    payload={
                        "spell_name": spell.name,
                        "tracking_id": body.tracking_id,
                    },
                )
            )

        stale_ids = [tracking_id for tracking_id in self._history if tracking_id not in seen_ids]
        for tracking_id in stale_ids:
            self._history.pop(tracking_id, None)
        return events

    def _match_spell(self, history: list[Joint]) -> SpellPattern | None:
        if len(history) < 2:
            return None

        path_distance = sum(distance_3d(history[index - 1], history[index]) for index in range(1, len(history)))
        x_values = [point.x for point in history]
        y_values = [point.y for point in history]
        span_x = max(x_values) - min(x_values)
        span_y = max(y_values) - min(y_values)
        directions = self._quantize(history)
        if not directions:
            return None

        best_match: SpellPattern | None = None
        best_score = 0.0
        for pattern in self.patterns:
            if len(history) < pattern.min_points or path_distance < pattern.min_distance:
                continue
            if span_x < pattern.min_span_x or span_y < pattern.min_span_y:
                continue
            if pattern.max_span_x is not None and span_x > pattern.max_span_x:
                continue
            if pattern.max_span_y is not None and span_y > pattern.max_span_y:
                continue

            score = self._direction_score(pattern.directions, directions)
            if score >= pattern.similarity_threshold and score > best_score:
                best_match = pattern
                best_score = score
        return best_match

    def _direction_score(self, expected: list[str], observed: list[str]) -> float:
        if not expected:
            return 0.0

        expanded_expected = self._expand_diagonal_tokens(expected)
        expanded_observed = self._expand_diagonal_tokens(observed)
        index = 0
        matched = 0
        for token in expanded_expected:
            while index < len(expanded_observed) and expanded_observed[index] != token:
                index += 1
            if index == len(expanded_observed):
                break
            matched += 1
            index += 1

        return matched / len(expanded_expected)

    def _expand_diagonal_tokens(self, tokens: list[str]) -> list[str]:
        expanded: list[str] = []
        for token in tokens:
            if token == "up_right":
                values = ["up", "right"]
            elif token == "down_right":
                values = ["down", "right"]
            elif token == "up_left":
                values = ["up", "left"]
            elif token == "down_left":
                values = ["down", "left"]
            else:
                values = [token]

            for value in values:
                if not expanded or expanded[-1] != value:
                    expanded.append(value)
        return expanded

    def _quantize(self, history: list[Joint]) -> list[str]:
        tokens: list[str] = []
        for index in range(1, len(history)):
            previous = history[index - 1]
            current = history[index]
            dx = current.x - previous.x
            dy = current.y - previous.y
            if abs(dx) < self.min_step and abs(dy) < self.min_step:
                continue
            if abs(dx) > abs(dy) * 1.5:
                token = "right" if dx > 0 else "left"
            elif abs(dy) > abs(dx) * 1.5:
                token = "up" if dy > 0 else "down"
            else:
                if dx > 0 and dy > 0:
                    token = "up_right"
                elif dx > 0 and dy < 0:
                    token = "down_right"
                elif dx < 0 and dy > 0:
                    token = "up_left"
                else:
                    token = "down_left"
            if not tokens or tokens[-1] != token:
                tokens.append(token)
        return tokens
