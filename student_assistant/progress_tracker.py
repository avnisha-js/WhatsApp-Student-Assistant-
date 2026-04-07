"""Persist and summarize per-student, per-lesson practice progress."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils import student_progress_filename

ROOT = Path(__file__).resolve().parent
PROGRESS_DIR = ROOT / "data" / "student_progress"


def _ensure_dir() -> None:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)


def _path_for_student(student_id: str) -> Path:
    _ensure_dir()
    return PROGRESS_DIR / student_progress_filename(student_id)


def _load_all(student_id: str) -> dict[str, Any]:
    path = _path_for_student(student_id)
    if not path.is_file():
        return {"student_id": student_id, "lessons": {}}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {"student_id": student_id, "lessons": {}}
    if "lessons" not in data or not isinstance(data["lessons"], dict):
        data["lessons"] = {}
    data["student_id"] = student_id
    return data


def _save_all(student_id: str, data: dict[str, Any]) -> None:
    path = _path_for_student(student_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _ensure_lesson_record(
    lessons: dict[str, Any], lesson_id: str
) -> dict[str, Any]:
    if lesson_id not in lessons or not isinstance(lessons[lesson_id], dict):
        lessons[lesson_id] = {
            "attempted": 0,
            "correct": 0,
            "accuracy": 0.0,
            "strengths": [],
            "weaknesses": [],
            "difficulty": "normal",
            "last_practiced_at": None,
            "concept_tally": {},
        }
    rec = lessons[lesson_id]
    rec.setdefault("attempted", 0)
    rec.setdefault("correct", 0)
    rec.setdefault("accuracy", 0.0)
    rec.setdefault("strengths", [])
    rec.setdefault("weaknesses", [])
    rec.setdefault("difficulty", "normal")
    rec.setdefault("last_practiced_at", None)
    rec.setdefault("concept_tally", {})
    if not isinstance(rec["strengths"], list):
        rec["strengths"] = []
    if not isinstance(rec["weaknesses"], list):
        rec["weaknesses"] = []
    if not isinstance(rec["concept_tally"], dict):
        rec["concept_tally"] = {}
    return rec


def record_answer(
    student_id: str,
    lesson_id: str,
    concept: str,
    is_correct: bool,
    session_difficulty: str,
) -> dict[str, Any]:
    """Update progress after one practice answer. Returns updated lesson record."""
    data = _load_all(student_id)
    lessons: dict[str, Any] = data["lessons"]
    rec = _ensure_lesson_record(lessons, lesson_id)

    rec["attempted"] = int(rec["attempted"]) + 1
    if is_correct:
        rec["correct"] = int(rec["correct"]) + 1

    attempted = max(rec["attempted"], 1)
    rec["accuracy"] = round(rec["correct"] / attempted, 4)

    tally: dict[str, Any] = rec["concept_tally"]
    if concept not in tally or not isinstance(tally[concept], dict):
        tally[concept] = {"correct": 0, "wrong": 0}
    tc = tally[concept]
    if is_correct:
        tc["correct"] = int(tc.get("correct", 0)) + 1
    else:
        tc["wrong"] = int(tc.get("wrong", 0)) + 1

    if tc["correct"] >= 2 and concept not in rec["strengths"]:
        rec["strengths"].append(concept)
    if tc["wrong"] >= 2 and concept not in rec["weaknesses"]:
        rec["weaknesses"].append(concept)

    rec["difficulty"] = session_difficulty
    rec["last_practiced_at"] = datetime.now(timezone.utc).isoformat()

    _save_all(student_id, data)
    return rec


def get_lesson_progress(student_id: str, lesson_id: str) -> dict[str, Any] | None:
    data = _load_all(student_id)
    rec = data["lessons"].get(lesson_id)
    return dict(rec) if isinstance(rec, dict) else None


def format_progress_summary(student_id: str, lesson_id: str) -> str:
    """Short WhatsApp-friendly summary for current lesson."""
    rec = get_lesson_progress(student_id, lesson_id)
    if not rec or rec.get("attempted", 0) == 0:
        return (
            "No practice data for this lesson yet. Try option 3 (Practice Problem)."
        )
    acc = rec.get("accuracy", 0)
    pct = int(round(float(acc) * 100))
    strengths = rec.get("strengths") or []
    weaknesses = rec.get("weaknesses") or []
    lines = [
        f"Attempts: {rec.get('attempted', 0)} | Correct: {rec.get('correct', 0)} | About {pct}% accuracy.",
        f"Level used: {rec.get('difficulty', 'normal')}.",
    ]
    if strengths:
        lines.append("Strengths: " + ", ".join(strengths[:5]))
    if weaknesses:
        lines.append("To improve: " + ", ".join(weaknesses[:5]))
    if not strengths and not weaknesses:
        lines.append("Keep practicing — we will spot strengths and gaps after more answers.")
    return "\n".join(lines)
