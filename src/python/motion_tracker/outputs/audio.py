"""Windows audio output adapter."""

from __future__ import annotations

from pathlib import Path
import winsound

from motion_tracker.engine.events import MotionEvent


class AudioOutput:
    def trigger(self, action: dict[str, str], event: MotionEvent) -> None:
        action_type = action.get("type", "beep")
        if action_type == "wave":
            path = action.get("path")
            if path and Path(path).exists():
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
        elif action_type == "text":
            print(f"AUDIO TEXT: {action.get('message', '')} for {event.name}")
            winsound.MessageBeep(winsound.MB_OK)
            return

        frequency = int(action.get("frequency", 1200))
        duration = int(action.get("duration_ms", 300))
        winsound.Beep(frequency, duration)
