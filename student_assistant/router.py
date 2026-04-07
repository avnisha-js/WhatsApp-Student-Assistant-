"""Route WhatsApp text to menu actions; text-only responses."""

from __future__ import annotations

import json
from typing import Any

from lesson_manager import load_lesson_by_filename, list_lessons
from practice_engine import (
    check_answer,
    describe_expected_format,
    pick_practice_questions,
)
from progress_tracker import format_progress_summary, record_answer
from session_manager import load_session, reset_session, save_session

INVALID_MENU = "Invalid choice. Please enter a number from 1 to 7."
NO_LESSON = "Please select a lesson first.\n\n1. Select Lesson\n7. Exit"
MISSING_LESSON = (
    "Sorry, this lesson is not available right now. Please select another lesson."
)
INVALID_LESSON_NUM = "Invalid choice. Please select a lesson number."


def main_menu_text() -> str:
    return (
        "1. Select Lesson\n"
        "2. Explain Lesson\n"
        "3. Practice Problem\n"
        "4. How Am I Doing\n"
        "5. Make It Easier\n"
        "6. Make It Harder\n"
        "7. Exit"
    )


def _has_lesson(session: dict[str, Any]) -> bool:
    return bool(session.get("current_lesson_id") and session.get("current_lesson_file"))


def _load_current_lesson(session: dict[str, Any]) -> dict[str, Any]:
    fn = session.get("current_lesson_file")
    if not fn:
        raise FileNotFoundError
    return load_lesson_by_filename(str(fn))


def _parse_menu_choice(raw: str) -> int | None:
    raw = (raw or "").strip()
    if not raw.isdigit():
        return None
    n = int(raw)
    if 1 <= n <= 7:
        return n
    return None


def _handle_lesson_pick(student_id: str, session: dict[str, Any], raw: str) -> str:
    raw = (raw or "").strip()
    if not raw.isdigit():
        return INVALID_LESSON_NUM
    idx = int(raw) - 1
    choices: list[str] = list(session.get("lesson_choices") or [])
    if idx < 0 or idx >= len(choices):
        return INVALID_LESSON_NUM
    filename = choices[idx]
    try:
        lesson = load_lesson_by_filename(filename)
    except FileNotFoundError:
        return MISSING_LESSON
    except (OSError, ValueError, json.JSONDecodeError):
        return MISSING_LESSON

    session["current_lesson_id"] = lesson["lesson_id"]
    session["current_lesson_file"] = filename
    session["awaiting_lesson_selection"] = False
    session["lesson_choices"] = []
    save_session(session)
    return f"Selected: {lesson['display_name']}\n\n{main_menu_text()}"


def _handle_practice_answer(student_id: str, session: dict[str, Any], raw: str) -> str:
    last: list[dict[str, Any]] = list(session.get("last_questions") or [])
    idx = int(session.get("practice_q_index") or 0)
    if idx >= len(last):
        session["awaiting_answer"] = False
        session["last_questions"] = []
        save_session(session)
        return "Practice finished.\n\n" + main_menu_text()

    q = last[idx]
    concept = str(q.get("concept") or "")
    expected = str(q.get("answer") or "")

    reply = (raw or "").strip()
    if not reply:
        hint = describe_expected_format(expected)
        return f"Please type an answer. {hint}"

    result = check_answer(reply, expected, concept)
    lesson_id = str(session.get("current_lesson_id") or "")
    record_answer(
        student_id,
        lesson_id,
        result["concept"],
        bool(result["correct"]),
        str(session.get("difficulty") or "normal"),
    )

    lines: list[str] = []
    if result["correct"]:
        lines.append("Correct!")
    else:
        lines.append(f"Not quite. Expected something like: {result['expected_normalized']}")

    idx += 1
    session["practice_q_index"] = idx
    if idx >= len(last):
        session["awaiting_answer"] = False
        session["last_questions"] = []
        save_session(session)
        lines.append("Done with this round.")
        lines.append(main_menu_text())
        return "\n".join(lines)

    session["awaiting_answer"] = True
    save_session(session)
    nq = last[idx]["question"]
    lines.append(f"Next:\n{nq}")
    return "\n".join(lines)


