"""Application entry point for MotionTracker."""

from __future__ import annotations

import argparse
from pathlib import Path

from motion_tracker.app import MotionTrackerApp, build_detectors, build_rule_engine
from motion_tracker.sensor.bridge_client import BridgeBodyFrameSource


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MotionTracker runner")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--replay", type=Path, help="Path to a JSON or JSONL body-frame recording")
    source_group.add_argument("--live", action="store_true", help="Read live frames from the local Kinect bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Kinect bridge host")
    parser.add_argument("--port", type=int, default=9001, help="Kinect bridge TCP port")
    parser.add_argument("--spells", type=Path, default=Path("config/spells.json"), help="Spell detector config path")
    parser.add_argument("--poses", type=Path, default=Path("config/poses.json"), help="Pose detector config path")
    parser.add_argument("--rules", type=Path, default=Path("config/rules.json"), help="Rule config path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    app = MotionTrackerApp(
        detectors=build_detectors(args.spells, args.poses),
        rule_engine=build_rule_engine(args.rules),
    )

    if args.replay is not None:
        events = app.run_replay(args.replay)
        if not events:
            print("No events detected")
            return 0
        for event in events:
            print(f"{event.timestamp_ms}: {event.name} {event.payload}")
        return 0

    if args.live:
        source = BridgeBodyFrameSource(host=args.host, port=args.port)
        print(f"Listening for Kinect bridge frames on {args.host}:{args.port}")
        for frame in source.iter_frames():
            for event in app.process_frame(frame):
                print(f"{event.timestamp_ms}: {event.name} {event.payload}")
        return 0

    print("MotionTracker bootstrap ready. Use --replay or --live.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
