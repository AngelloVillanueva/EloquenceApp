"""Ensure CUDA DLLs bundled with PyTorch are visible to onnxruntime-gpu on Windows.

onnxruntime-gpu needs cuDNN/CUDA libraries on PATH. When the system CUDA Toolkit
is not installed, PyTorch's cu124 wheels still ship the required DLLs under
``torch/lib``. Call ``bootstrap_cuda_dlls()`` before importing/using Kokoro.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_BOOTSTRAPPED = False


def bootstrap_cuda_dlls() -> Path | None:
    """Add ``torch/lib`` to the process DLL search path. Idempotent."""
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return None

    try:
        import torch
    except ImportError:
        logger.warning("torch not installed; skipping CUDA DLL bootstrap")
        _BOOTSTRAPPED = True
        return None

    torch_lib = Path(torch.__file__).resolve().parent / "lib"
    if not torch_lib.is_dir():
        logger.warning("torch lib dir missing: %s", torch_lib)
        _BOOTSTRAPPED = True
        return None

    # Prefer add_dll_directory on Windows (Python 3.8+)
    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(torch_lib))

    path = os.environ.get("PATH", "")
    torch_lib_str = str(torch_lib)
    if torch_lib_str not in path.split(os.pathsep):
        os.environ["PATH"] = torch_lib_str + os.pathsep + path

    os.environ.setdefault("ONNX_PROVIDER", "CUDAExecutionProvider")
    _BOOTSTRAPPED = True
    logger.info("CUDA DLL path bootstrapped from %s", torch_lib)
    return torch_lib
