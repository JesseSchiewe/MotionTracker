# Setup

## Python app

1. Create and activate a Python 3.10+ virtual environment.
2. From the repository root, run `python -m motion_tracker.main` with `PYTHONPATH=src/python` for source-tree execution.
3. Use `python -m unittest discover -s tests/python -p "test_*.py" -v` to run the detector tests.

## Kinect bridge

The bridge is a Visual Studio console project under `src/bridge/KinectBridge`.

Prerequisites:

- Kinect for Windows SDK v2 installed
- Kinect v2 sensor connected and recognized by the SDK tools
- Visual Studio with .NET Framework desktop development support

The project references `Microsoft.Kinect.dll` from the standard Kinect SDK install path through the `KINECTSDK20_DIR` environment variable exposed by the SDK installer.

## Current transport plan

- Kinect bridge publishes body frames as newline-delimited JSON over TCP on `127.0.0.1:9001`.
- The Python app currently supports replay-driven development and detector validation.
- Live bridge ingestion is the next implementation step on the Python side.
