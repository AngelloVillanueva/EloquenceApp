"""TTS service: Kokoro-ONNX (preferred) with Piper fallback."""

from __future__ import annotations

import logging
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.config import OUTPUT_DIR, Settings, get_settings
from app.utils.cuda_bootstrap import bootstrap_cuda_dlls

logger = logging.getLogger(__name__)


@dataclass
class TTSResult:
    audio_path: Path | None
    sample_rate: int
    num_samples: int
    inference_s: float
    engine: str
    text: str
    pcm16: bytes | None = None

    @property
    def duration_s(self) -> float:
        if self.sample_rate <= 0:
            return 0.0
        return self.num_samples / float(self.sample_rate)


def _write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.asarray(samples, dtype=np.float32)
    # Clamp and convert to int16 PCM
    audio = np.clip(audio, -1.0, 1.0)
    pcm = (audio * 32767.0).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _float_to_pcm16(samples: np.ndarray) -> bytes:
    audio = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    return (audio * 32767.0).astype(np.int16).tobytes()


class KokoroTTS:
    """Kokoro-82M via kokoro-onnx (CUDA when onnxruntime-gpu is installed)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._kokoro = None

    def load(self) -> None:
        if self._kokoro is not None:
            return

        model_path = Path(self.settings.kokoro_model_path)
        voices_path = Path(self.settings.kokoro_voices_path)
        if not model_path.exists() or not voices_path.exists():
            raise FileNotFoundError(
                "Kokoro model files missing. Run: python scripts/download_models.py\n"
                f"  Expected: {model_path}\n"
                f"           {voices_path}"
            )

        bootstrap_cuda_dlls()
        from kokoro_onnx import Kokoro

        logger.info("Loading Kokoro ONNX from %s ...", model_path)
        t0 = time.perf_counter()
        self._kokoro = Kokoro(str(model_path), str(voices_path))
        logger.info("Kokoro ready in %.2fs", time.perf_counter() - t0)

    def synthesize(self, text: str, out_path: Path | None = None) -> TTSResult:
        self.load()
        assert self._kokoro is not None

        out = out_path or (OUTPUT_DIR / "kokoro_out.wav")
        t0 = time.perf_counter()
        samples, sample_rate = self._kokoro.create(
            text,
            voice=self.settings.kokoro_voice,
            speed=self.settings.kokoro_speed,
        )
        inference_s = time.perf_counter() - t0
        samples_arr = np.asarray(samples, dtype=np.float32)
        pcm16 = _float_to_pcm16(samples_arr)
        _write_wav(out, samples_arr, int(sample_rate))

        return TTSResult(
            audio_path=out,
            sample_rate=int(sample_rate),
            num_samples=int(samples_arr.size),
            inference_s=inference_s,
            engine="kokoro",
            text=text,
            pcm16=pcm16,
        )

    def synthesize_pcm(self, text: str) -> TTSResult:
        """Synthesize without requiring a caller-facing file path."""
        self.load()
        assert self._kokoro is not None
        t0 = time.perf_counter()
        samples, sample_rate = self._kokoro.create(
            text,
            voice=self.settings.kokoro_voice,
            speed=self.settings.kokoro_speed,
        )
        inference_s = time.perf_counter() - t0
        samples_arr = np.asarray(samples, dtype=np.float32)
        return TTSResult(
            audio_path=None,
            sample_rate=int(sample_rate),
            num_samples=int(samples_arr.size),
            inference_s=inference_s,
            engine="kokoro",
            text=text,
            pcm16=_float_to_pcm16(samples_arr),
        )


class PiperTTS:
    """Lightweight Piper TTS fallback (CPU/ONNX)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._voice = None

    def load(self) -> None:
        if self._voice is not None:
            return

        model_path = Path(self.settings.piper_model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                "Piper model missing. Run: python scripts/download_models.py\n"
                f"  Expected: {model_path}"
            )

        from piper import PiperVoice

        logger.info("Loading Piper voice from %s ...", model_path)
        t0 = time.perf_counter()
        config = Path(self.settings.piper_config_path)
        self._voice = PiperVoice.load(
            str(model_path),
            config_path=str(config) if config.exists() else None,
        )
        logger.info("Piper ready in %.2fs", time.perf_counter() - t0)

    def synthesize(self, text: str, out_path: Path | None = None) -> TTSResult:
        self.load()
        assert self._voice is not None

        out = out_path or (OUTPUT_DIR / "piper_out.wav")
        out.parent.mkdir(parents=True, exist_ok=True)

        t0 = time.perf_counter()
        with wave.open(str(out), "wb") as wf:
            self._voice.synthesize_wav(text, wf)
            sample_rate = wf.getframerate()
            num_frames = wf.getnframes()
        inference_s = time.perf_counter() - t0
        pcm16 = _read_wav_pcm16(out)

        return TTSResult(
            audio_path=out,
            sample_rate=int(sample_rate),
            num_samples=int(num_frames),
            inference_s=inference_s,
            engine="piper",
            text=text,
            pcm16=pcm16,
        )

    def synthesize_pcm(self, text: str) -> TTSResult:
        return self.synthesize(text, out_path=OUTPUT_DIR / "piper_stream.wav")


def _read_wav_pcm16(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wf:
        return wf.readframes(wf.getnframes())


class TTSService:
    """Facade that prefers Kokoro and falls back to Piper."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._kokoro = KokoroTTS(self.settings)
        self._piper = PiperTTS(self.settings)
        self._active_engine: str | None = None

    def load(self) -> str:
        engine = self.settings.tts_engine.lower().strip()
        if engine == "piper":
            self._piper.load()
            self._active_engine = "piper"
            return "piper"

        try:
            self._kokoro.load()
            self._active_engine = "kokoro"
            return "kokoro"
        except Exception as exc:  # noqa: BLE001 — intentional fallback
            logger.warning("Kokoro unavailable (%s); falling back to Piper.", exc)
            self._piper.load()
            self._active_engine = "piper"
            return "piper"

    def synthesize(self, text: str, out_path: Path | None = None) -> TTSResult:
        if self._active_engine is None:
            self.load()

        if self._active_engine == "kokoro":
            try:
                return self._kokoro.synthesize(text, out_path=out_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Kokoro synthesis failed (%s); trying Piper.", exc)
                self._active_engine = "piper"

        return self._piper.synthesize(text, out_path=out_path)

    def synthesize_pcm(self, text: str) -> TTSResult:
        if self._active_engine is None:
            self.load()

        if self._active_engine == "kokoro":
            try:
                return self._kokoro.synthesize_pcm(text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Kokoro PCM synthesis failed (%s); trying Piper.", exc)
                self._active_engine = "piper"

        return self._piper.synthesize_pcm(text)
