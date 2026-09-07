"""SQLite memory service tests (no GPU)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.memory import MemoryService


def test_memory_brief_and_upsert(tmp_path: Path) -> None:
    db = tmp_path / "elevate.db"
    mem = MemoryService(db_path=db)
    uid = mem.ensure_default_user("Angello", "C1")
    sid = mem.start_session(user_id=uid, scenario="job")
    mem.record_turn(
        user_id=uid,
        session_id=sid,
        user_text="I depend of luck.",
        assistant_text="You can depend on preparation more than luck.",
        feedback={
            "grammar": [
                {
                    "original": "depend of",
                    "correction": "depend on",
                    "note": "Spanish transfer",
                }
            ],
            "phrasing": [
                {
                    "original": "depend of luck",
                    "upgrade": "hinge on preparation",
                    "note": "C1",
                }
            ],
            "pronunciation": [
                {"word": "elaborate", "tip": "Stress on lab"}
            ],
            "notes": "",
        },
    )
    mem.record_turn(
        user_id=uid,
        session_id=sid,
        user_text="I depend of that again.",
        assistant_text="Try 'depend on' once more.",
        feedback={
            "grammar": [
                {"original": "depend of", "correction": "depend on", "note": ""}
            ],
            "phrasing": [],
            "pronunciation": [],
            "notes": "",
        },
    )
    mem.end_session(sid, ttfa_avg=1.8)
    brief = mem.build_brief(uid, scenario="job")
    assert "Angello" in brief
    assert "depend of" in brief
    assert "depend on" in brief
    assert "×2" in brief
    snap = mem.snapshot(uid)
    assert snap["sessions"] == 1
    assert snap["errors"][0]["count"] == 2
    assert snap["last_session"] is not None
    assert snap["last_session"]["scenario"] == "job"
    assert "sessions_week" in snap
    assert snap["slip_count"] >= 2
    prompts = mem.shadow_prompts(uid)
    assert prompts[0]["text"] == "elaborate"
    mem.close()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        test_memory_brief_and_upsert(Path(d))
    print("memory tests OK")
