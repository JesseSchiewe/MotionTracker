"""Latest-frame buffering for sensor and replay sources."""

from __future__ import annotations

from collections import deque
from threading import Lock

from motion_tracker.sensor.models import BodyFrame


class FrameBuffer:
    """Thread-safe fixed-size buffer for recent body frames."""

    def __init__(self, maxlen: int = 10) -> None:
        self._frames: deque[BodyFrame] = deque(maxlen=maxlen)
        self._lock = Lock()

    def push(self, frame: BodyFrame) -> None:
        with self._lock:
            self._frames.append(frame)

    def latest(self) -> BodyFrame | None:
        with self._lock:
            return self._frames[-1] if self._frames else None

    def snapshot(self) -> list[BodyFrame]:
        with self._lock:
            return list(self._frames)
