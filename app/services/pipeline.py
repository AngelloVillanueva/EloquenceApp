"""End-to-end STT → LLM → TTS pipeline helpers.

Phase 1 batch path (sync). Do **not** call ``VoicePipeline.run`` from an
``async`` FastAPI/WebSocket handler without ``asyncio.to_thread`` / the
runtime GPU executor — it blocks the event loop. Streaming voice path lives
in ``app.ws.handler``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import OUTPUT_DIR, Settings, get_settings
from app.services.llm import OllamaLLM
from app.services.stt import WhisperSTT
from app.services.tts import TTSService

logger = logging.getLogger(__name__)


@dataclass
class PipelineTimings:
    stt_s: float
    llm_s: float
    tts_s: float
    total_s: float
    load_s: float

    def under_target(self, target_s: float) -> bool:
        return self.total_s <= target_s


@dataclass
class PipelineResult:
    transcript: str
    llm_reply: str
    llm_model: str
    tts_engine: str
    audio_out: str
    timings: PipelineTimings
    target_latency_s: float
    passed_latency_target: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VoicePipeline:
    """Warmable STT + LLM + TTS pipeline for Phase 1 validation (sync)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.stt = WhisperSTT(self.settings)
        self.llm = OllamaLLM(self.settings)
        self.tts = TTSService(self.settings)
        self._loaded = False
        self.load_s = 0.0

    def load(self) -> None:
        if self._loaded:
            return
        t0 = time.perf_counter()
        self.stt.load()
        _ = self.llm.resolve_model()
        self.tts.load()
        self.load_s = time.perf_counter() - t0
        self._loaded = True
        logger.info("Pipeline models loaded in %.2fs", self.load_s)

    def run(
        self,
        audio_path: str | Path,
        *,
        out_wav: Path | None = None,
    ) -> PipelineResult:
        self.load()
        audio_path = Path(audio_path)
        out_wav = out_wav or (OUTPUT_DIR / "pipeline_reply.wav")

        t_pipe = time.perf_counter()

        stt_result = self.stt.transcribe(audio_path)
        if not stt_result.text:
            raise RuntimeError(f"STT returned empty transcript for {audio_path}")

        llm_result = self.llm.latency_reply(stt_result.text)
        if not llm_result.text:
            raise RuntimeError("LLM returned an empty response")

        tts_result = self.tts.synthesize(llm_result.text, out_path=out_wav)
        total_s = time.perf_counter() - t_pipe

        timings = PipelineTimings(
            stt_s=stt_result.inference_s,
            llm_s=llm_result.inference_s,
            tts_s=tts_result.inference_s,
            total_s=total_s,
            load_s=self.load_s,
        )

        return PipelineResult(
            transcript=stt_result.text,
            llm_reply=llm_result.text,
            llm_model=llm_result.model,
            tts_engine=tts_result.engine,
            audio_out=str(tts_result.audio_path),
            timings=timings,
            target_latency_s=self.settings.target_pipeline_latency_s,
            passed_latency_target=timings.under_target(
                self.settings.target_pipeline_latency_s
            ),
        )

    async def run_async(
        self,
        audio_path: str | Path,
        *,
        out_wav: Path | None = None,
    ) -> PipelineResult:
        """Async wrapper — runs the sync batch pipeline off the event loop."""
        return await asyncio.to_thread(self.run, audio_path, out_wav=out_wav)
