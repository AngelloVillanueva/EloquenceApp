#!/usr/bin/env python3
"""Phase 1 local inference test: Faster-Whisper + Ollama + Kokoro/Piper on RTX 3060.

Measures warm-pipeline STT → LLM → TTS latency against the ~2.0s voice-to-voice target.

Usage (from repo root, with venv active):
  python scripts/download_models.py
  python scripts/test_inference_pipeline.py
  python scripts/test_inference_pipeline.py --audio data/samples/probe.wav
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Prefer CUDA EP for kokoro-onnx / onnxruntime-gpu when available
os.environ.setdefault("ONNX_PROVIDER", "CUDAExecutionProvider")

from app.config import OUTPUT_DIR, SAMPLES_DIR, get_settings  # noqa: E402
from app.services.llm import OllamaLLM  # noqa: E402
from app.services.pipeline import VoicePipeline  # noqa: E402
from app.services.stt import WhisperSTT  # noqa: E402
from app.services.tts import TTSService  # noqa: E402
from app.utils.cuda_bootstrap import bootstrap_cuda_dlls  # noqa: E402

bootstrap_cuda_dlls()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("test_inference")

PROBE_TEXT = (
    "Hello! I want to practice advanced English for a senior software interview. "
    "Could you help me sound more professional?"
)


def check_cuda() -> dict:
    info: dict = {"torch_cuda": False, "device_name": None, "vram_gb": None}
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_cuda"] = bool(torch.cuda.is_available())
        if info["torch_cuda"]:
            info["device_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info["vram_gb"] = round(props.total_memory / (1024**3), 2)
            info["cuda_runtime"] = torch.version.cuda
    except Exception as exc:  # noqa: BLE001
        info["torch_error"] = str(exc)

    try:
        import onnxruntime as ort

        info["onnx_providers"] = ort.get_available_providers()
        info["onnx_cuda"] = "CUDAExecutionProvider" in info["onnx_providers"]
    except Exception as exc:  # noqa: BLE001
        info["onnx_error"] = str(exc)

    return info


def check_ollama(settings) -> dict:
    llm = OllamaLLM(settings)
    try:
        models = llm.list_models()
        resolved = llm.resolve_model()
        return {"ok": True, "models": models, "resolved": resolved}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def synthesize_probe_audio(tts: TTSService, path: Path) -> Path:
    """Create a short WAV via TTS so STT has real speech to transcribe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Synthesizing probe audio → %s", path)
    result = tts.synthesize(PROBE_TEXT, out_path=path)
    logger.info(
        "Probe ready: %.2fs audio, engine=%s, synth=%.2fs",
        result.duration_s,
        result.engine,
        result.inference_s,
    )
    return result.audio_path


