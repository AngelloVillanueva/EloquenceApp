"""FastAPI application entrypoint — Phase 2 WebSocket audio streaming."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.services.runtime import get_runtime
from app.utils.cuda_bootstrap import bootstrap_cuda_dlls
from app.ws.handler import audio_websocket

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    bootstrap_cuda_dlls()
    runtime = get_runtime()
    # Warm STT/TTS + force Ollama GGUF into VRAM (keep_alive=-1) to avoid 60–80s TTFA.
    try:
        status = await runtime.warm(include_llm=True)
        logger.info(
            "Lifespan warm OK: whisper=%s tts=%s ollama=%s warmed=%s ctx=%s",
            status.whisper_model,
            status.tts_engine,
            status.ollama_model,
            status.ollama_warmed,
            settings.ollama_num_ctx,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "Startup warm failed — models will load on first /ws/audio connection"
        )
    yield
    logger.info("Lifespan shutdown: releasing GPU executor")
    runtime.shutdown()
    _ = settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    def index() -> FileResponse:
        demo = STATIC_DIR / "ws_demo.html"
        if not demo.exists():
            raise FileNotFoundError(f"Missing demo page: {demo}")
        # Avoid stale cached JS (e.g. old `None` bug) breaking the Conectar button.
        return FileResponse(
            demo,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    @app.get("/health")
    def health() -> dict[str, Any]:
        status = get_runtime().status()
        return {
            "status": "ok",
            "version": __version__,
            "device": settings.device,
            "whisper_model": settings.whisper_model_size,
            "ollama_model": settings.ollama_model,
            "tts_engine": settings.tts_engine,
            "phase": 2,
            "runtime_loaded": status.loaded,
            "runtime_tts": status.tts_engine,
            "runtime_ollama": status.ollama_model,
            "ollama_warmed": status.ollama_warmed,
            "ollama_num_ctx": settings.ollama_num_ctx,
            "runtime_error": status.load_error,
            "ws": "/ws/audio",
        }

    @app.get("/api/config")
    def public_config() -> dict[str, Any]:
        return {
            "app_name": settings.app_name,
            "phase": 2,
            "ws_audio": "/ws/audio",
            "target_pipeline_latency_s": settings.target_pipeline_latency_s,
            "capture_sample_rate": 16000,
            "ollama": {
                "model": settings.ollama_model,
                "num_ctx": settings.ollama_num_ctx,
                "num_predict": settings.ollama_num_predict,
                "keep_alive": settings.ollama_keep_alive,
            },
            "vram_notes": {
                "stt": "Faster-Whisper medium.en float16 ~2–3 GB",
                "llm": "Ollama 7–8B Q5 ~5.5–6.5 GB",
                "tts": "Kokoro/Piper ~0.5 GB",
                "budget": "RTX 3060 12 GB (~8.5–10 GB active)",
            },
            "events": {
                "client": ["END_TURN", "CANCEL_AUDIO", "PING", "CONFIG"],
                "server": [
                    "READY",
                    "STATE",
                    "TRANSCRIPT",
                    "TOKEN",
                    "SENTENCE",
                    "AUDIO_META",
                    "TURN_DONE",
                    "CANCELLED",
                    "ERROR",
                    "PONG",
                ],
            },
        }

    @app.websocket("/ws/audio")
    async def ws_audio(websocket: WebSocket) -> None:
        await audio_websocket(websocket)

    return app


app = create_app()
