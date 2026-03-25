"""Spec Status updater — programmatically update Status field in spec files.

STORY-slim-018 R3: Done flow MUST update Spec Status to Done.
"""
from __future__ import annotations

import re
from pathlib import Path

from pactkit.schemas import SPEC_VALID_STATUSES

_STATUS_PATTERN = re.compile(r"(\|\s*Status\s*\|\s*)([^|]+?)(\s*\|)")


def update_spec_status(spec_path: Path, new_status: str) -> dict:
    """Update the Status field in a spec file's metadata table.

    Returns dict with action and details.
    """
    if new_status not in SPEC_VALID_STATUSES:
        return {
            "action": "error",
            "message": f"Invalid status '{new_status}'. Valid: {', '.join(SPEC_VALID_STATUSES)}",
        }

    text = spec_path.read_text(encoding="utf-8")
    match = _STATUS_PATTERN.search(text)
    if not match:
        return {
            "action": "error",
            "message": f"No Status field found in {spec_path}",
        }

    old_status = match.group(2).strip()
    if old_status == new_status:
        return {
            "action": "skipped",
            "message": f"Status already '{new_status}'",
        }

    new_text = _STATUS_PATTERN.sub(rf"\g<1>{new_status} \3", text, count=1)
    # Normalize spacing: collapse multiple spaces before closing pipe
    new_text = re.sub(r"(\| Status \|)\s+(\w[\w ]*\w)\s+(\|)", r"\1 \2 \3", new_text)
    spec_path.write_text(new_text, encoding="utf-8")
    return {
        "action": "updated",
        "old_status": old_status,
        "new_status": new_status,
        "message": f"Updated {spec_path.name}: {old_status} → {new_status}",
    }
