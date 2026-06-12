"""Replay body frames from JSON files for offline detector development."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from motion_tracker.sensor.models import BodyFrame


class ReplayBodyFrameSource:
    """Load recorded body frames from a JSON list or JSONL file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def iter_frames(self) -> Iterator[BodyFrame]:
        text = self.path.read_text(encoding="utf-8")
        stripped = text.lstrip()
        if stripped.startswith("["):
            payload = json.loads(text)
            for frame in payload:
                yield BodyFrame.from_mapping(frame)
            return

        for line in text.splitlines():
            if line.strip():
                yield BodyFrame.from_mapping(json.loads(line))
