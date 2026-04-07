"""Practice questions: pick items, check answers, return structured results."""

from __future__ import annotations

from typing import Any

from utils import answers_match, normalize_for_compare


def pick_practice_questions(
    lesson: dict[str, Any], difficulty: str, count: int = 2
) -> list[dict[str, Any]]:
    """Return up to `count` practice items for the tier (easy/normal/hard)."""
    practice = lesson.get("practice") or {}
    tier = practice.get(difficulty) or practice.get("normal") or []
    if not isinstance(tier, list):
        return []
    out: list[dict[str, Any]] = []
    for item in tier[:count]:
        if isinstance(item, dict) and "question" in item:
            out.append(dict(item))
    return out


def check_answer(
    student_reply: str, expected_answer: str, concept: str
) -> dict[str, Any]:
    """Return structured result: correctness, concept, normalized strings."""
    ok = answers_match(student_reply, expected_answer)
    st_norm, exp_norm = normalize_for_compare(student_reply, expected_answer)
    return {
        "correct": ok,
        "concept": concept,
        "student_normalized": st_norm,
        "expected_normalized": exp_norm,
    }


def describe_expected_format(expected_answer: str) -> str:
    """Short hint when the reply cannot be parsed usefully."""
    exp = (expected_answer or "").strip()
    if "," in exp:
        return "Send answers separated by commas, like: word1, word2"
    if len(exp.split()) > 1:
        return "Send all needed words, separated by spaces."
    if "/" in exp:
        return "Use a fraction like 3/4 or a whole number."
    return "Send a short text or number answer."
