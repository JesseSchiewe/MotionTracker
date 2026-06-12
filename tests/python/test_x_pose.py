from __future__ import annotations

import unittest

from motion_tracker.detectors.x_pose import XPoseConfig, XPoseDetector
from motion_tracker.sensor.models import Body, BodyFrame, Joint, JointType


class XPoseDetectorTests(unittest.TestCase):
    def test_detects_x_pose_after_hold(self) -> None:
        detector = XPoseDetector(XPoseConfig(required_people=2, hold_ms=1000))

        frames = [
            BodyFrame(frame_index=0, timestamp_ms=0, bodies=[self._body(1), self._body(2)]),
            BodyFrame(frame_index=1, timestamp_ms=500, bodies=[self._body(1), self._body(2)]),
            BodyFrame(frame_index=2, timestamp_ms=1200, bodies=[self._body(1), self._body(2)]),
        ]

        events = []
        for frame in frames:
            events.extend(detector.process_frame(frame))

        self.assertEqual(1, len(events))
        self.assertEqual("pose_detected", events[0].name)
        self.assertEqual("x_pose", events[0].payload["pose_name"])
        self.assertEqual([1, 2], events[0].payload["tracking_ids"])

    def _body(self, tracking_id: int) -> Body:
        return Body(
            tracking_id=tracking_id,
            joints={
                JointType.SHOULDER_LEFT: Joint(x=-0.2, y=1.5, z=1.0),
                JointType.HAND_LEFT: Joint(x=-0.5, y=1.8, z=1.0),
                JointType.SHOULDER_RIGHT: Joint(x=0.2, y=1.5, z=1.0),
                JointType.HAND_RIGHT: Joint(x=0.5, y=1.8, z=1.0),
                JointType.HIP_LEFT: Joint(x=-0.15, y=0.9, z=1.0),
                JointType.FOOT_LEFT: Joint(x=-0.4, y=0.1, z=1.0),
                JointType.HIP_RIGHT: Joint(x=0.15, y=0.9, z=1.0),
                JointType.FOOT_RIGHT: Joint(x=0.4, y=0.1, z=1.0),
            },
        )


if __name__ == "__main__":
    unittest.main()
