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

    def test_nearest_mode_ignores_farther_body_spell(self) -> None:
        detector = WandSpellDetector(
            patterns=[
                SpellPattern(
                    name="right_sweep",
                    directions=["right"],
                    min_distance=0.2,
                    min_points=4,
                    similarity_threshold=1.0,
                    min_span_x=0.2,
                )
            ],
            history_size=8,
            refractory_ms=200,
            active_caster_mode="nearest",
        )

        events = []
        farther_points = [0.0, 0.1, 0.2, 0.3, 0.4]
        for index, x in enumerate(farther_points):
            frame = BodyFrame(
                frame_index=index,
                timestamp_ms=index * 100,
                bodies=[
                    Body(
                        tracking_id=1,
                        joints={JointType.HAND_RIGHT: Joint(x=x, y=0.0, z=2.0)},
                    ),
                    Body(
                        tracking_id=2,
                        joints={JointType.HAND_RIGHT: Joint(x=0.0, y=0.0, z=1.0)},
                    ),
                ],
            )
            events.extend(detector.process_frame(frame))

        self.assertEqual([], events)

    def test_strict_diagonal_mode_requires_true_diagonal_token(self) -> None:
        detector = WandSpellDetector(
            patterns=[
                SpellPattern(
                    name="diag_spell",
                    directions=["down_right", "left"],
                    diagonal_mode="strict",
                    min_distance=0.15,
                    min_points=4,
                    similarity_threshold=1.0,
                    min_span_x=0.12,
                    min_span_y=0.05,
                )
            ],
            history_size=10,
            refractory_ms=300,
        )

        # Axis-only path: down, right, left. This should not satisfy down_right in strict mode.
        points = [
            (0.0, 0.0),
            (0.0, -0.12),
            (0.12, -0.12),
            (0.0, -0.12),
        ]
        events = []
        for index, (x, y) in enumerate(points):
            frame = BodyFrame(
                frame_index=index,
                timestamp_ms=index * 100,
                bodies=[
                    Body(
                        tracking_id=1,
                        joints={JointType.HAND_RIGHT: Joint(x=x, y=y, z=1.0)},
                    )
                ],
            )
            events.extend(detector.process_frame(frame))

        self.assertEqual([], events)

    def test_expanded_diagonal_mode_accepts_axis_subsequence(self) -> None:
        detector = WandSpellDetector(
            patterns=[
                SpellPattern(
                    name="diag_spell",
                    directions=["down_right", "left"],
                    diagonal_mode="expanded",
                    min_distance=0.15,
                    min_points=4,
                    similarity_threshold=1.0,
                    min_span_x=0.12,
                    min_span_y=0.05,
                )
            ],
            history_size=10,
            refractory_ms=300,
        )

        # Same path as strict test, but expansion should allow down_right to match as down + right.
        points = [
            (0.0, 0.0),
            (0.0, -0.12),
            (0.12, -0.12),
            (0.0, -0.12),
        ]
        events = []
        for index, (x, y) in enumerate(points):
            frame = BodyFrame(
                frame_index=index,
                timestamp_ms=index * 100,
                bodies=[
                    Body(
                        tracking_id=1,
                        joints={JointType.HAND_RIGHT: Joint(x=x, y=y, z=1.0)},
                    )
                ],
            )
            events.extend(detector.process_frame(frame))

        self.assertEqual(1, len(events))
        self.assertEqual("diag_spell", events[0].payload["spell_name"])


if __name__ == "__main__":
    unittest.main()
