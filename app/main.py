"""FastAPI application entrypoint — Phase 2 WebSocket audio streaming."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.services.memory import get_memory
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
            "phase": 4,
            "runtime_loaded": status.loaded,
            "runtime_tts": status.tts_engine,
            "runtime_ollama": status.ollama_model,
            "ollama_warmed": status.ollama_warmed,
            "ollama_num_ctx": settings.ollama_num_ctx,
            "runtime_error": status.load_error,
            "ws": "/ws/audio",
            "memory": "/api/memory",
        }

    @app.get("/api/config")
    def public_config() -> dict[str, Any]:
        return {
            "app_name": settings.app_name,
            "phase": 4,
            "ws_audio": "/ws/audio",
            "memory": "/api/memory",
            "tts": "/api/tts",
            "shadow": "/api/shadow/prompts",
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
                    "FEEDBACK",
                    "AUDIO_META",
                    "TURN_DONE",
                    "CANCELLED",
                    "ERROR",
                    "PONG",
                ],
            },
        }

    @app.get("/api/memory")
    def memory_snapshot() -> dict[str, Any]:
        mem = get_memory()
        user_id = mem.ensure_default_user()
        return mem.snapshot(user_id)

    @app.get("/api/shadow/prompts")
    def shadow_prompts() -> dict[str, Any]:
        mem = get_memory()
        user_id = mem.ensure_default_user()
        return {"prompts": mem.shadow_prompts(user_id)}

    @app.post("/api/shadow/gloss")
    async def shadow_gloss(payload: dict[str, Any]) -> dict[str, Any]:
        """Spanish meaning for a phrase — Ollama, same local model as the tutor."""
        import asyncio

        from app.services.shadow import GLOSS_SYSTEM, clean_gloss

        text = str(payload.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        if len(text) > 200:
            raise HTTPException(status_code=400, detail="text too long")
        runtime = get_runtime()
        try:
            result = await asyncio.to_thread(
                runtime.llm.chat, text, system=GLOSS_SYSTEM
            )
        except Exception as exc:  # noqa: BLE001 — gloss is optional garnish
            logger.warning("Gloss failed for %r: %s", text[:60], exc)
            return {"es": ""}
        return {"es": clean_gloss(result.text)}

    @app.post("/api/tts")
    async def speak_text(payload: dict[str, Any]) -> Response:
        text = str(payload.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        if len(text) > 400:
            raise HTTPException(status_code=400, detail="text too long")
        from app.ws.audio_utils import write_wav_bytes

        runtime = get_runtime()
        await runtime.warm(include_llm=False)
        result = await runtime.run_on_gpu(runtime.tts.synthesize_pcm, text)
        wav = write_wav_bytes(result.pcm16 or b"", result.sample_rate)
        return Response(content=wav, media_type="audio/wav")

    @app.post("/api/shadow/evaluate")
    async def shadow_evaluate(payload: dict[str, Any]) -> dict[str, Any]:
        import base64

        from app.services.shadow import score_repeat
        from app.ws.audio_utils import pcm16_bytes_to_float32

        target = str(payload.get("target") or "").strip()
        raw = payload.get("pcm_b64") or ""
        if not target:
            raise HTTPException(status_code=400, detail="target is required")
        if not raw:
            raise HTTPException(status_code=400, detail="pcm_b64 is required")
        try:
            pcm = base64.b64decode(raw)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail="invalid pcm_b64") from exc
        if len(pcm) < 3200:
            raise HTTPException(status_code=400, detail="audio too short")
        sample_rate = int(payload.get("sample_rate") or 16000)
        audio = pcm16_bytes_to_float32(pcm)
        runtime = get_runtime()
        await runtime.warm(include_llm=False)
        tr = await runtime.run_on_gpu(
            runtime.stt.transcribe_array, audio, sample_rate=sample_rate
        )
        return score_repeat(target, tr.text)

    @app.websocket("/ws/audio")
    async def ws_audio(websocket: WebSocket) -> None:
        await audio_websocket(websocket)

    return app


app = create_app()
