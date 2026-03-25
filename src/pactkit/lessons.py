"""Lesson auto-append with specificity check and dedup (STORY-slim-017 R1)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from pactkit.schemas import LESSONS_ROW_FORMAT


def _is_specific(text: str) -> bool:
    """Check if text references a concrete file, function, or code pattern."""
    patterns = [
        r"\.\w{2,4}\b",      # file extensions (.py, .ts, .go, .java)
        r"\w+\(\)",           # function calls foo()
        r"\w+/\w+",          # path-like patterns
        r"`[^`]+`",           # inline code
    ]
    return any(re.search(p, text) for p in patterns)


def _jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity on word sets."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _get_last_n_entries(text: str, n: int = 5) -> list[str]:
    """Extract the last N lesson texts from lessons.md content."""
    rows = re.findall(r"\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*(.+?)\s*\|[^|]*\|", text)
    return rows[-n:] if rows else []


def _is_duplicate(text: str, recent_entries: list[str], threshold: float = 0.5) -> bool:
    """Check if text is too similar to any recent entry."""
    for entry in recent_entries:
        if _jaccard_similarity(text, entry) >= threshold:
            return True
    return False


def append_lesson(
    project_root: Path,
    story_id: str,
    text: str,
    context: str = "",
) -> dict:
    """Append a lesson to lessons.md if it passes specificity and dedup checks.

    Returns:
        {"action": "appended"|"skipped", "reason": str}
    """
    lessons_path = project_root / "docs" / "architecture" / "governance" / "lessons.md"

    if not lessons_path.exists():
        return {"action": "skipped", "reason": "lessons.md not found"}

    if not _is_specific(text):
        return {"action": "skipped", "reason": "not specific enough — no file/function reference"}

    content = lessons_path.read_text(encoding="utf-8")
    recent = _get_last_n_entries(content)

    if _is_duplicate(text, recent):
        return {"action": "skipped", "reason": "duplicate of recent entry"}

    today = date.today().isoformat()
    ctx = context if context else story_id
    row = LESSONS_ROW_FORMAT.format(date=today, lesson=text, context=ctx) + "\n"

    with open(lessons_path, "a", encoding="utf-8") as f:
        f.write(row)

    return {"action": "appended", "reason": f"lesson added for {story_id}"}
