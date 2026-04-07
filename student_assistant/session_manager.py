"""In-memory session storage keyed by WhatsApp phone number (student_id)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_sessions: dict[str, dict[str, Any]] = {}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_session(student_id: str) -> dict[str, Any]:
    now = _utc_now_iso()
    return {
        "student_id": student_id,
        "current_lesson_id": None,
        "current_lesson_file": None,
        "difficulty": "normal",
        "menu_state": "main",
        "awaiting_answer": False,
        "awaiting_lesson_selection": False,
        "last_questions": [],
        "lesson_choices": [],
        "started_at": now,
        "updated_at": now,
        # Index of current practice question within last_questions (0-based).
        "practice_q_index": 0,
    }


def load_session(student_id: str) -> dict[str, Any]:
    if student_id not in _sessions:
        _sessions[student_id] = default_session(student_id)
    return _sessions[student_id]


def save_session(session: dict[str, Any]) -> None:
    sid = session.get("student_id")
    if not sid:
        return
    session["updated_at"] = _utc_now_iso()
    _sessions[sid] = session


def touch_session(student_id: str) -> None:
    s = load_session(student_id)
    save_session(s)


def reset_session(student_id: str) -> None:
    _sessions[student_id] = default_session(student_id)
