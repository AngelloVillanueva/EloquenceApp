"""WebSocket JSON protocol helpers for /ws/audio."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class ClientEvent(StrEnum):
    END_TURN = "END_TURN"
    CANCEL_AUDIO = "CANCEL_AUDIO"
    PING = "PING"
    CONFIG = "CONFIG"


class ServerEvent(StrEnum):
    READY = "READY"
    STATE = "STATE"
    PONG = "PONG"
    TRANSCRIPT = "TRANSCRIPT"
    TOKEN = "TOKEN"
    SENTENCE = "SENTENCE"
    FEEDBACK = "FEEDBACK"
    AUDIO_META = "AUDIO_META"
    TURN_DONE = "TURN_DONE"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class SessionState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"


def msg(event_type: str, **payload: Any) -> dict[str, Any]:
    return {"type": event_type, **payload}
