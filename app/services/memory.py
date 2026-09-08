"""Local SQLite memory — FastAPI owns SQL; the LLM only receives a text brief."""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'B2',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    scenario TEXT NOT NULL DEFAULT 'free',
    started_at TEXT NOT NULL,
    ended_at TEXT,
    duration_s REAL,
    ttfa_avg REAL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    user_text TEXT NOT NULL,
    assistant_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
CREATE TABLE IF NOT EXISTS errors (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL,
    original TEXT NOT NULL,
    correction TEXT NOT NULL,
    note TEXT,
    count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS vocab (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    word_or_phrase TEXT NOT NULL,
    context TEXT,
    mastery INTEGER NOT NULL DEFAULT 0,
    last_seen_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX IF NOT EXISTS idx_errors_user ON errors(user_id, count DESC);
CREATE INDEX IF NOT EXISTS idx_vocab_user ON vocab(user_id, last_seen_at DESC);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _iso_day(stamp: str | None) -> str | None:
    if not stamp:
        return None
    return str(stamp)[:10]


def _streak(days: list[str], today: str) -> int:
    have = {d for d in days if d}
    if not have:
        return 0
    cursor = datetime.fromisoformat(today).date()
    latest = max(datetime.fromisoformat(d).date() for d in have)
    if latest < cursor - timedelta(days=1):
        return 0
    n = 0
    day = latest
    while day.isoformat() in have:
        n += 1
        day -= timedelta(days=1)
    return n


def _hub_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    week_from = now - timedelta(days=7)
    today = now.date().isoformat()
    minutes_total = 0.0
    minutes_week = 0.0
    sessions_week = 0
    days: list[str] = []
    ended = [r for r in rows if r.get("ended_at")]
    for r in ended:
        dur = float(r.get("duration_s") or 0)
        minutes_total += dur
        ended_at = str(r.get("ended_at") or "")
        try:
            when = datetime.fromisoformat(ended_at)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when >= week_from:
                minutes_week += dur
                sessions_week += 1
        except ValueError:
            pass
        day = _iso_day(ended_at)
        if day:
            days.append(day)
    last = ended[0] if ended else None
    recent = [
        {
            "scenario": r.get("scenario"),
            "duration_s": r.get("duration_s"),
            "ttfa_avg": r.get("ttfa_avg"),
            "ended_at": r.get("ended_at"),
        }
        for r in ended[:5]
    ]
    return {
        "sessions_week": sessions_week,
        "minutes_total": int(round(minutes_total / 60)),
        "minutes_week": int(round(minutes_week / 60)),
        "streak_days": _streak(days, today),
        "last_session": last,
        "recent_sessions": recent,
    }


class MemoryService:
    """Thread-safe SQLite store for sessions, slips, and C1 vocab."""

    def __init__(self, db_path: Path | None = None) -> None:
        settings = get_settings()
        self.path = Path(db_path or settings.sqlite_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self.ensure_default_user()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def ensure_default_user(self, display_name: str = "Angello", level: str = "B2") -> int:
        """Create the single local user if missing. Never overwrite a stored level."""
        from app.prompts.tutor_system import normalize_level

        level = normalize_level(level)
        with self._lock:
            row = self._conn.execute(
                "SELECT id FROM users ORDER BY id LIMIT 1"
            ).fetchone()
            if row:
                return int(row["id"])
            cur = self._conn.execute(
                "INSERT INTO users (display_name, level, created_at) VALUES (?, ?, ?)",
                (display_name, level, _now()),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def get_level(self, user_id: int) -> str:
        from app.prompts.tutor_system import normalize_level

        with self._lock:
            row = self._conn.execute(
                "SELECT level FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return normalize_level(row["level"] if row else "B2")

    def set_level(self, user_id: int, level: str) -> str:
        from app.prompts.tutor_system import normalize_level

        cefr = normalize_level(level)
        with self._lock:
            self._conn.execute(
                "UPDATE users SET level = ? WHERE id = ?",
                (cefr, user_id),
            )
            self._conn.commit()
        logger.info("User %s level set to %s", user_id, cefr)
        return cefr

    def start_session(self, *, user_id: int, scenario: str) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO sessions (user_id, scenario, started_at) VALUES (?, ?, ?)",
                (user_id, scenario, _now()),
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def end_session(self, session_id: int | None, *, ttfa_avg: float | None = None) -> None:
        if not session_id:
            return
        with self._lock:
            row = self._conn.execute(
                "SELECT started_at FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if not row:
                return
            started = datetime.fromisoformat(row["started_at"])
            ended = datetime.now(timezone.utc)
            duration = (ended - started).total_seconds()
            self._conn.execute(
                "UPDATE sessions SET ended_at = ?, duration_s = ?, ttfa_avg = ? WHERE id = ?",
                (ended.isoformat(timespec="seconds"), duration, ttfa_avg, session_id),
            )
            self._conn.commit()

    def record_turn(
        self,
        *,
        user_id: int,
        session_id: int | None,
        user_text: str,
        assistant_text: str,
        feedback: dict[str, Any] | None,
    ) -> None:
        if not session_id:
            return
        with self._lock:
            self._conn.execute(
                "INSERT INTO turns (session_id, user_text, assistant_text, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, user_text, assistant_text, _now()),
            )
            if feedback:
                self._ingest_feedback_locked(user_id, feedback)
            self._conn.commit()

    def _ingest_feedback_locked(self, user_id: int, feedback: dict[str, Any]) -> None:
        stamp = _now()
        for item in feedback.get("grammar") or []:
            if not isinstance(item, dict):
                continue
            original = str(item.get("original") or "").strip()
            correction = str(item.get("correction") or "").strip()
            if not original or not correction:
                continue
            note = str(item.get("note") or "")
            self._upsert_error(user_id, "grammar", original, correction, note, stamp)

        for item in feedback.get("phrasing") or []:
            if not isinstance(item, dict):
                continue
            original = str(item.get("original") or "").strip()
            upgrade = str(item.get("upgrade") or item.get("correction") or "").strip()
            if not original or not upgrade:
                continue
            note = str(item.get("note") or "")
            self._upsert_error(user_id, "phrasing", original, upgrade, note, stamp)
            self._upsert_vocab(user_id, upgrade, original, stamp)

        for item in feedback.get("pronunciation") or []:
            if not isinstance(item, dict):
                continue
            word = str(item.get("word") or "").strip()
            if not word:
                continue
            tip = str(item.get("tip") or "")
            self._upsert_error(user_id, "pronunciation", word, word, tip, stamp)

    def _upsert_error(
        self,
        user_id: int,
        kind: str,
        original: str,
        correction: str,
        note: str,
        stamp: str,
    ) -> None:
        existing = self._conn.execute(
            "SELECT id, count FROM errors WHERE user_id = ? AND kind = ? AND original = ?",
            (user_id, kind, original),
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE errors SET correction = ?, note = ?, count = ?, last_seen_at = ? WHERE id = ?",
                (correction, note, int(existing["count"]) + 1, stamp, existing["id"]),
            )
        else:
            self._conn.execute(
                "INSERT INTO errors (user_id, kind, original, correction, note, count, last_seen_at) "
                "VALUES (?, ?, ?, ?, ?, 1, ?)",
                (user_id, kind, original, correction, note, stamp),
            )

    def _upsert_vocab(self, user_id: int, phrase: str, context: str, stamp: str) -> None:
        existing = self._conn.execute(
            "SELECT id FROM vocab WHERE user_id = ? AND word_or_phrase = ?",
            (user_id, phrase),
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE vocab SET context = ?, last_seen_at = ? WHERE id = ?",
                (context, stamp, existing["id"]),
            )
        else:
            self._conn.execute(
                "INSERT INTO vocab (user_id, word_or_phrase, context, mastery, last_seen_at) "
                "VALUES (?, ?, ?, 0, ?)",
                (user_id, phrase, context, stamp),
            )

    def build_brief(self, user_id: int, *, scenario: str = "") -> str:
        """Short text injected into the LLM system prompt — never spoken."""
        with self._lock:
            user = self._conn.execute(
                "SELECT display_name, level FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            errors = self._conn.execute(
                "SELECT kind, original, correction, count FROM errors "
                "WHERE user_id = ? ORDER BY count DESC, last_seen_at DESC LIMIT 5",
                (user_id,),
            ).fetchall()
            vocab = self._conn.execute(
                "SELECT word_or_phrase FROM vocab WHERE user_id = ? "
                "ORDER BY last_seen_at DESC LIMIT 5",
                (user_id,),
            ).fetchall()
            last = self._conn.execute(
                "SELECT scenario, duration_s FROM sessions WHERE user_id = ? AND ended_at IS NOT NULL "
                "ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()

        name = user["display_name"] if user else "learner"
        level = user["level"] if user else "B2"
        lines = [
            f"User: {name} · Level {level}"
            + (f" · Scenario: {scenario}" if scenario else ""),
        ]
        if errors:
            slips = "; ".join(
                f'{r["original"]} → {r["correction"]} ({r["kind"]} ×{r["count"]})'
                for r in errors
            )
            lines.append(f"Recurring slips: {slips}")
        if vocab:
                lines.append("Targets: " + ", ".join(r["word_or_phrase"] for r in vocab))
        if last:
            mins = (last["duration_s"] or 0) / 60
            lines.append(f"Last session: {mins:.0f} min · {last['scenario']}")
        return "\n".join(lines)

    def snapshot(self, user_id: int) -> dict[str, Any]:
        with self._lock:
            user = self._conn.execute(
                "SELECT display_name, level FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            n_sessions = self._conn.execute(
                "SELECT COUNT(*) AS n FROM sessions WHERE user_id = ?", (user_id,)
            ).fetchone()["n"]
            errors = [
                dict(r)
                for r in self._conn.execute(
                    "SELECT kind, original, correction, note, count FROM errors "
                    "WHERE user_id = ? ORDER BY count DESC LIMIT 8",
                    (user_id,),
                )
            ]
            vocab = [
                dict(r)
                for r in self._conn.execute(
                    "SELECT word_or_phrase, context FROM vocab WHERE user_id = ? "
                    "ORDER BY last_seen_at DESC LIMIT 8",
                    (user_id,),
                )
            ]
            session_rows = [
                dict(r)
                for r in self._conn.execute(
                    "SELECT scenario, duration_s, ttfa_avg, started_at, ended_at "
                    "FROM sessions WHERE user_id = ? ORDER BY id DESC LIMIT 40",
                    (user_id,),
                )
            ]
        stats = _hub_stats(session_rows)
        slip_count = sum(int(e.get("count") or 0) for e in errors)
        return {
            "user": dict(user) if user else None,
            "sessions": n_sessions,
            "brief": self.build_brief(user_id),
            "errors": errors,
            "vocab": vocab,
            "slip_count": slip_count,
            **stats,
        }

    def shadow_prompts(
        self,
        user_id: int,
        *,
        limit: int = 12,
        level: str | None = None,
    ) -> list[dict[str, Any]]:
        from app.services.shadow import merge_prompts

        cefr = level or self.get_level(user_id)
        with self._lock:
            slips = [
                dict(r)
                for r in self._conn.execute(
                    "SELECT original, note FROM errors "
                    "WHERE user_id = ? AND kind = 'pronunciation' "
                    "ORDER BY count DESC, last_seen_at DESC LIMIT ?",
                    (user_id, limit),
                )
            ]
        return merge_prompts(slips, limit=limit, level=cefr)


_memory: MemoryService | None = None


def get_memory() -> MemoryService:
    global _memory
    if _memory is None:
        _memory = MemoryService()
        logger.info("SQLite memory ready at %s", _memory.path)
    return _memory
