"""Shared body-frame models used by frame sources and detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JointType(str, Enum):
    HEAD = "head"
    NECK = "neck"
    SPINE_SHOULDER = "spine_shoulder"
    SPINE_MID = "spine_mid"
    SPINE_BASE = "spine_base"
    SHOULDER_LEFT = "shoulder_left"
    ELBOW_LEFT = "elbow_left"
    HAND_LEFT = "hand_left"
    SHOULDER_RIGHT = "shoulder_right"
    ELBOW_RIGHT = "elbow_right"
    HAND_RIGHT = "hand_right"
    HIP_LEFT = "hip_left"
    KNEE_LEFT = "knee_left"
    ANKLE_LEFT = "ankle_left"
    FOOT_LEFT = "foot_left"
    HIP_RIGHT = "hip_right"
    KNEE_RIGHT = "knee_right"
    ANKLE_RIGHT = "ankle_right"
    FOOT_RIGHT = "foot_right"


@dataclass(slots=True)
class Joint:
    x: float
    y: float
    z: float
    tracked: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Joint":
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            z=float(data.get("z", 0.0)),
            tracked=bool(data.get("tracked", True)),
        )


@dataclass(slots=True)
class Body:
    tracking_id: int
    joints: dict[JointType, Joint] = field(default_factory=dict)
    hand_state_left: str = "unknown"
    hand_state_right: str = "unknown"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Body":
        joints = {
            JointType(key): Joint.from_mapping(value)
            for key, value in data.get("joints", {}).items()
            if key in JointType._value2member_map_
        }
        return cls(
            tracking_id=int(data["tracking_id"]),
            joints=joints,
            hand_state_left=str(data.get("hand_state_left", "unknown")),
            hand_state_right=str(data.get("hand_state_right", "unknown")),
        )

    def get_joint(self, joint_type: JointType) -> Joint | None:
        return self.joints.get(joint_type)

    def has_joints(self, *joint_types: JointType) -> bool:
        return all(joint_type in self.joints and self.joints[joint_type].tracked for joint_type in joint_types)


@dataclass(slots=True)
class BodyFrame:
    frame_index: int
    timestamp_ms: int
    bodies: list[Body] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "BodyFrame":
        bodies = [Body.from_mapping(item) for item in data.get("bodies", [])]
        return cls(
            frame_index=int(data.get("frame_index", 0)),
            timestamp_ms=int(data["timestamp_ms"]),
            bodies=bodies,
        )
