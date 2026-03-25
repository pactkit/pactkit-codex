"""Artifact cleaner — remove language-specific temp files (STORY-slim-014 R1).

Replaces the prompt-based cleanup from Done Phase 2.
"""
from __future__ import annotations

import shutil
from pathlib import Path

# Cleanup patterns per stack (canonical source: prompts/workflows.py LANG_PROFILES)
_CLEANUP_PATTERNS: dict[str, list[str]] = {
    "python": ["__pycache__", ".pytest_cache", "*.pyc"],
    "node": ["node_modules/.cache", ".next", "dist", "coverage"],
    "go": ["cover.out", "cover.html"],
    "java": ["target/", "build/", ".gradle/"],
}

# Stack detection markers (ordered by priority)
_STACK_MARKERS: list[tuple[str, str]] = [
    ("pyproject.toml", "python"),
    ("setup.py", "python"),
    ("setup.cfg", "python"),
    ("package.json", "node"),
    ("go.mod", "go"),
    ("pom.xml", "java"),
    ("build.gradle", "java"),
]


def detect_stack(project_root: Path) -> str:
    """Detect project stack from marker files.

    Returns stack name ('python', 'node', 'go', 'java').
    Defaults to 'python' if no markers found.
    """
    for marker_file, stack in _STACK_MARKERS:
        if (project_root / marker_file).exists():
            return stack
    return "python"


def clean_artifacts(
    project_root: Path,
    stack: str = "auto",
    dry_run: bool = False,
) -> list[Path]:
    """Remove language-specific temp artifacts.

    Args:
        project_root: Project root directory.
        stack: Language stack ('python', 'node', 'go', 'java', 'auto').
        dry_run: If True, list files without deleting.

    Returns:
        List of removed (or would-be-removed) paths.
    """
    if stack == "auto":
        stack = detect_stack(project_root)

    patterns = _CLEANUP_PATTERNS.get(stack, [])
    removed: list[Path] = []

    for pattern in patterns:
        if "*" in pattern:
            # Glob pattern (e.g., "*.pyc")
            for match in project_root.rglob(pattern):
                removed.append(match)
                if not dry_run:
                    if match.is_dir():
                        shutil.rmtree(match)
                    else:
                        match.unlink()
        else:
            # Directory or file name (e.g., "__pycache__", ".pytest_cache")
            clean_name = pattern.rstrip("/")
            for match in project_root.rglob(clean_name):
                removed.append(match)
                if not dry_run:
                    if match.is_dir():
                        shutil.rmtree(match)
                    else:
                        match.unlink()

    return removed
