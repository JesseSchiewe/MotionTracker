"""Windows audio output adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import winsound

from motion_tracker.engine.events import MotionEvent

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency fallback
    pyttsx3 = None


class AudioOutput:
    def trigger(self, action: dict[str, Any], event: MotionEvent) -> None:
        action_type = action.get("type", "beep")
        if action_type == "wave":
            path = action.get("path")
            if path and Path(path).exists():
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
        elif action_type == "speech":
            self._speak(action, event)
            return
        elif action_type == "text":
            print(f"AUDIO TEXT: {action.get('message', '')} for {event.name}")
            winsound.MessageBeep(winsound.MB_OK)
            return

        frequency = int(action.get("frequency", 1200))
        duration = int(action.get("duration_ms", 300))
        winsound.Beep(frequency, duration)

    def _speak(self, action: dict[str, Any], event: MotionEvent) -> None:
        if pyttsx3 is None:
            message = self._render_speech_text(action, event)
            print(f"SPEECH (fallback): {message}")
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return

        message = self._render_speech_text(action, event)
        rate = action.get("rate")
        volume = action.get("volume")
        voice_contains = str(action.get("voice_contains", "")).strip().lower()

        try:
            # Recreate the engine each utterance to avoid intermittent one-shot failures.
            engine = pyttsx3.init()
            if rate is not None:
                engine.setProperty("rate", int(rate))
            if volume is not None:
                engine.setProperty("volume", max(0.0, min(1.0, float(volume))))
            if voice_contains:
                for voice in engine.getProperty("voices"):
                    name = str(getattr(voice, "name", "")).lower()
                    voice_id = str(getattr(voice, "id", "")).lower()
                    if voice_contains in name or voice_contains in voice_id:
                        engine.setProperty("voice", voice.id)
                        break

            engine.say(message)
            engine.runAndWait()
            engine.stop()
        except Exception:
            print(f"SPEECH ERROR (fallback text): {message}")
            winsound.MessageBeep(winsound.MB_ICONASTERISK)

    def _render_speech_text(self, action: dict[str, Any], event: MotionEvent) -> str:
        template = str(action.get("message_template", "{spell_name}"))
        payload = dict(event.payload)
        payload.setdefault("event_name", event.name)
        try:
            return template.format(**payload)
        except Exception:
            return template
