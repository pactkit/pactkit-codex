"""Invariants refresh — test count update in rules.md (STORY-slim-017 R2)."""

from __future__ import annotations

import re
from pathlib import Path

_PATTERN = re.compile(r"All (\d+)\+ tests must pass")


def refresh_test_count(project_root: Path, test_count: int) -> dict:
    """Update the test count invariant in rules.md.

    Returns:
        {"action": "updated"|"skipped"|"not_found", "old_count": int, "new_count": int}
    """
    rules_path = project_root / "docs" / "architecture" / "governance" / "rules.md"

    if not rules_path.exists():
        return {"action": "not_found", "old_count": 0, "new_count": test_count}

    content = rules_path.read_text(encoding="utf-8")
    match = _PATTERN.search(content)

    if not match:
        return {"action": "not_found", "old_count": 0, "new_count": test_count}

    old_count = int(match.group(1))

    if old_count == test_count:
        return {"action": "skipped", "old_count": old_count, "new_count": test_count}

    new_content = _PATTERN.sub(f"All {test_count}+ tests must pass", content)
    rules_path.write_text(new_content, encoding="utf-8")

    return {"action": "updated", "old_count": old_count, "new_count": test_count}
