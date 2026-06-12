"""Detect multi-person X-shaped poses from skeleton joints."""

from __future__ import annotations

from dataclasses import dataclass

from motion_tracker.engine.events import MotionEvent
from motion_tracker.sensor.models import Body, BodyFrame, JointType


@dataclass(slots=True)
class XPoseConfig:
    required_people: int = 2
    hold_ms: int = 1200
    min_arm_extension: float = 0.2
    min_leg_extension: float = 0.15
    min_hand_raise: float = 0.02

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> "XPoseConfig":
        return cls(
            required_people=int(data.get("required_people", 2)),
            hold_ms=int(data.get("hold_ms", 1200)),
            min_arm_extension=float(data.get("min_arm_extension", 0.2)),
            min_leg_extension=float(data.get("min_leg_extension", 0.15)),
            min_hand_raise=float(data.get("min_hand_raise", 0.02)),
        )


class XPoseDetector:
    def __init__(self, config: XPoseConfig) -> None:
        self.config = config
        self._started_at_ms: int | None = None
        self._active = False

    def process_frame(self, frame: BodyFrame) -> list[MotionEvent]:
        qualifying = [body.tracking_id for body in frame.bodies if self._is_x_pose(body)]
        if len(qualifying) < self.config.required_people:
            self._started_at_ms = None
            self._active = False
            return []

        if self._started_at_ms is None:
            self._started_at_ms = frame.timestamp_ms
            return []

        held_ms = frame.timestamp_ms - self._started_at_ms
        if self._active or held_ms < self.config.hold_ms:
            return []

        self._active = True
        return [
            MotionEvent(
                name="pose_detected",
                timestamp_ms=frame.timestamp_ms,
                payload={
                    "pose_name": "x_pose",
                    "tracking_ids": qualifying,
                    "held_ms": held_ms,
                },
            )
        ]

    def _is_x_pose(self, body: Body) -> bool:
        required = (
            JointType.SHOULDER_LEFT,
            JointType.HAND_LEFT,
            JointType.SHOULDER_RIGHT,
            JointType.HAND_RIGHT,
            JointType.HIP_LEFT,
            JointType.FOOT_LEFT,
            JointType.HIP_RIGHT,
            JointType.FOOT_RIGHT,
        )
        if not body.has_joints(*required):
            return False

        shoulder_left = body.get_joint(JointType.SHOULDER_LEFT)
        hand_left = body.get_joint(JointType.HAND_LEFT)
        shoulder_right = body.get_joint(JointType.SHOULDER_RIGHT)
        hand_right = body.get_joint(JointType.HAND_RIGHT)
        hip_left = body.get_joint(JointType.HIP_LEFT)
        foot_left = body.get_joint(JointType.FOOT_LEFT)
        hip_right = body.get_joint(JointType.HIP_RIGHT)
        foot_right = body.get_joint(JointType.FOOT_RIGHT)
        assert shoulder_left and hand_left and shoulder_right and hand_right
        assert hip_left and foot_left and hip_right and foot_right

        left_arm_ok = (shoulder_left.x - hand_left.x) >= self.config.min_arm_extension and (hand_left.y - shoulder_left.y) >= self.config.min_hand_raise
        right_arm_ok = (hand_right.x - shoulder_right.x) >= self.config.min_arm_extension and (hand_right.y - shoulder_right.y) >= self.config.min_hand_raise
        left_leg_ok = (hip_left.x - foot_left.x) >= self.config.min_leg_extension
        right_leg_ok = (foot_right.x - hip_right.x) >= self.config.min_leg_extension
        return left_arm_ok and right_arm_ok and left_leg_ok and right_leg_ok
