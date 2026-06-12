"""Detect wand-like spell patterns from hand motion."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from difflib import SequenceMatcher
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

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "SpellPattern":
        return cls(
            name=str(data["name"]),
            directions=[str(item) for item in data.get("directions", [])],
            min_distance=float(data.get("min_distance", 0.3)),
            min_points=int(data.get("min_points", 6)),
            similarity_threshold=float(data.get("similarity_threshold", 0.72)),
        )


class WandSpellDetector:
    def __init__(
        self,
        patterns: Iterable[SpellPattern],
        history_size: int = 20,
        active_hand: JointType = JointType.HAND_RIGHT,
        refractory_ms: int = 1500,
    ) -> None:
        self.patterns = list(patterns)
        self.history_size = history_size
        self.active_hand = active_hand
        self.refractory_ms = refractory_ms
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
        directions = self._quantize(history)
        if not directions:
            return None

        best_match: SpellPattern | None = None
        best_score = 0.0
        for pattern in self.patterns:
            if len(history) < pattern.min_points or path_distance < pattern.min_distance:
                continue
            score = SequenceMatcher(a=pattern.directions, b=directions).ratio()
            if score >= pattern.similarity_threshold and score > best_score:
                best_match = pattern
                best_score = score
        return best_match

    def _quantize(self, history: list[Joint]) -> list[str]:
        tokens: list[str] = []
        for index in range(1, len(history)):
            previous = history[index - 1]
            current = history[index]
            dx = current.x - previous.x
            dy = current.y - previous.y
            if abs(dx) < 0.02 and abs(dy) < 0.02:
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
