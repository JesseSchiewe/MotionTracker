"""Application wiring for replay and live processing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Protocol

from motion_tracker.detectors.wand_spell import SpellPattern, WandSpellDetector
from motion_tracker.detectors.x_pose import XPoseConfig, XPoseDetector
from motion_tracker.engine.events import MotionEvent
from motion_tracker.engine.rules import Rule, RuleEngine
from motion_tracker.outputs.audio import AudioOutput
from motion_tracker.sensor.models import BodyFrame
from motion_tracker.sensor.replay import ReplayBodyFrameSource


class FrameDetector(Protocol):
    def process_frame(self, frame: BodyFrame) -> list[MotionEvent]:
        ...


class EventSink(Protocol):
    def publish(self, event: MotionEvent) -> None:
        ...


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


class MotionTrackerApp:
    def __init__(
        self,
        detectors: Iterable[FrameDetector],
        rule_engine: RuleEngine,
        event_sink: EventSink | None = None,
    ) -> None:
        self.detectors = list(detectors)
        self.rule_engine = rule_engine
        self.event_sink = event_sink

    def process_frame(self, frame: BodyFrame) -> list[MotionEvent]:
        events: list[MotionEvent] = []
        for detector in self.detectors:
            detector_events = detector.process_frame(frame)
            events.extend(detector_events)
            for event in detector_events:
                if self.event_sink is not None:
                    self.event_sink.publish(event)
                self.rule_engine.handle(event)
        return events

    def run_replay(self, path: str | Path) -> list[MotionEvent]:
        events: list[MotionEvent] = []
        for frame in ReplayBodyFrameSource(path).iter_frames():
            events.extend(self.process_frame(frame))
        return events


def build_detectors(spell_config_path: str | Path, pose_config_path: str | Path) -> list[FrameDetector]:
    spell_config = load_json(spell_config_path)
    pose_config = load_json(pose_config_path)
    spell_patterns = [SpellPattern.from_mapping(item) for item in spell_config.get("patterns", [])]
    wand_detector = WandSpellDetector(
        patterns=spell_patterns,
        history_size=int(spell_config.get("history_size", 20)),
        refractory_ms=int(spell_config.get("refractory_ms", 1500)),
    )
    pose_detector = XPoseDetector(XPoseConfig.from_mapping(pose_config))
    return [wand_detector, pose_detector]


def build_rule_engine(config_path: str | Path) -> RuleEngine:
    config = load_json(config_path)
    rules = [
        Rule(
            name=item["name"],
            event_name=item["event_name"],
            action=item["action"],
            cooldown_ms=int(item.get("cooldown_ms", 5000)),
            match=dict(item.get("match", {})),
        )
        for item in config.get("rules", [])
    ]
    return RuleEngine(rules=rules, output=AudioOutput())
