"""Faster-Whisper STT service — CUDA float16 on RTX 3060."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from app.config import Settings, get_settings
from app.utils.cuda_bootstrap import bootstrap_cuda_dlls

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    language: str | None
    duration_s: float
    inference_s: float


class WhisperSTT:
    """Lazy-loaded Faster-Whisper wrapper."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return

        bootstrap_cuda_dlls()
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Faster-Whisper '%s' on %s (%s)...",
            self.settings.whisper_model_size,
            self.settings.whisper_device,
            self.settings.whisper_compute_type,
        )
        t0 = time.perf_counter()
        self._model = WhisperModel(
            self.settings.whisper_model_size,
            device=self.settings.whisper_device,
            compute_type=self.settings.whisper_compute_type,
        )
        logger.info("Faster-Whisper ready in %.2fs", time.perf_counter() - t0)

    @property
    def model(self):
        self.load()
        return self._model

    def transcribe(self, audio_path: str | Path) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        t0 = time.perf_counter()
        segments, info = self.model.transcribe(
            str(path),
            beam_size=self.settings.whisper_beam_size,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        inference_s = time.perf_counter() - t0

        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", None),
            duration_s=float(getattr(info, "duration", 0.0) or 0.0),
            inference_s=inference_s,
        )

    def transcribe_array(
        self,
        audio: "np.ndarray",
        *,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """Transcribe mono float32 PCM in [-1, 1]."""
        import numpy as np

        samples = np.asarray(audio, dtype=np.float32).reshape(-1)
        if samples.size == 0:
            return TranscriptionResult(
                text="",
                language=None,
                duration_s=0.0,
                inference_s=0.0,
            )

        t0 = time.perf_counter()
        segments, info = self.model.transcribe(
            samples,
            language="en",
            beam_size=self.settings.whisper_beam_size,
            vad_filter=True,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        inference_s = time.perf_counter() - t0
        duration_s = float(samples.size) / float(sample_rate) if sample_rate else 0.0

        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", None) or "en",
            duration_s=duration_s,
            inference_s=inference_s,
        )