def _start_lesson_selection(student_id: str, session: dict[str, Any]) -> str:
    lessons = list_lessons()
    if not lessons:
        return "No lessons are available right now. Try again later.\n\n" + main_menu_text()

    lines = ["Pick a lesson (reply with the number):"]
    choices: list[str] = []
    for i, item in enumerate(lessons, start=1):
        lines.append(f"{i}. {item['display_name']}")
        choices.append(item["filename"])

    session["lesson_choices"] = choices
    session["awaiting_lesson_selection"] = True
    save_session(session)
    return "\n".join(lines)


def _start_practice(student_id: str, session: dict[str, Any]) -> str:
    try:
        lesson = _load_current_lesson(session)
    except FileNotFoundError:
        return MISSING_LESSON
    except (OSError, ValueError, json.JSONDecodeError):
        return MISSING_LESSON

    diff = str(session.get("difficulty") or "normal")
    qs = pick_practice_questions(lesson, diff, 2)
    if not qs:
        return (
            "No practice questions for this level. Try another difficulty.\n\n"
            + main_menu_text()
        )

    session["last_questions"] = qs
    session["practice_q_index"] = 0
    session["awaiting_answer"] = True
    save_session(session)
    return f"Question 1:\n{qs[0]['question']}"


def _explain_lesson(session: dict[str, Any]) -> str:
    try:
        lesson = _load_current_lesson(session)
    except FileNotFoundError:
        return MISSING_LESSON
    except (OSError, ValueError, json.JSONDecodeError):
        return MISSING_LESSON

    summary = str(lesson.get("summary") or "").strip()
    concepts = lesson.get("concepts") or []
    lines = [summary, "", "Key ideas:"]
    if isinstance(concepts, list):
        for c in concepts[:6]:
            lines.append(f"- {c}")
    return "\n".join(lines) + "\n\n" + main_menu_text()


def _adjust_difficulty(session: dict[str, Any], easier: bool) -> str:
    d = str(session.get("difficulty") or "normal")
    if easier:
        if d == "easy":
            return (
                "You are already on the easiest level.\n\n" + main_menu_text()
            )
        new_d = {"hard": "normal", "normal": "easy"}.get(d, "easy")
    else:
        if d == "hard":
            return (
                "You are already on the hardest level.\n\n" + main_menu_text()
            )
        new_d = {"easy": "normal", "normal": "hard"}.get(d, "hard")

    session["difficulty"] = new_d
    save_session(session)
    return f"Okay — level is now {new_d}.\n\n{main_menu_text()}"


def handle_message(phone: str, text: str) -> str:
    student_id = (phone or "").strip()
    raw = (text or "").strip()
    session = load_session(student_id)

    if session.get("awaiting_answer"):
        return _handle_practice_answer(student_id, session, raw)

    if session.get("awaiting_lesson_selection"):
        return _handle_lesson_pick(student_id, session, raw)

    choice = _parse_menu_choice(raw)
    if choice is None:
        if raw.isdigit():
            return INVALID_MENU + "\n\n" + main_menu_text()
        return "Hi! Reply with a number:\n\n" + main_menu_text()

    if choice == 1:
        return _start_lesson_selection(student_id, session)

    if not _has_lesson(session):
        return NO_LESSON

    if choice == 2:
        return _explain_lesson(session)

    if choice == 3:
        return _start_practice(student_id, session)

    if choice == 4:
        lid = str(session.get("current_lesson_id") or "")
        summary = format_progress_summary(student_id, lid)
        return summary + "\n\n" + main_menu_text()

    if choice == 5:
        return _adjust_difficulty(session, easier=True)

    if choice == 6:
        return _adjust_difficulty(session, easier=False)

    if choice == 7:
        reset_session(student_id)
        return "Thanks for studying. Send any message to open the menu again."

    return INVALID_MENU + "\n\n" + main_menu_text()
