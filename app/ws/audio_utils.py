"""PCM / WAV helpers for WebSocket audio streaming."""

from __future__ import annotations

import io
import wave
from dataclasses import dataclass

import numpy as np


@dataclass
class PcmChunk:
    pcm16: bytes
    sample_rate: int
    num_samples: int

    @property
    def duration_s(self) -> float:
        if self.sample_rate <= 0:
            return 0.0
        return self.num_samples / float(self.sample_rate)


def float32_to_pcm16_bytes(samples: np.ndarray) -> bytes:
    audio = np.asarray(samples, dtype=np.float32)
    audio = np.clip(audio, -1.0, 1.0)
    return (audio * 32767.0).astype(np.int16).tobytes()


def pcm16_bytes_to_float32(pcm: bytes) -> np.ndarray:
    if not pcm:
        return np.zeros(0, dtype=np.float32)
    arr = np.frombuffer(pcm, dtype=np.int16)
    return (arr.astype(np.float32) / 32768.0)


def write_wav_bytes(pcm16: bytes, sample_rate: int, *, channels: int = 1) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16)
    return buf.getvalue()


def lookalike_wav_header(data: bytes) -> bool:
    return len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WAVE"
