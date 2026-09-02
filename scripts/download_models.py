"""Download Kokoro (and optional Piper) model assets into ./models."""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import MODELS_DIR  # noqa: E402

KOKORO_FILES = {
    "kokoro-v1.0.onnx": (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/kokoro-v1.0.onnx"
    ),
    "voices-v1.0.bin": (
        "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
        "model-files-v1.0/voices-v1.0.bin"
    ),
}

# Piper en_US medium voice (Rhasspy releases)
PIPER_FILES = {
    "en_US-lessac-medium.onnx": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    ),
    "en_US-lessac-medium.onnx.json": (
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/"
        "en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
    ),
}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest.name} already present ({dest.stat().st_size:,} bytes)")
        return

    print(f"[get ] {dest.name}")
    print(f"       {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")

    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        if total_size <= 0:
            return
        downloaded = block_num * block_size
        pct = min(100, downloaded * 100 // total_size)
        print(f"\r       {pct:3d}% ({downloaded:,}/{total_size:,})", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, tmp, reporthook=_reporthook)
        print()
        tmp.replace(dest)
        print(f"[ok  ] saved {dest} ({dest.stat().st_size:,} bytes)")
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Download local TTS model files")
    parser.add_argument(
        "--engine",
        choices=("kokoro", "piper", "all"),
        default="all",
        help="Which TTS assets to download (default: all)",
    )
    args = parser.parse_args()

    if args.engine in ("kokoro", "all"):
        kokoro_dir = MODELS_DIR / "kokoro"
        for name, url in KOKORO_FILES.items():
            _download(url, kokoro_dir / name)

    if args.engine in ("piper", "all"):
        piper_dir = MODELS_DIR / "piper"
        for name, url in PIPER_FILES.items():
            _download(url, piper_dir / name)

    print("\nDone. Models live under:", MODELS_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