def write_silence_fallback(path: Path, seconds: float = 1.0, sr: int = 16000) -> Path:
    """Last-resort placeholder if TTS is unavailable (STT will be empty)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(seconds * sr)
    pcm = np.zeros(n, dtype=np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return path


def print_banner(title: str) -> None:
    bar = "=" * 64
    print(f"\n{bar}\n  {title}\n{bar}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 STT+LLM+TTS latency test")
    parser.add_argument(
        "--audio",
        type=Path,
        default=None,
        help="Input WAV/MP3 for STT (default: generate probe via TTS)",
    )
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Only run environment checks (CUDA / Ollama)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=OUTPUT_DIR / "last_pipeline_result.json",
        help="Where to write timing JSON",
    )
    args = parser.parse_args()

    settings = get_settings()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    print_banner("Elevate AI - Phase 1 Local Inference Test (RTX 3060)")
    print(f"Target warm latency: <= {settings.target_pipeline_latency_s:.1f}s")
    print(f"Whisper: {settings.whisper_model_size} | {settings.whisper_device}/{settings.whisper_compute_type}")
    print(f"Ollama:  {settings.ollama_model} @ {settings.ollama_base_url}")
    print(f"TTS:     {settings.tts_engine}")

    # --- Environment ---
    print_banner("1) GPU / CUDA check")
    cuda_info = check_cuda()
    print(json.dumps(cuda_info, indent=2))
    if not cuda_info.get("torch_cuda"):
        print(
            "\n[WARN] torch.cuda.is_available() == False.\n"
            "Install CUDA PyTorch wheels, e.g.:\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cu124\n"
        )

    print_banner("2) Ollama check")
    ollama_info = check_ollama(settings)
    print(json.dumps(ollama_info, indent=2))
    if not ollama_info.get("ok"):
        print(
            "\n[ERROR] Ollama is not reachable.\n"
            "1. Install from https://ollama.com/download\n"
            "2. Start the app / service\n"
            f"3. Pull a model: ollama pull {settings.ollama_fallback_model}\n"
            f"   or: ollama pull {settings.ollama_model}\n"
        )
        if args.skip_pipeline:
            return 1
        return 1

    if args.skip_pipeline:
        print("\n[--skip-pipeline] Environment checks done.")
        return 0

    # --- Load + probe audio ---
    print_banner("3) Load models + prepare audio")
    pipeline = VoicePipeline(settings)
    t_load = time.perf_counter()
    pipeline.load()
    load_s = time.perf_counter() - t_load
    print(f"Models loaded in {load_s:.2f}s (excluded from voice-to-voice latency)")

    if args.audio is not None:
        audio_path = args.audio
        if not audio_path.exists():
            print(f"[ERROR] Audio not found: {audio_path}")
            return 1
    else:
        probe_path = SAMPLES_DIR / "probe.wav"
        try:
            audio_path = synthesize_probe_audio(pipeline.tts, probe_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Could not synthesize probe audio: %s", exc)
            print(
                "\n[ERROR] TTS probe failed. Download models first:\n"
                "  python scripts/download_models.py\n"
            )
            return 1

    # --- Warm pipeline run ---
    print_banner("4) Warm pipeline: STT → LLM → TTS")
    # Optional micro-warmup so first-token / cudnn autotune doesn't dominate
    try:
        _ = pipeline.stt.transcribe(audio_path)
        logger.info("STT warmup transcription done")
    except Exception:  # noqa: BLE001
        logger.warning("STT warmup failed; continuing with timed run", exc_info=True)

    result = pipeline.run(audio_path, out_wav=OUTPUT_DIR / "pipeline_reply.wav")

    print(f"\nTranscript : {result.transcript}")
    print(f"LLM model  : {result.llm_model}")
    print(f"LLM reply  : {result.llm_reply}")
    print(f"TTS engine : {result.tts_engine}")
    print(f"Audio out  : {result.audio_out}")

    print_banner("5) Latency report (warm, load excluded)")
    t = result.timings
    print(f"  STT : {t.stt_s:6.3f}s")
    print(f"  LLM : {t.llm_s:6.3f}s")
    print(f"  TTS : {t.tts_s:6.3f}s")
    print(f"  --------------------")
    print(f"  TOTAL: {t.total_s:6.3f}s   (target <= {result.target_latency_s:.1f}s)")
    print(f"  Load: {t.load_s:6.3f}s   (one-time)")

    status = "PASS" if result.passed_latency_target else "OVER TARGET"
    print(f"\n  Result: {status}")
    if not result.passed_latency_target:
        print(
            "  Tips: use whisper medium.en + beam_size=1, shorter LLM replies,\n"
            "        Q4/Q5 7–8B models, Kokoro ONNX CUDA, keep models warm."
        )

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cuda": cuda_info,
        "ollama": ollama_info,
        "pipeline": result.to_dict(),
    }
    args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {args.json_out}")

    # Component-only smoke (optional clarity)
    print_banner("6) Component smoke (already exercised above)")
    stt = WhisperSTT(settings)
    print(f"  STT class OK ({settings.whisper_model_size})")
    print(f"  LLM class OK ({ollama_info.get('resolved')})")
    print(f"  TTS class OK ({result.tts_engine})")
    _ = stt  # silence lint

    return 0 if result.passed_latency_target else 2


if __name__ == "__main__":
    raise SystemExit(main())
