"""Spec release backfill — replace TBD with actual version (STORY-slim-015 R4).

Replaces the prompt-based backfill from SKILL_RELEASE_MD.
"""
from __future__ import annotations

import re
from pathlib import Path

from pactkit.schemas import BOARD_SECTION_DONE

_ITEM_ID_RE = re.compile(r"((?:STORY|BUG|HOTFIX)(?:-[\w]+)?-\d+)")
_TBD_RE = re.compile(r"\|\s*Release\s*\|\s*TBD\s*\|")


def _get_done_ids(project_root: Path) -> set[str]:
    """Collect IDs of done stories from board Done section + archive."""
    done_ids: set[str] = set()

    board_path = project_root / "docs" / "product" / "sprint_board.md"
    if board_path.exists():
        text = board_path.read_text(encoding="utf-8")
        # Find the Done section
        done_match = re.search(re.escape(BOARD_SECTION_DONE) + r"\b", text)
        if done_match:
            done_section = text[done_match.start():]
            done_ids.update(_ITEM_ID_RE.findall(done_section))

    archive_dir = project_root / "docs" / "product" / "archive"
    if archive_dir.is_dir():
        for f in archive_dir.iterdir():
            if f.suffix == ".md":
                done_ids.update(_ITEM_ID_RE.findall(f.read_text(encoding="utf-8")))

    return done_ids


def scan_and_replace_tbd(project_root: Path, version: str) -> dict:
    """Scan specs for Release: TBD and replace for done stories.

    Returns:
        {"backfilled": [{"id": ..., "file": ...}], "skipped": [{"id": ..., "reason": ...}]}
    """
    specs_dir = project_root / "docs" / "specs"
    if not specs_dir.is_dir():
        return {"backfilled": [], "skipped": []}

    done_ids = _get_done_ids(project_root)

    backfilled: list[dict] = []
    skipped: list[dict] = []

    for spec_file in sorted(specs_dir.glob("*.md")):
        content = spec_file.read_text(encoding="utf-8")

        if not _TBD_RE.search(content):
            continue  # No TBD → skip silently

        # Extract ID from filename
        m = _ITEM_ID_RE.match(spec_file.stem)
        if not m:
            continue
        spec_id = m.group(1)

        if spec_id in done_ids:
            new_content = _TBD_RE.sub(f"| Release | {version} |", content)
            spec_file.write_text(new_content, encoding="utf-8")
            backfilled.append({"id": spec_id, "file": str(spec_file.name)})
        else:
            skipped.append({"id": spec_id, "reason": "not done"})

    return {"backfilled": backfilled, "skipped": skipped}
