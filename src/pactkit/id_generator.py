"""Story ID generator — deterministic next-ID logic (STORY-slim-014 R1).

Replaces the prompt-based ID generation from Plan Phase 3.1.
"""
from __future__ import annotations

import re
from pathlib import Path


def next_story_id(specs_dir: Path, developer: str) -> str:
    """Generate the next Story ID by scanning existing specs.

    Args:
        specs_dir: Path to docs/specs/ directory.
        developer: Developer name from pactkit.yaml (empty = no prefix).

    Returns:
        Next Story ID string, e.g. "STORY-slim-014" or "STORY-001".
    """
    if developer:
        prefix = f"STORY-{developer}-"
        pattern = re.compile(rf"^STORY-{re.escape(developer)}-(\d+)\.md$")
    else:
        prefix = "STORY-"
        pattern = re.compile(r"^STORY-(\d+)\.md$")

    max_num = 0
    if specs_dir.is_dir():
        for f in specs_dir.iterdir():
            m = pattern.match(f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num

    return f"{prefix}{max_num + 1:03d}"
