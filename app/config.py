"""Central configuration for the local AI English tutor stack."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUT_DIR = DATA_DIR / "output"


class Settings(BaseSettings):
    """Runtime settings tuned for RTX 3060 12GB VRAM budget."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Eloquence — Local English Tutor"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # --- GPU / CUDA ---
    device: str = "cuda"
    compute_type: str = "float16"  # Faster-Whisper on RTX 3060

    # --- STT: Faster-Whisper (~2–3 GB VRAM) ---
    whisper_model_size: str = "medium.en"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    whisper_beam_size: int = 1  # greedy / low latency

    # --- LLM: Ollama (~5.5–6.5 GB VRAM for Q5 7–8B) ---
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_fallback_model: str = "qwen2.5:7b"
    ollama_timeout_s: float = 120.0
    ollama_temperature: float = 0.7
    ollama_num_predict: int = 220  # speak + compact feedback JSON
    ollama_num_ctx: int = 2048  # cap KV-cache on 12GB with STT+TTS coresident
    # Use int -1 (forever). String "-1" makes Ollama return 400: missing unit in duration.
    ollama_keep_alive: int | str = -1

    # --- TTS: Kokoro preferred, Piper fallback (~0.5 GB) ---
    tts_engine: str = "kokoro"  # "kokoro" | "piper"
    kokoro_model_path: Path = MODELS_DIR / "kokoro" / "kokoro-v1.0.onnx"
    kokoro_voices_path: Path = MODELS_DIR / "kokoro" / "voices-v1.0.bin"
    kokoro_voice: str = "af_sarah"
    kokoro_speed: float = 1.0
    piper_model_path: Path = MODELS_DIR / "piper" / "en_US-lessac-medium.onnx"
    piper_config_path: Path = MODELS_DIR / "piper" / "en_US-lessac-medium.onnx.json"
    piper_speaker_id: int = 0

    # --- Latency target (Phase 1 validation) ---
    target_pipeline_latency_s: float = 2.0

    # --- Persistent memory (app-owned SQLite; LLM never runs SQL) ---
    sqlite_path: Path = DATA_DIR / "elevate.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
