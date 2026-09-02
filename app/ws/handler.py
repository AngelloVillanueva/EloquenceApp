"""Bidirectional audio WebSocket session handler (Phase 2)."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.prompts.tutor_system import SPOKEN_TUTOR_PROMPT
from app.services.memory import MemoryService, get_memory
from app.services.runtime import AppRuntime, get_runtime
from app.ws.audio_utils import pcm16_bytes_to_float32
from app.ws.dual_channel import DualChannelSplitter, spoken_only_from_full
from app.ws.protocol import ClientEvent, ServerEvent, SessionState, msg
from app.ws.sentence_buffer import SentenceBuffer

logger = logging.getLogger(__name__)

# Split large TTS PCM into smaller WS binary frames (~100ms @ 24kHz mono PCM16).
_PCM_FRAME_BYTES = 4800
_SENTINEL = object()
# Rolling chat memory: pairs of user/assistant (fits under num_ctx=2048 with system).
_MAX_HISTORY_MESSAGES = 12


class AudioWsSession:
    """One WebSocket connection: buffer mic PCM, run STT→LLM stream→TTS, barge-in."""

    def __init__(self, websocket: WebSocket, runtime: AppRuntime | None = None) -> None:
        self.ws = websocket
        self.runtime = runtime or get_runtime()
        self.sample_rate = 16000
        self.pcm_buffer = bytearray()
        self.state = SessionState.IDLE
        self.cancel_event = asyncio.Event()
        self._turn_lock = asyncio.Lock()
        self._turn_task: asyncio.Task[None] | None = None
        # Multi-turn context for Ollama (user/assistant only; system is added by LLM client).
        self.history: list[dict[str, str]] = []
        self.memory: MemoryService = get_memory()
        self.user_id: int = self.memory.ensure_default_user()
        self.session_id: int | None = None
        self.scenario: str = "free"
        self.ttfa_samples: list[float] = []
        self._system_prompt: str = SPOKEN_TUTOR_PROMPT

    async def run(self) -> None:
        await self.ws.accept()
        try:
            status = self.runtime.status()
            if not status.loaded or not status.ollama_warmed:
                await self.send_json(
                    msg(ServerEvent.STATE, state="warming", detail="loading models")
                )
                status = await self.runtime.warm(include_llm=True)

            await self.send_json(
                msg(
                    ServerEvent.READY,
                    capture_sample_rate=self.sample_rate,
                    whisper_model=status.whisper_model,
                    ollama_model=status.ollama_model,
                    tts_engine=status.tts_engine,
                    ollama_warmed=status.ollama_warmed,
                    phase=2,
                )
            )
            await self.set_state(SessionState.LISTENING)

            while True:
                message = await self.ws.receive()
                if message.get("type") == "websocket.disconnect":
                    break

                if message.get("bytes") is not None:
                    await self.on_audio_bytes(message["bytes"])
                elif message.get("text") is not None:
                    await self.on_text(message["text"])
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as exc:  # noqa: BLE001
            logger.exception("WebSocket session error")
            await self.safe_send_json(msg(ServerEvent.ERROR, message=str(exc)))
        finally:
            await self._cancel_turn(reason="session_close")
            avg = (
                sum(self.ttfa_samples) / len(self.ttfa_samples)
                if self.ttfa_samples
                else None
            )
            try:
                self.memory.end_session(self.session_id, ttfa_avg=avg)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to close SQLite session")

    async def on_audio_bytes(self, data: bytes) -> None:
        if self.state in (
            SessionState.TRANSCRIBING,
            SessionState.THINKING,
            SessionState.SPEAKING,
        ):
            return
        if self.state == SessionState.IDLE:
            await self.set_state(SessionState.LISTENING)
        self.pcm_buffer.extend(data)

    async def on_text(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await self.send_json(
                msg(ServerEvent.ERROR, message="Invalid JSON control message")
            )
            return

        event = str(payload.get("type", "")).upper()
        if event == ClientEvent.PING:
            await self.send_json(msg(ServerEvent.PONG))
            return

        if event == ClientEvent.CONFIG:
            sr = int(payload.get("sample_rate", self.sample_rate))
            if sr > 0:
                self.sample_rate = sr
            scenario = str(payload.get("scenario") or self.scenario).strip() or "free"
            self.scenario = scenario
            if self.session_id is None:
                self.session_id = self.memory.start_session(
                    user_id=self.user_id, scenario=scenario
                )
                brief = self.memory.build_brief(self.user_id, scenario=scenario)
                self._system_prompt = (
                    f"{SPOKEN_TUTOR_PROMPT}\n\n"
                    f"[MEMORY BRIEF — do not read aloud]\n{brief}\n"
                )
                logger.info("SQLite session %s scenario=%s\n%s", self.session_id, scenario, brief)
            await self.send_json(
                msg(
                    ServerEvent.READY,
                    capture_sample_rate=self.sample_rate,
                    updated=True,
                    scenario=self.scenario,
                    session_id=self.session_id,
                )
            )
            return

        if event == ClientEvent.CANCEL_AUDIO:
            await self.handle_cancel()
            return

        if event == ClientEvent.END_TURN:
            await self.handle_end_turn()
            return

        await self.send_json(
            msg(ServerEvent.ERROR, message=f"Unknown event type: {event}")
        )

    async def handle_cancel(self) -> None:
        logger.info("CANCEL_AUDIO received — aborting active turn")
        self.cancel_event.set()
        self.pcm_buffer.clear()
        await self._cancel_turn(reason="CANCEL_AUDIO")
        await self.safe_send_json(msg(ServerEvent.CANCELLED))
        await self.set_state(SessionState.LISTENING)

    async def handle_end_turn(self) -> None:
        # New utterance preempts any in-flight turn (stability + barge-in path).
        if self._turn_task and not self._turn_task.done():
            logger.info("END_TURN while busy — cancelling previous turn first")
            self.cancel_event.set()
            await self._cancel_turn(reason="preempt_END_TURN")

        pcm = bytes(self.pcm_buffer)
        self.pcm_buffer.clear()
        if len(pcm) < self.sample_rate:  # < ~0.5s of 16-bit mono @ 16k
            await self.send_json(
                msg(ServerEvent.ERROR, message="Audio too short; keep speaking")
            )
            await self.set_state(SessionState.LISTENING)
            return

        self.cancel_event = asyncio.Event()  # fresh flag for the new turn
        self._turn_task = asyncio.create_task(
            self._run_turn(pcm), name="elevate-audio-turn"
        )

    async def _cancel_turn(self, *, reason: str) -> None:
        task = self._turn_task
        if task and not task.done():
            logger.info("Cancelling turn task (%s)", reason)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Turn task cancelled successfully (%s)", reason)
            except Exception:  # noqa: BLE001
                logger.exception("Error while cancelling turn (%s)", reason)
        self._turn_task = None

    async def _run_turn(self, pcm: bytes) -> None:
        async with self._turn_lock:
            t0 = time.perf_counter()
            timings: dict[str, float] = {}
            sentence_queue: asyncio.Queue[Any] = asyncio.Queue()
            tts_worker: asyncio.Task[dict[str, float]] | None = None

            try:
                await self.set_state(SessionState.TRANSCRIBING)
                audio = pcm16_bytes_to_float32(pcm)
                stt_t0 = time.perf_counter()
                stt_result = await self.runtime.run_on_gpu(
                    self.runtime.stt.transcribe_array,
                    audio,
                    sample_rate=self.sample_rate,
                )
                timings["stt_s"] = time.perf_counter() - stt_t0

                if self.cancel_event.is_set():
                    await self.safe_send_json(msg(ServerEvent.CANCELLED))
                    return

                if not stt_result.text:
                    await self.send_json(
                        msg(ServerEvent.ERROR, message="Empty transcription")
                    )
                    await self.set_state(SessionState.LISTENING)
                    return

                await self.send_json(
                    msg(
                        ServerEvent.TRANSCRIPT,
                        role="user",
                        text=stt_result.text,
                        stt_s=round(timings["stt_s"], 3),
                    )
                )

                await self.set_state(SessionState.THINKING)
                full_reply: list[str] = []
                dual = DualChannelSplitter()
                sentence_buf = SentenceBuffer()
                llm_t0 = time.perf_counter()

                tts_worker = asyncio.create_task(
                    self._tts_consumer(sentence_queue, t0),
                    name="elevate-tts-consumer",
                )

                async for delta in self.runtime.llm.chat_stream_async(
                    stt_result.text,
                    system=self._system_prompt,
                    cancel_event=self.cancel_event,
                    history=list(self.history),
                ):
                    if self.cancel_event.is_set():
                        break

                    full_reply.append(delta)
                    speak_delta = dual.push(delta)
                    if speak_delta:
                        await self.safe_send_json(
                            msg(ServerEvent.TOKEN, text=speak_delta)
                        )
                        for sentence in sentence_buf.push(speak_delta):
                            logger.info(
                                "Sentence buffer flush → TTS queue: %r", sentence[:80]
                            )
                            await sentence_queue.put(sentence)

                leftover_speak = dual.flush()
                if leftover_speak:
                    for sentence in sentence_buf.push(leftover_speak + "\n"):
                        await sentence_queue.put(sentence)
                leftover = sentence_buf.flush()
                if leftover and not self.cancel_event.is_set():
                    logger.info("Sentence buffer final flush → TTS: %r", leftover[:80])
                    await sentence_queue.put(leftover)

                await sentence_queue.put(_SENTINEL)
                tts_stats = await tts_worker
                tts_worker = None
                timings["llm_stream_s"] = time.perf_counter() - llm_t0
                timings["tts_s"] = tts_stats.get("tts_s", 0.0)
                timings["time_to_first_audio_s"] = tts_stats.get(
                    "time_to_first_audio_s", time.perf_counter() - t0
                )
                sentence_index = int(tts_stats.get("sentences", 0))

                if self.cancel_event.is_set():
                    await self.safe_send_json(msg(ServerEvent.CANCELLED))
                    await self.set_state(SessionState.LISTENING)
                    return

                raw_reply = "".join(full_reply).strip()
                reply_text = spoken_only_from_full(raw_reply) or raw_reply
                timings["total_s"] = time.perf_counter() - t0

                feedback = dual.parse_feedback()
                if feedback is not None:
                    await self.safe_send_json(
                        msg(ServerEvent.FEEDBACK, feedback=feedback)
                    )

                # Persist spoken-only text into rolling session memory + SQLite.
                if reply_text and not self.cancel_event.is_set():
                    self.history.append({"role": "user", "content": stt_result.text})
                    self.history.append({"role": "assistant", "content": reply_text})
                    if len(self.history) > _MAX_HISTORY_MESSAGES:
                        self.history = self.history[-_MAX_HISTORY_MESSAGES:]
                    ttfa = timings.get("time_to_first_audio_s")
                    if isinstance(ttfa, (int, float)):
                        self.ttfa_samples.append(float(ttfa))
                    try:
                        self.memory.record_turn(
                            user_id=self.user_id,
                            session_id=self.session_id,
                            user_text=stt_result.text,
                            assistant_text=reply_text,
                            feedback=feedback,
                        )
                    except Exception:  # noqa: BLE001
                        logger.exception("SQLite record_turn failed")
                    logger.info(
                        "Session history: %d messages (~%d turns)",
                        len(self.history),
                        len(self.history) // 2,
                    )

                await self.send_json(
                    msg(ServerEvent.TRANSCRIPT, role="assistant", text=reply_text)
                )
                await self.send_json(
                    msg(
                        ServerEvent.TURN_DONE,
                        sentences=sentence_index,
                        timings={k: round(v, 3) for k, v in timings.items()},
                        has_feedback=feedback is not None,
                    )
                )
                await self.set_state(SessionState.LISTENING)
            except asyncio.CancelledError:
                logger.info("Turn CancelledError — stopping LLM/TTS workers")
                self.cancel_event.set()
                if tts_worker and not tts_worker.done():
                    await sentence_queue.put(_SENTINEL)
                    tts_worker.cancel()
                    try:
                        await tts_worker
                    except asyncio.CancelledError:
                        pass
                await self.safe_send_json(msg(ServerEvent.CANCELLED))
                await self.set_state(SessionState.LISTENING)
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Turn failed")
                self.cancel_event.set()
                if tts_worker and not tts_worker.done():
                    await sentence_queue.put(_SENTINEL)
                    try:
                        await tts_worker
                    except Exception:  # noqa: BLE001
                        pass
                await self.safe_send_json(msg(ServerEvent.ERROR, message=str(exc)))
                await self.set_state(SessionState.LISTENING)

    async def _tts_consumer(
        self, queue: asyncio.Queue[Any], turn_t0: float
    ) -> dict[str, float]:
        """Consume sentences while LLM keeps streaming (overlap Ollama ∥ Kokoro)."""
        sentence_index = 0
        tts_total = 0.0
        first_audio_s: float | None = None

        while True:
            if self.cancel_event.is_set():
                # Drain remaining items without synthesizing.
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                logger.info("TTS consumer stopped by cancel_event")
                break

            item = await queue.get()
            if item is _SENTINEL:
                break
            if self.cancel_event.is_set():
                break

            sentence = str(item)
            if self.state != SessionState.SPEAKING:
                await self.set_state(SessionState.SPEAKING)

            sent = await self._speak_sentence(sentence, sentence_index)
            if sent is None:
                break
            tts_s, _sr = sent
            tts_total += tts_s
            if first_audio_s is None:
                first_audio_s = time.perf_counter() - turn_t0
                logger.info("Time-to-first-audio: %.3fs", first_audio_s)
            sentence_index += 1

        return {
            "tts_s": tts_total,
            "time_to_first_audio_s": first_audio_s or 0.0,
            "sentences": float(sentence_index),
        }

    async def _speak_sentence(
        self, sentence: str, index: int
    ) -> tuple[float, int] | None:
        if self.cancel_event.is_set():
            return None

        await self.safe_send_json(
            msg(ServerEvent.SENTENCE, text=sentence, index=index)
        )

        tts_t0 = time.perf_counter()
        result = await self.runtime.run_on_gpu(
            self.runtime.tts.synthesize_pcm, sentence
        )
        tts_s = time.perf_counter() - tts_t0

        if self.cancel_event.is_set():
            logger.info("Dropping TTS PCM after cancel (sentence=%d)", index)
            return None

        pcm = result.pcm16 or b""
        await self.safe_send_json(
            msg(
                ServerEvent.AUDIO_META,
                sample_rate=result.sample_rate,
                sentence_index=index,
                num_samples=result.num_samples,
                engine=result.engine,
                tts_s=round(tts_s, 3),
            )
        )

        for i in range(0, len(pcm), _PCM_FRAME_BYTES):
            if self.cancel_event.is_set():
                logger.info("Abort PCM frame send (sentence=%d)", index)
                return None
            chunk = pcm[i : i + _PCM_FRAME_BYTES]
            await self.send_bytes(chunk)
            await asyncio.sleep(0)

        return tts_s, result.sample_rate

    async def set_state(self, state: SessionState) -> None:
        self.state = state
        await self.safe_send_json(msg(ServerEvent.STATE, state=state.value))

    async def send_json(self, payload: dict[str, Any]) -> None:
        await self.ws.send_json(payload)

    async def send_bytes(self, data: bytes) -> None:
        await self.ws.send_bytes(data)

    async def safe_send_json(self, payload: dict[str, Any]) -> None:
        if self.ws.client_state != WebSocketState.CONNECTED:
            return
        try:
            await self.ws.send_json(payload)
        except Exception:  # noqa: BLE001
            logger.debug("Failed to send JSON on closing socket", exc_info=True)


async def audio_websocket(websocket: WebSocket) -> None:
    session = AudioWsSession(websocket)
    await session.run()
