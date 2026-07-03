# MotionTracker

MotionTracker is a Windows-first escape room motion tracking system built around Kinect v2.

## Goals

- Detect wand-like spell gestures from tracked hand motion.
- Detect multi-person body poses such as an X stance.
- Trigger puzzle outputs such as local audio cues and future unlock integrations.

## Architecture

The project is split into two parts:

- `src/python`: Python application for motion processing, gesture detection, puzzle rules, and outputs.
- `src/bridge`: C# Kinect v2 bridge that talks to the installed Kinect SDK and streams body frames to the Python app.

The bridge is scaffolded in this repository, but the Python app is the first runnable milestone.

## Current status

This repository currently contains the foundational Python package layout and the first implementation scaffolding for live and replay body-frame processing.

## Run the bridge and app

### Prerequisites

- Windows machine with Kinect v2 sensor connected.
- Kinect for Windows SDK v2 installed.
- .NET SDK installed (for `dotnet build`).
- Python 3.10+ installed.

### 1) Build the Kinect bridge

From the repository root:

```powershell
cd src/bridge/KinectBridge
dotnet build -c Release
```

Expected output executable:

```text
src/bridge/KinectBridge/bin/Release/net472/KinectBridge.exe
```

### 2) Start the Kinect bridge

You can run from the bridge folder:

```powershell
cd src/bridge/KinectBridge
.\bin\Release\net472\KinectBridge.exe
```

Or run by absolute path from anywhere:

```powershell
& "C:\GitRepos\MotionTracker\src\bridge\KinectBridge\bin\Release\net472\KinectBridge.exe"
```

If you see `Bridge running. Press Enter to stop.`, the bridge is ready.

### 3) Start the Python app in live mode

From the repository root:

```powershell
$env:PYTHONPATH = "src/python"
python -m motion_tracker.main --live
```

Note: `--live` is explicit and is not the default mode.

### 3b) Forward detected events to another local app

To send every detected spell/pose event to an HTTP endpoint:

```powershell
$env:PYTHONPATH = "src/python"
python -m motion_tracker.main --live --event-webhook-url http://127.0.0.1:5000/motion-events
```

JSON payload sent per event:

```json
{
	"event_name": "spell_detected",
	"timestamp_ms": 1718271200123,
	"payload": {
		"spell_name": "accio",
		"tracking_id": "1234"
	}
}
```

For pose events, `payload` contains:

```json
{
	"pose_name": "x_pose",
	"tracking_ids": ["1234"],
	"held_ms": 1028
}
```

If your receiver runs in Docker on the same machine:

- Publish the container port to host port 5000 (for example `-p 5000:5000`).
- Bind your server to `0.0.0.0` inside the container.
- Expose a POST route (for example `/motion-events`) that accepts JSON.

### 4) Run with recorded replay data

```powershell
$env:PYTHONPATH = "src/python"
python -m motion_tracker.main --replay path\to\recording.jsonl
```

### 5) One-frame smoke test

With the bridge already running, this confirms Python can read live frames:

```powershell
$env:PYTHONPATH = "src/python"
python -c "from motion_tracker.sensor.bridge_client import BridgeBodyFrameSource; src = BridgeBodyFrameSource(); frame = next(src.iter_frames()); print('smoke_ok frame_index=', frame.frame_index, 'bodies=', len(frame.bodies))"
```

### 6) Wait for tracked body smoke test

With the bridge running and someone in view, this waits up to 25 seconds for a tracked body:

```powershell
$env:PYTHONPATH = "src/python"
python -c "import time; from motion_tracker.sensor.bridge_client import BridgeBodyFrameSource; src = BridgeBodyFrameSource(); deadline = time.time() + 25; frames = 0; found = None; it = src.iter_frames();
while time.time() < deadline:
	frame = next(it)
	frames += 1
	if len(frame.bodies) > 0:
		found = frame
		break
if found is None:
	print('stream_active_frames=', frames, 'body_count_always_zero')
else:
	ids = [b.tracking_id for b in found.bodies]
	print('body_detected frame_index=', found.frame_index, 'count=', len(ids), 'tracking_ids=', ids)"
```

