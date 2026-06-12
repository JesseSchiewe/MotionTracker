"""Geometry helpers for motion and pose checks."""

from __future__ import annotations

import math

from motion_tracker.sensor.models import Joint


def distance_3d(first: Joint, second: Joint) -> float:
    return math.sqrt((first.x - second.x) ** 2 + (first.y - second.y) ** 2 + (first.z - second.z) ** 2)


def horizontal_distance(first: Joint, second: Joint) -> float:
    return abs(first.x - second.x)


def vertical_distance(first: Joint, second: Joint) -> float:
    return abs(first.y - second.y)


def angle_from_vertical(origin: Joint, target: Joint) -> float:
    dx = target.x - origin.x
    dy = target.y - origin.y
    magnitude = math.sqrt(dx * dx + dy * dy)
    if magnitude == 0:
        return 0.0
    cosine = max(-1.0, min(1.0, dy / magnitude))
    return math.degrees(math.acos(cosine))
