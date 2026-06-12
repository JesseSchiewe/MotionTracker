"""TCP client for live body-frame ingestion from the Kinect bridge."""

from __future__ import annotations

import json
import socket
from contextlib import closing
from typing import Iterator

from motion_tracker.sensor.models import BodyFrame


class BridgeBodyFrameSource:
    def __init__(self, host: str = "127.0.0.1", port: int = 9001, timeout_s: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout_s = timeout_s

    def iter_frames(self) -> Iterator[BodyFrame]:
        with closing(socket.create_connection((self.host, self.port), timeout=self.timeout_s)) as sock:
            with sock.makefile("r", encoding="utf-8") as reader:
                for line in reader:
                    payload = line.strip()
                    if not payload:
                        continue
                    yield BodyFrame.from_mapping(json.loads(payload))
