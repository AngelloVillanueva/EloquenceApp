"""CEFR levels, scenario gates, and SPEAK-language guard (no GPU)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.prompts.tutor_system import (
    clamp_scenario,
    normalize_level,
    scenario_allowed,
    spoken_tutor_prompt,
)
from app.ws.dual_channel import looks_like_spanish, spoken_only_from_full, strip_spanish_sentences


def test_normalize_level() -> None:
    assert normalize_level("b1") == "B1"
    assert normalize_level("C1") == "C1"
    assert normalize_level("nope") == "B2"
    assert normalize_level(None) == "B2"


def test_spoken_tutor_prompt_b1_spanish_notes_english_speak() -> None:
    b1 = spoken_tutor_prompt("B1")
    assert "B1" in b1
    assert "Latin American Spanish" in b1
    assert "Never Spanish" in b1
    assert "C1 idioms" in b1
    assert "everyday words" in b1.lower() or "Everyday words" in b1

    b2 = spoken_tutor_prompt("B2")
    assert "Latin American Spanish" in b2
    assert "Never Spanish" in b2

    c1 = spoken_tutor_prompt("C1")
    assert "notes` in English" in c1 or "in English" in c1
    assert "Latin American Spanish" not in c1


def test_scenario_allowed_and_clamp() -> None:
    assert scenario_allowed("free", "B1")
    assert scenario_allowed("vocab", "B1")
    assert not scenario_allowed("job", "B1")
    assert not scenario_allowed("nego", "B2")
    assert scenario_allowed("job", "B2")
    assert scenario_allowed("arch", "C1")
    assert clamp_scenario("nego", "B1") == "free"
    assert clamp_scenario("job", "B2") == "job"
    assert clamp_scenario("unknown", "C1") == "free"


def test_strip_spanish_sentences() -> None:
    assert looks_like_spanish("¿Cómo estás?")
    assert looks_like_spanish("Gracias por venir.")
    assert not looks_like_spanish("How was your day?")
    assert not looks_like_spanish("I'll get back to you this afternoon.")
    mixed = "That sounds good. Gracias por eso."
    assert strip_spanish_sentences(mixed) == "That sounds good."
    assert strip_spanish_sentences("Hola, vamos ahora.") == ""


def test_spoken_only_strips_spanish() -> None:
    raw = (
        "<<<SPEAK>>>\nHello there. Gracias por venir.\n<<<FEEDBACK>>>\n"
        '{"grammar":[],"phrasing":[],"pronunciation":[],"notes":""}'
    )
    assert spoken_only_from_full(raw) == "Hello there."


if __name__ == "__main__":
    test_normalize_level()
    test_spoken_tutor_prompt_b1_spanish_notes_english_speak()
    test_scenario_allowed_and_clamp()
    test_strip_spanish_sentences()
    test_spoken_only_strips_spanish()
    print("level tests OK")
