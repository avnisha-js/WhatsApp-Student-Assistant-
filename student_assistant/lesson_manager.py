"""Load and validate lesson JSON files from ./data/lessons/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
LESSONS_DIR = ROOT / "data" / "lessons"

REQUIRED_TOP_LEVEL = (
    "lesson_id",
    "display_name",
    "grade",
    "subject",
    "topic",
    "language",
    "summary",
    "concepts",
    "examples",
    "practice",
)

REQUIRED_PRACTICE_KEYS = ("easy", "normal", "hard")


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _validate_lesson_payload(data: dict[str, Any]) -> None:
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            raise ValueError(f"Missing required field: {key}")

    if not _is_non_empty_str(data["lesson_id"]):
        raise ValueError("lesson_id must be a non-empty string")
    if not _is_non_empty_str(data["display_name"]):
        raise ValueError("display_name must be a non-empty string")

    for list_key in ("concepts", "examples"):
        if not isinstance(data[list_key], list):
            raise ValueError(f"{list_key} must be a list")

    practice = data["practice"]
    if not isinstance(practice, dict):
        raise ValueError("practice must be an object")
    for tier in REQUIRED_PRACTICE_KEYS:
        if tier not in practice:
            raise ValueError(f"practice missing tier: {tier}")
        if not isinstance(practice[tier], list):
            raise ValueError(f"practice.{tier} must be a list")
        for item in practice[tier]:
            if not isinstance(item, dict):
                raise ValueError(f"practice.{tier} items must be objects")
            for f in ("question", "answer", "concept"):
                if f not in item or not _is_non_empty_str(str(item[f]).strip()):
                    raise ValueError(
                        f"Each practice item needs non-empty {f} in tier {tier}"
                    )


def list_lessons() -> list[dict[str, str]]:
    """Return sorted list of {display_name, filename} for each valid lesson file."""
    if not LESSONS_DIR.is_dir():
        return []

    out: list[dict[str, str]] = []
    for path in sorted(LESSONS_DIR.glob("*.json")):
        try:
            data = load_lesson_by_filename(path.name)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        out.append(
            {
                "display_name": str(data["display_name"]),
                "filename": path.name,
            }
        )
    return out


def load_lesson_by_filename(filename: str) -> dict[str, Any]:
    """Load and validate a lesson JSON by filename (e.g. grade_5_math_fractions.json)."""
    if not filename or ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename")
    path = LESSONS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(filename)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Lesson root must be a JSON object")
    _validate_lesson_payload(data)
    return data


def load_lesson_file(path: Path) -> dict[str, Any]:
    """Load lesson from an absolute path (internal use)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Lesson root must be a JSON object")
    _validate_lesson_payload(data)
    return data
