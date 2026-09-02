"""Ollama LLM client for local Llama/Qwen instruct models."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.prompts.tutor_system import LATENCY_TEST_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str
    model: str
    inference_s: float
    eval_count: int | None = None
    prompt_eval_count: int | None = None


class OllamaLLM:
    """Thin HTTP client around the local Ollama native chat API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def base_url(self) -> str:
        return self.settings.ollama_base_url.rstrip("/")

    def healthcheck(self) -> dict[str, Any]:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(f"{self.base_url}/api/tags")
            r.raise_for_status()
            return r.json()

    def list_models(self) -> list[str]:
        data = self.healthcheck()
        return [m.get("name", "") for m in data.get("models", [])]

    def resolve_model(self) -> str:
        available = self.list_models()
        preferred = self.settings.ollama_model
        fallback = self.settings.ollama_fallback_model

        if any(
            preferred in name or name.startswith(preferred.split(":")[0])
            for name in available
        ):
            for name in available:
                if name == preferred or name.startswith(preferred):
                    return name
            return preferred

        for name in available:
            if fallback in name or name.startswith(fallback.split(":")[0]):
                logger.warning(
                    "Preferred model '%s' not found; using fallback '%s'",
                    preferred,
                    name,
                )
                return name

        if available:
            logger.warning(
                "Preferred/fallback models missing; using first available: %s",
                available[0],
            )
            return available[0]

        raise RuntimeError(
            "No Ollama models found. Pull one with:\n"
            f"  ollama pull {preferred}\n"
            f"  ollama pull {fallback}"
        )

    def keep_alive_value(self) -> int | str:
        """Ollama accepts int seconds, duration strings (\"5m\"), or int -1 (forever).

        Env often loads as str \"-1\"; that MUST be coerced to int -1 or Ollama
        returns HTTP 400: time: missing unit in duration \"-1\".
        """
        raw = self.settings.ollama_keep_alive
        if isinstance(raw, bool):
            return -1 if raw else 0
        if isinstance(raw, int):
            return raw
        text = str(raw).strip()
        if text == "-1":
            return -1
        try:
            return int(text)
        except ValueError:
            return text

    def _options(self) -> dict[str, Any]:
        return {
            "temperature": self.settings.ollama_temperature,
            "num_predict": self.settings.ollama_num_predict,
            "num_ctx": self.settings.ollama_num_ctx,
        }

    def _chat_payload(
        self,
        user_message: str,
        *,
        system: str | None,
        model_name: str,
        stream: bool,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system or SYSTEM_PROMPT},
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return {
            "model": model_name,
            "messages": messages,
            "stream": stream,
            "keep_alive": self.keep_alive_value(),
            "options": self._options(),
        }

    def warmup_model(self, model: str | None = None) -> dict[str, Any]:
        """Force-load GGUF weights into VRAM via /api/generate + keep_alive=-1."""
        model_name = model or self.resolve_model()
        keep_alive = self.keep_alive_value()
        payload = {
            "model": model_name,
            "prompt": "OK",
            "stream": False,
            "keep_alive": keep_alive,
            "options": {
                "num_predict": 1,
                "num_ctx": self.settings.ollama_num_ctx,
            },
        }
        logger.info(
            "Warming Ollama model '%s' into VRAM (keep_alive=%r)...",
            model_name,
            keep_alive,
        )
        t0 = time.perf_counter()
        with httpx.Client(timeout=self.settings.ollama_timeout_s) as client:
            r = client.post(f"{self.base_url}/api/generate", json=payload)
            if r.is_error:
                logger.error(
                    "Ollama warmup failed status=%s body=%s",
                    r.status_code,
                    r.text[:500],
                )
            r.raise_for_status()
            data = r.json()
        elapsed = time.perf_counter() - t0
        logger.info("Ollama warmup done in %.2fs (model=%s)", elapsed, model_name)
        return {"model": model_name, "warmup_s": elapsed, "response": data.get("response")}

    async def warmup_model_async(self, model: str | None = None) -> dict[str, Any]:
        return await asyncio.to_thread(self.warmup_model, model)

    def chat(
        self,
        user_message: str,
        *,
        system: str | None = None,
        model: str | None = None,
        stream: bool = False,
    ) -> LLMResult:
        del stream  # non-stream path only
        model_name = model or self.resolve_model()
        payload = self._chat_payload(
            user_message, system=system, model_name=model_name, stream=False
        )

        t0 = time.perf_counter()
        with httpx.Client(timeout=self.settings.ollama_timeout_s) as client:
            r = client.post(f"{self.base_url}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()

        inference_s = time.perf_counter() - t0
        text = (data.get("message") or {}).get("content", "").strip()

        return LLMResult(
            text=text,
            model=model_name,
            inference_s=inference_s,
            eval_count=data.get("eval_count"),
            prompt_eval_count=data.get("prompt_eval_count"),
        )

    def chat_stream(
        self,
        user_message: str,
        *,
        system: str | None = None,
        model: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> Iterator[str]:
        """Yield token deltas for sentence-level TTS (sync)."""
        model_name = model or self.resolve_model()
        payload = self._chat_payload(
            user_message,
            system=system,
            model_name=model_name,
            stream=True,
            history=history,
        )

        with httpx.Client(timeout=self.settings.ollama_timeout_s) as client:
            with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    delta = (chunk.get("message") or {}).get("content", "")
                    if delta:
                        yield delta
                    if chunk.get("done"):
                        break

    async def chat_stream_async(
        self,
        user_message: str,
        *,
        system: str | None = None,
        model: str | None = None,
        cancel_event: asyncio.Event | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncIterator[str]:
        """Yield token deltas asynchronously; abort HTTP stream on cancel/CancelledError."""
        model_name = model or await asyncio.to_thread(self.resolve_model)
        payload = self._chat_payload(
            user_message,
            system=system,
            model_name=model_name,
            stream=True,
            history=history,
        )

        timeout = httpx.Timeout(self.settings.ollama_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                try:
                    async for line in response.aiter_lines():
                        if cancel_event is not None and cancel_event.is_set():
                            logger.info(
                                "LLM stream abort: cancel_event set (model=%s)",
                                model_name,
                            )
                            break
                        if not line:
                            continue
                        chunk = json.loads(line)
                        delta = (chunk.get("message") or {}).get("content", "")
                        if delta:
                            yield delta
                        if chunk.get("done"):
                            break
                except asyncio.CancelledError:
                    logger.info(
                        "LLM stream cancelled (CancelledError) model=%s", model_name
                    )
                    raise
                finally:
                    # Ensure Ollama stops generating as soon as we drop the connection.
                    await response.aclose()

    def latency_reply(self, user_message: str) -> LLMResult:
        """Short spoken-style reply for Phase 1 pipeline timing."""
        return self.chat(user_message, system=LATENCY_TEST_PROMPT)
