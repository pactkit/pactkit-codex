"""Regression decision tree — classify changed files to decide test scope (STORY-slim-014 R1).

Replaces the prompt-based regression decision from Done Phase 2.5.
"""
from __future__ import annotations

import fnmatch

# Files that match these patterns are considered "doc-only" — safe to skip tests.
_DOC_ONLY_PATTERNS: tuple[str, ...] = (
    "docs/**",
    "tests/**",
    "*.md",
    "README*",
    "*.txt",
)

# Version/dependency manifest files that trigger full regression.
_VERSION_FILES: frozenset[str] = frozenset(
    [
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
    ]
)


def _is_doc_only(path: str) -> bool:
    """Return True if *path* matches any doc-only pattern."""
    # Normalise separators
    norm = path.replace("\\", "/")
    for pattern in _DOC_ONLY_PATTERNS:
        # fnmatch handles * but not ** — handle ** via startswith trick
        if "**" in pattern:
            prefix = pattern.split("**")[0].rstrip("/")
            if norm.startswith(prefix + "/") or norm == prefix:
                return True
        else:
            if fnmatch.fnmatch(norm, pattern) or fnmatch.fnmatch(norm.split("/")[-1], pattern):
                return True
    return False


def _is_version_file(path: str) -> bool:
    """Return True if *path* is a known version/dependency manifest (basename only)."""
    basename = path.replace("\\", "/").rsplit("/", 1)[-1]
    return basename in _VERSION_FILES


def classify_changes(changed_files: list[str]) -> tuple[str, str]:
    """Classify a list of changed file paths and decide the regression strategy.

    Decision tree (in priority order):
        1. Empty list or ALL files are doc-only → ('skip', 'doc-only change')
        2. ANY file is a version/dependency manifest → ('full', 'version/dependency change')
        3. Default → ('impact', 'run mapped tests')

    Args:
        changed_files: List of file paths as returned by ``git diff --name-only``.

    Returns:
        (strategy, reason) where strategy is one of 'skip', 'full', or 'impact'.
    """
    if not changed_files:
        return ("skip", "doc-only change")

    if all(_is_doc_only(f) for f in changed_files):
        return ("skip", "doc-only change")

    if any(_is_version_file(f) for f in changed_files):
        return ("full", "version/dependency change")

    return ("impact", "run mapped tests")
