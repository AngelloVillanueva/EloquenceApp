"""Shadow scoring and prompt merge (no GPU)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.shadow import clean_gloss, coach_word, merge_prompts, score_repeat


def test_score_repeat_hits() -> None:
    out = score_repeat("Let me elaborate on that point.", "Let me elaborate on that point")
    assert out["hits"] == out["total"]
    assert out["close"] is True
    assert all(w["ok"] for w in out["words"])
    assert out["coach"] == []


def test_score_repeat_partial() -> None:
    out = score_repeat("circle back after the review", "circle after review")
    assert out["hits"] == 3
    assert out["total"] == 5
    assert out["close"] is False
    missed = [w["word"] for w in out["words"] if not w["ok"]]
    assert missed == ["back", "the"]
    # Every miss ships an actionable fix, never just a red word.
    assert [c["word"] for c in out["coach"]] == ["back", "the"]
    assert all(c["fixes"] for c in out["coach"])


def test_coach_word_targets_spanish_transfer() -> None:
    assert any("th" in fix for fix in coach_word("think"))
    assert any("«e»" in fix for fix in coach_word("speak"))
    assert coach_word("") == []
    assert coach_word("elaborate")  # falls back to a generic but usable cue


def test_clean_gloss_strips_noise() -> None:
    assert clean_gloss('  "Hola, ¿cómo estás?"  ') == "Hola, ¿cómo estás?"
    assert clean_gloss("Traducción: Buenos días\nextra") == "Buenos días"
    assert clean_gloss("") == ""


def test_merge_prompts_prefers_slips() -> None:
    prompts = merge_prompts(
        [{"original": "Eloquence", "note": "Four syllables"}],
        limit=3,
        level="B2",
    )
    assert prompts[0]["text"] == "Eloquence"
    assert prompts[0]["kind"] == "pronunciation"
    assert len(prompts) == 3
    assert any(p["kind"] == "bank" for p in prompts)
    assert all(p.get("es") is not None for p in prompts)
    assert any(p["kind"] == "bank" and p["es"] for p in prompts)


def test_merge_prompts_filters_by_cefr() -> None:
    b1 = merge_prompts([], limit=12, level="B1")
    assert b1
    assert all(p.get("cefr") == "B1" for p in b1)
    assert all("non-negotiable" not in p["text"].lower() for p in b1)
    assert all("walk me through" not in p["text"].lower() for p in b1)

    b2 = merge_prompts([], limit=12, level="B2")
    cefr_b2 = {p.get("cefr") for p in b2}
    assert "B1" in cefr_b2 and "B2" in cefr_b2
    assert "C1" not in cefr_b2

    c1 = merge_prompts([], limit=12, level="C1")
    cefr_c1 = {p.get("cefr") for p in c1}
    assert "B2" in cefr_c1 and "C1" in cefr_c1
    assert "B1" not in cefr_c1
    assert any("non-negotiable" in p["text"].lower() for p in c1)


if __name__ == "__main__":
    test_score_repeat_hits()
    test_score_repeat_partial()
    test_coach_word_targets_spanish_transfer()
    test_clean_gloss_strips_noise()
    test_merge_prompts_prefers_slips()
    test_merge_prompts_filters_by_cefr()
    print("shadow tests OK")
