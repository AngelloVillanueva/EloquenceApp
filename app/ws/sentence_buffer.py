"""Sentence buffering for streaming LLM → sentence-level TTS."""

from __future__ import annotations

import re

# Strong sentence endings OR newline boundaries (spoken paragraphs).
_SENTENCE_END = re.compile(r"([.!?]+)(\s+|$)|(\n+)")


class SentenceBuffer:
    """Accumulate token deltas and emit complete sentences."""

    def __init__(self) -> None:
        self._buf = ""

    def push(self, delta: str) -> list[str]:
        if not delta:
            return []
        self._buf += delta
        out: list[str] = []
        while True:
            match = _SENTENCE_END.search(self._buf)
            if not match:
                break
            if match.group(1):
                # Punctuation ending: keep .?! with the sentence.
                sentence = self._buf[: match.end(1)].strip()
                self._buf = self._buf[match.end() :]
            else:
                # Newline ending: take text before newlines.
                sentence = self._buf[: match.start()].strip()
                self._buf = self._buf[match.end() :]
            if sentence:
                out.append(sentence)
        return out

    def flush(self) -> str | None:
        leftover = self._buf.strip()
        self._buf = ""
        return leftover or None

    def clear(self) -> None:
        self._buf = ""
