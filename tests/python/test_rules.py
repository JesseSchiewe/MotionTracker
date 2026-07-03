from __future__ import annotations

import unittest

from motion_tracker.engine.events import MotionEvent
from motion_tracker.engine.rules import Rule


class RuleTests(unittest.TestCase):
    def test_cooldown_scope_key_applies_cooldown_per_payload_value(self) -> None:
        rule = Rule(
            name="spell-voice-announce",
            event_name="spell_detected",
            action={"type": "speech"},
            cooldown_ms=1000,
            cooldown_scope_key="spell_name",
        )

        event_accio_0 = MotionEvent(
            name="spell_detected",
            timestamp_ms=1000,
            payload={"spell_name": "accio"},
        )
        event_incendio_100 = MotionEvent(
            name="spell_detected",
            timestamp_ms=1100,
            payload={"spell_name": "incendio"},
        )
        event_accio_200 = MotionEvent(
            name="spell_detected",
            timestamp_ms=1200,
            payload={"spell_name": "accio"},
        )

        self.assertTrue(rule.should_fire(event_accio_0))
        self.assertTrue(rule.should_fire(event_incendio_100))
        self.assertFalse(rule.should_fire(event_accio_200))


if __name__ == "__main__":
    unittest.main()
