"""Small helpers: answer normalization and safe filenames."""

from __future__ import annotations

import re
from fractions import Fraction


def student_progress_filename(student_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in student_id.strip())
    return f"{safe or 'unknown'}.json"


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _try_parse_number_or_fraction(s: str) -> str | None:
    t = normalize_text(s)
    if not t:
        return None
    # Integer
    if re.fullmatch(r"-?\d+", t):
        return str(int(t))
    # Decimal
    try:
        if "." in t:
            x = float(t)
            if x == int(x):
                return str(int(x))
            return t
    except ValueError:
        pass
    # Fraction a/b
    m = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", t)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == 0:
            return t
        try:
            f = Fraction(a, b)
            return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
        except (ValueError, ZeroDivisionError):
            return t
    return None


def normalize_for_compare(student: str, expected: str) -> tuple[str, str]:
    """Return (normalized_student, normalized_expected) for equality check."""
    exp = normalize_text(expected)
    st = normalize_text(student)

    exp_num = _try_parse_number_or_fraction(exp)
    st_num = _try_parse_number_or_fraction(st)
    if exp_num is not None and st_num is not None:
        return st_num, exp_num

    # Multi-token answers: compare sorted word sets (order-independent).
    exp_parts = exp.split()
    if len(exp_parts) > 1:
        st_parts = st.split()
        st_joined = " ".join(sorted(st_parts))
        exp_joined = " ".join(sorted(exp_parts))
        return st_joined, exp_joined

    # Comma-separated lists (e.g. "Ravi, school" vs "school, Ravi")
    if "," in exp:
        exp_tokens = sorted(normalize_text(x) for x in exp.split(",") if x.strip())
        st_tokens = sorted(normalize_text(x) for x in st.replace(",", " ").split() if x.strip())
        if len(exp_tokens) >= 2:
            return " ".join(st_tokens), " ".join(exp_tokens)

    return st, exp


def answers_match(student: str, expected: str) -> bool:
    a, b = normalize_for_compare(student, expected)
    return a == b
