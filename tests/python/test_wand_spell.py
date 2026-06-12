from __future__ import annotations

import unittest

from motion_tracker.detectors.wand_spell import SpellPattern, WandSpellDetector
from motion_tracker.sensor.models import Body, BodyFrame, Joint, JointType


class WandSpellDetectorTests(unittest.TestCase):
    def test_detects_alohomora_pattern(self) -> None:
        detector = WandSpellDetector(
            patterns=[
                SpellPattern(
                    name="alohomora",
                    directions=["right", "down", "left", "up"],
                    min_distance=0.2,
                    min_points=5,
                    similarity_threshold=0.7,
                )
            ],
            history_size=12,
            refractory_ms=500,
        )

        points = [
            (0.0, 0.0),
            (0.1, 0.0),
            (0.2, 0.0),
            (0.2, -0.1),
            (0.2, -0.2),
            (0.1, -0.2),
            (0.0, -0.2),
            (0.0, -0.1),
            (0.0, 0.0),
        ]

        events = []
        for index, (x, y) in enumerate(points):
            frame = BodyFrame(
                frame_index=index,
                timestamp_ms=index * 100,
                bodies=[
                    Body(
                        tracking_id=1,
                        joints={
                            JointType.HAND_RIGHT: Joint(x=x, y=y, z=1.0),
                        },
                    )
                ],
            )
            events.extend(detector.process_frame(frame))

        self.assertEqual(1, len(events))
        self.assertEqual("spell_detected", events[0].name)
        self.assertEqual("alohomora", events[0].payload["spell_name"])


if __name__ == "__main__":
    unittest.main()
