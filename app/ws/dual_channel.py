"""Split LLM stream into spoken text (TTS) vs feedback JSON (sidebar)."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_SPEAK_OPEN = "<<<SPEAK>>>"
_FEEDBACK_OPEN = "<<<FEEDBACK>>>"
# Tolerate minor variants models sometimes emit.
_FEEDBACK_RE = re.compile(r"<<<\s*FEEDBACK(?:_JSON)?\s*>>>", re.IGNORECASE)
_SPEAK_RE = re.compile(r"<<<\s*SPEAK\s*>>>", re.IGNORECASE)


class DualChannelSplitter:
    """
    Streaming splitter:
      <<<SPEAK>>> ...spoken... <<<FEEDBACK>>> {...json...}

    Only SPEAK text is yielded for TTS. FEEDBACK is buffered until flush().
    If markers are missing, the whole stream is treated as SPEAK (safe fallback).
    """

    def __init__(self) -> None:
        self._mode: str = "speak"  # speak | feedback
        self._carry = ""
        self._feedback_raw = ""
        self._saw_speak_marker = False
        self._saw_feedback_marker = False

    def push(self, delta: str) -> str:
        """Return text that belongs to the spoken channel (may be empty)."""
        if not delta:
            return ""
        self._carry += delta
        spoken = ""

        while self._carry:
            if self._mode == "speak":
                m_fb = _FEEDBACK_RE.search(self._carry)
                m_sp = _SPEAK_RE.search(self._carry)

                # Strip leading SPEAK marker once
                if m_sp and m_sp.start() == 0:
                    self._saw_speak_marker = True
                    self._carry = self._carry[m_sp.end() :]
                    continue

                if m_sp and (m_fb is None or m_sp.start() < m_fb.start()):
                    # Text before SPEAK marker (ignore) + marker
                    spoken += self._carry[: m_sp.start()]
                    self._saw_speak_marker = True
                    self._carry = self._carry[m_sp.end() :]
                    continue

                if m_fb:
                    spoken += self._carry[: m_fb.start()]
                    self._carry = self._carry[m_fb.end() :]
                    self._mode = "feedback"
                    self._saw_feedback_marker = True
                    continue

                # Incomplete marker at end? Hold back a short prefix.
                hold = _holdback_for_marker(self._carry)
                if hold:
                    spoken += self._carry[: -hold]
                    self._carry = self._carry[-hold:]
                else:
                    spoken += self._carry
                    self._carry = ""
                break

            # feedback mode
            self._feedback_raw += self._carry
            self._carry = ""
            break

        return spoken

    def flush(self) -> str:
        """Flush remaining speak-side carry (ignore leftover if already in feedback)."""
        if self._mode == "feedback":
            self._feedback_raw += self._carry
            self._carry = ""
            return ""
        leftover = self._carry
        self._carry = ""
        # Strip any markers that only completed at flush
        leftover = _SPEAK_RE.sub("", leftover)
        leftover = _FEEDBACK_RE.split(leftover, maxsplit=1)[0]
        return leftover

    def parse_feedback(self) -> dict[str, Any] | None:
        raw = self._feedback_raw.strip()
        if not raw:
            return None
        # Extract first JSON object if model added prose
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            logger.warning("Feedback present but no JSON object: %r", raw[:120])
            return None
        blob = raw[start : end + 1]
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            logger.warning("Invalid feedback JSON: %r", blob[:200])
            return None
        if not isinstance(data, dict):
            return None
        return _normalize_feedback(data)


def _holdback_for_marker(buf: str) -> int:
    """How many trailing chars might be an incomplete <<<...>>> marker.

    Must hold the *longest* prefix: if the buffer is ``<<<``, holding only
    the last ``<`` would leak ``<<`` into the spoken channel and the
    marker would never assemble (Ollama often emits ``<<<`` as one token).
    """
    max_mark = len(_FEEDBACK_OPEN) + 4
    n = min(len(buf), max_mark)
    for i in range(n, 0, -1):
        tail = buf[-i:]
        if _FEEDBACK_OPEN.startswith(tail) or _SPEAK_OPEN.startswith(tail):
            return i
    return 0


def _normalize_feedback(data: dict[str, Any]) -> dict[str, Any]:
    grammar = data.get("grammar") or data.get("corrections") or []
    phrasing = data.get("phrasing") or data.get("upgrades") or []
    pronunciation = data.get("pronunciation") or data.get("phonetics") or []
    notes = data.get("notes") or data.get("tip") or ""

    def _as_list(v: Any) -> list[Any]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    return {
        "grammar": _as_list(grammar),
        "phrasing": _as_list(phrasing),
        "pronunciation": _as_list(pronunciation),
        "notes": notes if isinstance(notes, str) else str(notes),
    }


def spoken_only_from_full(text: str) -> str:
    """Extract spoken channel from a completed assistant message (for history/UI)."""
    split = DualChannelSplitter()
    speak = split.push(text) + split.flush()
    return speak.strip() or _SPEAK_RE.sub("", _FEEDBACK_RE.split(text, maxsplit=1)[0]).strip()