## Common startup issue

If PowerShell says:

```text
The term '.\bin\Release\net472\KinectBridge.exe' is not recognized
```

you are likely in the wrong working directory. Either `cd src/bridge/KinectBridge` first or use the absolute executable path.

## Configuring spells

Spells are defined in [`config/spells.json`](config/spells.json).

### Top-level properties

| Property | Description |
|---|---|
| `history_size` | Number of Kinect frames of hand position kept in the rolling window. At 30 FPS, `20` = ~0.67 seconds of motion. |
| `refractory_ms` | Minimum milliseconds before the same person can trigger any spell again. Prevents a gesture firing twice. |
| `axis_dominance_ratio` | Direction quantization sensitivity. Higher values classify more strokes as diagonal (instead of forcing `up/down/left/right`). Useful when diagonal spells are hard to trigger. |
| `min_caster_distance_m` | Minimum hand distance from camera (meters) required before any spell tracking runs. `0.9144` = 3 feet. |
| `active_caster_mode` | Which bodies are evaluated for spells. `all` checks every tracked person. `nearest` only checks the closest tracked wand hand (recommended in crowded scenes). |
| `active_caster_lost_timeout_ms` | When using `nearest`, how long to keep the current active caster if hand tracking drops out before selecting another person. |

### Per-pattern properties

| Property | Description |
|---|---|
| `name` | Identifier for the spell. Matched in `config/rules.json` via `"spell_name": "..."`. |
| `directions` | Expected sequence of movement tokens the hand must trace in order. Valid tokens: `up`, `down`, `left`, `right`, `up_right`, `down_right`, `up_left`, `down_left`. Matching is in-order and tolerant — extra tokens between expected ones are allowed, and diagonals expand (e.g. `up_right` counts toward both `up` and `right`). |
| `diagonal_mode` | *(Optional)* How diagonals are matched. `expanded` (default) lets `up_right` match as `up` + `right`. `strict` requires an actual diagonal token from quantization, which helps prevent axis-only motions from matching diagonal spells. |
| `max_direction_tokens` | *(Optional)* Maximum number of quantized direction tokens allowed in the observed motion window for this spell. Helps prevent short spells from matching inside larger, noisy movement paths. |
| `min_distance` | Minimum total hand path length in meters across the whole gesture. Guards against matching a technically correct sequence that was barely a twitch. `0.3` ≈ 30 cm arc. |
| `min_points` | Minimum number of Kinect frames required in the history window before matching is attempted. Lower = faster reaction but more noise-prone. |
| `similarity_threshold` | Fraction of expected direction tokens that must appear in order. `1.0` = all tokens must match exactly. `0.75` = 3 out of 4 is enough. |
| `min_span_x` | Minimum horizontal spread (meters) between the leftmost and rightmost hand positions. Blocks up/down motions from matching spells that need lateral movement. |
| `min_span_y` | Minimum vertical spread (meters). Blocks horizontal drifts from triggering up/down spells. |
| `max_span_x` | *(Optional)* Maximum allowed horizontal spread. Use for spells that should stay predominantly vertical (e.g. `lumos`, `nox`). |
| `max_span_y` | *(Optional)* Maximum allowed vertical spread. Useful for wide-horizontal-only spells. |

### Tuning quick reference

| Goal | Change |
|---|---|
| Spell fires too easily | Increase `min_distance`, `min_span_x/y`, or `similarity_threshold` |
| Spell never detects | Decrease `similarity_threshold`, `min_distance`, or `min_points` |
| Spell fires from small jitter | Add or increase `min_span_x/y`, increase `min_distance` |
| Spell fires from broad movements you don't want | Add `max_span_x` or `max_span_y` |
| Spell overlaps with another | Increase `similarity_threshold` on the more specific one, or make `directions` sequences more distinct |
