"""Shared warm runtime for STT / LLM / TTS (one GPU-resident set per process)."""

from __future__ import annotations

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from app.config import Settings, get_settings
from app.services.llm import OllamaLLM
from app.services.stt import WhisperSTT
from app.services.tts import TTSService
from app.utils.cuda_bootstrap import bootstrap_cuda_dlls

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RuntimeStatus:
    loaded: bool
    tts_engine: str | None
    whisper_model: str
    ollama_model: str | None
    ollama_warmed: bool = False
    load_error: str | None = None


class AppRuntime:
    """Process-wide model holders. Safe to share across WebSocket sessions.

    CUDA work in *this* process (Whisper/Kokoro) is serialized through a
    single-worker executor to avoid STT+TTS contending on the same GPU context.
    Ollama runs in a separate process and may overlap with our TTS intentionally.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.stt = WhisperSTT(self.settings)
        self.llm = OllamaLLM(self.settings)
        self.tts = TTSService(self.settings)
        self._lock = threading.Lock()
        self._loaded = False
        self._ollama_warmed = False
        self._tts_engine: str | None = None
        self._ollama_model: str | None = None
        self._load_error: str | None = None
        self._gpu_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="elevate-gpu"
        )

    @property
    def loaded(self) -> bool:
        return self._loaded

    def status(self) -> RuntimeStatus:
        return RuntimeStatus(
            loaded=self._loaded,
            tts_engine=self._tts_engine,
            whisper_model=self.settings.whisper_model_size,
            ollama_model=self._ollama_model,
            ollama_warmed=self._ollama_warmed,
            load_error=self._load_error,
        )

    def warm_sync(self, *, include_llm: bool = True) -> RuntimeStatus:
        """Load STT/TTS and optionally resolve + VRAM-warm Ollama."""
        with self._lock:
            if self._loaded and (not include_llm or self._ollama_warmed):
                return self.status()
            try:
                bootstrap_cuda_dlls()
                if not self._loaded:
                    self.stt.load()
                    self._tts_engine = self.tts.load()
                    self._loaded = True
                if include_llm:
                    self._ollama_model = self.llm.resolve_model()
                    try:
                        self.llm.warmup_model(self._ollama_model)
                        self._ollama_warmed = True
                        self._load_error = None
                    except Exception as warm_exc:  # noqa: BLE001
                        # STT/TTS already usable; do not fail the whole runtime warm.
                        self._ollama_warmed = False
                        self._load_error = f"ollama_warmup: {warm_exc}"
                        logger.exception(
                            "Ollama VRAM warmup failed; continuing with STT/TTS loaded"
                        )
                else:
                    self._load_error = None
                logger.info(
                    "Runtime warm: whisper=%s tts=%s ollama=%s warmed=%s",
                    self.settings.whisper_model_size,
                    self._tts_engine,
                    self._ollama_model,
                    self._ollama_warmed,
                )
            except Exception as exc:  # noqa: BLE001
                self._load_error = str(exc)
                logger.exception("Runtime warm failed")
                raise
            return self.status()

    async def warm(self, *, include_llm: bool = True) -> RuntimeStatus:
        return await asyncio.to_thread(self.warm_sync, include_llm=include_llm)

    async def run_on_gpu(self, fn: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
        """Run blocking CUDA work off the event loop on the serialized GPU pool."""
        loop = asyncio.get_running_loop()

        def _call() -> T:
            return fn(*args, **kwargs)

        return await loop.run_in_executor(self._gpu_executor, _call)

    def shutdown(self) -> None:
        self._gpu_executor.shutdown(wait=False, cancel_futures=True)


_runtime: AppRuntime | None = None


def get_runtime() -> AppRuntime:
    global _runtime
    if _runtime is None:
        _runtime = AppRuntime()
    return _runtime
