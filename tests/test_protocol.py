"""Quick unit checks for Phase 2 helpers (no GPU required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import Settings
from app.prompts.tutor_system import scenario_instruction
from app.services.llm import OllamaLLM
from app.ws.dual_channel import DualChannelSplitter, spoken_only_from_full
from app.ws.sentence_buffer import SentenceBuffer


def test_sentence_buffer_basic() -> None:
    buf = SentenceBuffer()
    assert buf.push("Hello there") == []
    assert buf.push(". How are you?") == ["Hello there.", "How are you?"]
    assert buf.flush() is None


def test_sentence_buffer_newline() -> None:
    buf = SentenceBuffer()
    assert buf.push("Line one\nLine two.") == ["Line one", "Line two."]
    assert buf.flush() is None


def test_sentence_buffer_flush_leftover() -> None:
    buf = SentenceBuffer()
    buf.push("Almost done")
    assert buf.flush() == "Almost done"


def test_dual_channel_tokenized_markers() -> None:
    """Ollama often yields <<< as its own token; holdback must not leak it."""
    split = DualChannelSplitter()
    speak = ""
    for piece in ("<<<", "SPEAK>>>", "\nHello.", "\n<<<", "FEEDBACK>>>\n", '{"grammar":[],"phrasing":[],"pronunciation":[],"notes":""}'):
        speak += split.push(piece)
    speak += split.flush()
    assert speak.strip() == "Hello."
    assert split.parse_feedback() is not None


def test_dual_channel_streaming() -> None:
    split = DualChannelSplitter()
    speak = ""
    speak += split.push("<<<SPEAK>>>\nNice try. ")
    speak += split.push("Keep going.")
    speak += split.push("\n<<<FEEDBACK>>>\n")
    speak += split.push(
        '{"grammar":[],"phrasing":[{"original":"nice try","upgrade":"solid attempt","note":"C1"}],'
        '"pronunciation":[],"notes":"Good."}'
    )
    speak += split.flush()
    assert "Nice try." in speak
    assert "Keep going." in speak
    assert "{" not in speak
    fb = split.parse_feedback()
    assert fb is not None
    assert len(fb["phrasing"]) == 1
    assert fb["notes"] == "Good."


def test_spoken_only_from_full() -> None:
    raw = (
        "<<<SPEAK>>>\nHello there.\n<<<FEEDBACK>>>\n"
        '{"grammar":[],"phrasing":[],"pronunciation":[],"notes":""}'
    )
    assert spoken_only_from_full(raw) == "Hello there."


def test_protocol_imports() -> None:
    from app.ws.protocol import ClientEvent, ServerEvent

    assert ClientEvent.CANCEL_AUDIO == "CANCEL_AUDIO"
    assert ServerEvent.TURN_DONE == "TURN_DONE"
    assert ServerEvent.FEEDBACK == "FEEDBACK"


def test_llm_payload_includes_vram_guards() -> None:
    settings = Settings(
        ollama_num_ctx=2048,
        ollama_num_predict=220,
        ollama_keep_alive="-1",
    )
    llm = OllamaLLM(settings)
    assert llm.keep_alive_value() == -1
    payload = llm._chat_payload(
        "hi", system="sys", model_name="llama3.1:8b", stream=True
    )
    assert payload["keep_alive"] == -1
    assert isinstance(payload["keep_alive"], int)
    assert payload["options"]["num_ctx"] == 2048
    assert payload["options"]["num_predict"] == 220


def test_scenario_instruction_free_not_job() -> None:
    free = scenario_instruction("free")
    assert "Active scenario: free" in free
    assert "Do NOT default to job interviews" in free
    job = scenario_instruction("job")
    assert "Active scenario: job" in job
    assert "interviewer" in job


if __name__ == "__main__":
    test_sentence_buffer_basic()
    test_sentence_buffer_newline()
    test_sentence_buffer_flush_leftover()
    test_dual_channel_tokenized_markers()
    test_dual_channel_streaming()
    test_spoken_only_from_full()
    test_protocol_imports()
    test_llm_payload_includes_vram_guards()
    test_scenario_instruction_free_not_job()
    print("Phase 2 unit checks OK")
