"""Document structure validators — R2 (STORY-slim-014).

Validate document structure against schemas defined in pactkit.schemas.
All three validators follow the same contract:
    - Return an empty list on success.
    - Return a list of human-readable error strings on failure.
"""

from __future__ import annotations

import re
from pathlib import Path

from pactkit.schemas import (
    CONTEXT_HEADER,
    CONTEXT_SECTIONS,
    LESSONS_TABLE_HEADER,
    LESSONS_TABLE_SEPARATOR,
    TEST_CASE_KEYWORDS,
    TEST_CASE_SCENARIO_PATTERN,
)


def lint_context(path: Path) -> list[str]:
    """Validate context.md structure.

    Checks:
    - File exists.
    - CONTEXT_HEADER is present.
    - All CONTEXT_SECTIONS headers are present.

    Returns:
        List of error messages; empty list means the file is valid.
    """
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except OSError as exc:
        return [f"Cannot read file {path}: {exc}"]

    if CONTEXT_HEADER not in content:
        errors.append(f"Missing header: '{CONTEXT_HEADER}'")

    for section in CONTEXT_SECTIONS:
        if section not in content:
            errors.append(f"Missing section: '{section}'")

    return errors


def lint_lessons(path: Path) -> list[str]:
    """Validate lessons.md structure.

    Checks:
    - File exists.
    - LESSONS_TABLE_HEADER is present.
    - LESSONS_TABLE_SEPARATOR is present.

    Returns:
        List of error messages; empty list means the file is valid.
    """
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except OSError as exc:
        return [f"Cannot read file {path}: {exc}"]

    if LESSONS_TABLE_HEADER not in content:
        errors.append(f"Missing table header: '{LESSONS_TABLE_HEADER}'")

    if LESSONS_TABLE_SEPARATOR not in content:
        errors.append(f"Missing table separator: '{LESSONS_TABLE_SEPARATOR}'")

    # Validate row column count (3 columns per LESSONS_ROW_FORMAT)
    lines = content.splitlines()
    in_table = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped == LESSONS_TABLE_SEPARATOR:
            in_table = True
            continue
        if in_table and stripped.startswith("|") and stripped.endswith("|"):
            # A proper 3-col row like "| a | b | c |" splits to ['', ' a ', ' b ', ' c ', '']
            col_count = len(stripped.split("|")) - 2  # subtract leading/trailing empty
            if col_count != 3:
                errors.append(
                    f"Line {i}: expected 3 columns but found {col_count}"
                )
        elif in_table and not stripped.startswith("|"):
            # End of table
            break

    return errors


def lint_testcase(path: Path) -> list[str]:
    """Validate test case file structure.

    Checks:
    - File exists.
    - At least one match for TEST_CASE_SCENARIO_PATTERN (e.g. '## TC-01:').
    - All TEST_CASE_KEYWORDS are present (e.g. '**Given**', '**When**', '**Then**').

    Returns:
        List of error messages; empty list means the file is valid.
    """
    errors: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"File not found: {path}"]
    except OSError as exc:
        return [f"Cannot read file {path}: {exc}"]

    if not re.search(TEST_CASE_SCENARIO_PATTERN, content):
        errors.append(
            f"No scenario headings found. Expected pattern matching '{TEST_CASE_SCENARIO_PATTERN}' "
            "(e.g. '## TC-01: ...')"
        )

    for keyword in TEST_CASE_KEYWORDS:
        if keyword not in content:
            errors.append(f"Missing keyword: '{keyword}'")

    return errors
