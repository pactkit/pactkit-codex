#!/usr/bin/env python3
"""Spec Linter — Non-AI structural validation gate for PactKit specs.

Usage (standalone):
    python3 src/pactkit/skills/spec_linter.py docs/specs/STORY-042.md
    python3 src/pactkit/skills/spec_linter.py --all
    python3 src/pactkit/skills/spec_linter.py --all --specs-dir path/to/specs
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Import schema constants (STORY-slim-007: single source of truth)
try:
    from pactkit.schemas import (
        SPEC_AC_PATTERN,
        SPEC_GIVEN_WHEN_THEN,
        SPEC_REQUIRED_METADATA_FIELDS,
        SPEC_REQUIRED_SECTIONS,
        SPEC_REQUIREMENT_PATTERN,
        SPEC_RFC_KEYWORDS,
        SPEC_RFC_PATTERN,
        SPEC_SEC_PATTERN,
        SPEC_SECURITY_SCOPE_SECTION,
        SPEC_VALID_STATUSES,
    )
except ImportError:
    # Fallback for standalone execution without pactkit installed
    # Keep in sync with src/pactkit/schemas.py
    SPEC_REQUIRED_METADATA_FIELDS = ("ID", "Status", "Priority", "Release")
    SPEC_REQUIRED_SECTIONS = ("## Requirements", "## Acceptance Criteria", "## Security Scope")
    SPEC_REQUIREMENT_PATTERN = r"### R\d+[:\s]"
    SPEC_AC_PATTERN = r"### AC\d+[:\s]|### Scenario\s+\d+[:\s]"
    SPEC_GIVEN_WHEN_THEN = ("Given", "When", "Then")
    SPEC_RFC_KEYWORDS = ("MUST", "SHOULD", "MAY", "SHALL", "REQUIRED", "RECOMMENDED", "OPTIONAL")
    SPEC_RFC_PATTERN = re.compile(r"\b(" + "|".join(SPEC_RFC_KEYWORDS) + r")\b")
    SPEC_VALID_STATUSES = ("Draft", "In Progress", "Done")
    SPEC_SECURITY_SCOPE_SECTION = "Security Scope"
    SPEC_SEC_PATTERN = r"\|\s*SEC-"

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class LintIssue:
    rule_id: str
    message: str
    line: int | None = None


@dataclass
class LintResult:
    errors: list[LintIssue] = field(default_factory=list)
    warnings: list[LintIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_RFC2119 = SPEC_RFC_PATTERN
_METADATA_ROW = re.compile(r"^\|\s*(\w[\w\s]*\w|\w)\s*\|\s*(.+?)\s*\|", re.MULTILINE)
_METADATA_HEADER = re.compile(r"^\|\s*Field\s*\|\s*Value\s*\|", re.MULTILINE | re.IGNORECASE)
_REQ_SUBSECTION = re.compile(SPEC_REQUIREMENT_PATTERN, re.MULTILINE)
_AC_SUBSECTION = re.compile(SPEC_AC_PATTERN, re.MULTILINE | re.IGNORECASE)


_FENCED_BLOCK = re.compile(r"^```[^\n]*\n.*?^```", re.MULTILINE | re.DOTALL)


def _strip_code_blocks(text: str) -> str:
    """Replace fenced code block content with blank lines (preserving line count)."""

    def _blank(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")

    return _FENCED_BLOCK.sub(_blank, text)


def _find_section(text: str, heading: str) -> tuple[int, int] | None:
    """Return (start_idx, end_idx) of a ## heading block, or None if absent.

    ``text`` should already have code blocks stripped via ``_strip_code_blocks``
    so that headings inside examples don't confuse parsing.
    """
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE | re.IGNORECASE)
    m = pattern.search(text)
    if not m:
        return None
    start = m.start()
    next_h2 = re.search(r"^##\s+", text[m.end() :], re.MULTILINE)
    end = m.end() + next_h2.start() if next_h2 else len(text)
    return start, end


def _section_text(text: str, heading: str) -> str | None:
    """Return the body text of a ## heading block, or None if absent.

    ``text`` should already have code blocks stripped.
    """
    bounds = _find_section(text, heading)
    if bounds is None:
        return None
    return text[bounds[0] : bounds[1]]


def _line_number(text: str, idx: int) -> int:
    return text[:idx].count("\n") + 1


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------


def _check_metadata(text: str, result: LintResult) -> dict[str, str]:
    """E001, E002, E008 — metadata table structure and required fields."""
    fields: dict[str, str] = {}

    # E001: metadata table must exist (Field | Value header)
    if not _METADATA_HEADER.search(text):
        result.errors.append(LintIssue("E001", "Missing metadata table (| Field | Value | header not found)"))
        return fields

    # Parse all metadata rows
    for m in _METADATA_ROW.finditer(text):
        key = m.group(1).strip()
        val = m.group(2).strip()
        if key.lower() not in ("field", "-"):
            fields[key] = val

    # E002: required fields must be present and non-empty (from schemas.SPEC_REQUIRED_METADATA_FIELDS)
    for req in SPEC_REQUIRED_METADATA_FIELDS:
        if req not in fields or not fields[req]:
            result.errors.append(LintIssue("E002", f"Missing or empty required metadata field: {req}"))

    # E008: Release must not be TBD
    if fields.get("Release", "").upper() == "TBD":
        result.errors.append(LintIssue("E008", "Release field is 'TBD' — must be a concrete version before Act"))

    # W006: Status value must be in SPEC_VALID_STATUSES (STORY-slim-018 R3)
    status_val = fields.get("Status", "")
    if status_val and status_val not in SPEC_VALID_STATUSES:
        result.warnings.append(
            LintIssue("W006", f"Status value '{status_val}' not in allowed set: {', '.join(SPEC_VALID_STATUSES)}")
        )

    return fields


def _check_requirements_section(text: str, result: LintResult) -> None:
    """E003, E004, W003 — Requirements section."""
    body = _section_text(text, "Requirements")

    # E003: section must exist
    if body is None:
        result.errors.append(LintIssue("E003", "Missing '## Requirements' section"))
        return

    # E004: must contain at least one ### R{N}: subsection
    if not _REQ_SUBSECTION.search(body):
        result.errors.append(LintIssue("E004", "Requirements section has no '### R{N}:' subsections"))

    # W003: requirements should use RFC 2119 keywords
    if not _RFC2119.search(body):
        result.warnings.append(LintIssue("W003", "No RFC 2119 keywords (MUST/SHOULD/MAY) found in Requirements"))


def _check_acceptance_criteria(text: str, result: LintResult, raw_text: str | None = None) -> None:
    """E005, E006, E007 — Acceptance Criteria section."""
    body = _section_text(text, "Acceptance Criteria")

    # E005: section must exist
    if body is None:
        result.errors.append(LintIssue("E005", "Missing '## Acceptance Criteria' section"))
        return

    # E006: must contain at least one ### AC{N}: or ### Scenario {N}: subsection
    if not _AC_SUBSECTION.search(body):
        result.errors.append(
            LintIssue("E006", "Acceptance Criteria has no '### AC{N}:' or '### Scenario {N}:' subsections")
        )
        return

    # E007: each AC subsection must contain Given, When, Then keywords (per-subsection check)
    # Use raw_text (with code blocks) for GWT search — specs may wrap Gherkin in ```gherkin fences
    raw_body = (_section_text(raw_text, "Acceptance Criteria") if raw_text else None) or body
    ac_matches = list(_AC_SUBSECTION.finditer(body))
    raw_ac_matches = list(_AC_SUBSECTION.finditer(raw_body)) if raw_body != body else ac_matches
    for i, m in enumerate(ac_matches):
        # Extract AC ID from the heading (e.g., "AC1" or "Scenario 1")
        ac_heading = m.group(0).strip()
        ac_id_match = re.search(r"(AC\d+|Scenario\s+\d+)", ac_heading, re.IGNORECASE)
        ac_id = ac_id_match.group(0) if ac_id_match else ac_heading
        # Get subsection text from raw (preserves code block content for GWT search)
        if i < len(raw_ac_matches):
            raw_start = raw_ac_matches[i].end()
            raw_end = raw_ac_matches[i + 1].start() if i + 1 < len(raw_ac_matches) else len(raw_body)
            subsection_lower = raw_body[raw_start:raw_end].lower()
        else:
            start = m.end()
            end = ac_matches[i + 1].start() if i + 1 < len(ac_matches) else len(body)
            subsection_lower = body[start:end].lower()
        # Word-boundary match to prevent "whenever" matching "when"
        missing = [kw for kw in SPEC_GIVEN_WHEN_THEN if not re.search(r"\b" + kw.lower() + r"\b", subsection_lower)]
        if missing:
            result.errors.append(LintIssue("E007", f"{ac_id} missing keyword(s): {', '.join(missing).upper()}"))


_PIPE_TABLE_ROW = re.compile(r"^\|.+\|.+\|", re.MULTILINE)

# STORY-slim-024: R{N} ID extraction pattern
# Uses \s+ instead of SPEC_REQUIREMENT_PATTERN's literal space to tolerate minor
# whitespace variations in hand-written specs (e.g., tab or double-space after ###).
# Adds capture group (R\d+) for ID extraction — SPEC_REQUIREMENT_PATTERN is match-only.
_REQ_ID_PATTERN = re.compile(r"###\s+(R\d+)[:\s]", re.MULTILINE)


def _extract_requirement_ids(req_section: str) -> dict[str, str]:
    """Extract R{N} IDs and their body text from Requirements section.

    Returns dict mapping R{N} (e.g., "R1") to the requirement body text.
    """
    result: dict[str, str] = {}
    # Find all ### R{N}: headers
    matches = list(_REQ_ID_PATTERN.finditer(req_section))
    for i, m in enumerate(matches):
        req_id = m.group(1).upper()  # Normalize to uppercase (R1, R2, etc.)
        # Body is from end of this header to start of next (or end of section)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(req_section)
        body = req_section[start:end].strip()
        result[req_id] = body
    return result


def _check_req_ac_coverage(text: str, result: LintResult) -> None:
    """W007 — Check that all R{N} are referenced by at least one AC."""
    req_section = _section_text(text, "Requirements")
    ac_section = _section_text(text, "Acceptance Criteria")

    if req_section is None or ac_section is None:
        return  # Missing sections are handled by E003/E005

    # Extract all R{N} IDs and their bodies
    req_map = _extract_requirement_ids(req_section)
    if not req_map:
        return  # No requirements found (handled by E004)

    # Check each R{N} for coverage in AC section (word-boundary match)
    for req_id, req_body in req_map.items():
        # STORY-slim-025 R4: use \b word boundary to prevent R1 matching R10/CR1/ERROR1
        if not re.search(rf"\b{re.escape(req_id)}\b", ac_section, re.IGNORECASE):
            # STORY-slim-025 R5: use SPEC_RFC_PATTERN (same as W003) for word-boundary keyword match
            rfc_match = _RFC2119.search(req_body)
            emphasis = f" ({rfc_match.group(0)})" if rfc_match else ""
            result.warnings.append(
                LintIssue("W007", f"Requirement {req_id} has no corresponding AC reference{emphasis}")
            )


def _check_implementation_steps(text: str, result: LintResult) -> None:
    """W005 — Implementation Steps table format validation (STORY-055)."""
    section = _section_text(text, "Implementation Steps")
    if section is None:
        return  # section absent — no warning
    if not _PIPE_TABLE_ROW.search(section):
        result.warnings.append(
            LintIssue(
                "W005",
                "## Implementation Steps exists but has no pipe table "
                "(expected columns: Step, File, Action, Dependencies, Risk)",
            )
        )


# Canonical: src/pactkit/schemas.py SPEC_TEMPLATE
_SCAFFOLD_PLACEHOLDERS = {
    "Background": "(Description of the problem or feature)",
    "Target Call Chain": "(Trace call chain here)",
}


def _check_optional_sections(text: str, result: LintResult) -> None:
    """W001, W002, W004, W008 — recommended sections and placeholder detection."""
    bg = _section_text(text, "Background")
    if bg is None:
        result.warnings.append(LintIssue("W001", "Missing '## Background' section (recommended)"))
    elif _SCAFFOLD_PLACEHOLDERS["Background"] in bg:
        result.warnings.append(LintIssue("W008", "## Background still contains scaffold placeholder text"))

    tcc = _section_text(text, "Target Call Chain")
    if tcc is None:
        result.warnings.append(LintIssue("W002", "Missing '## Target Call Chain' section (recommended)"))
    elif _SCAFFOLD_PLACEHOLDERS["Target Call Chain"] in tcc:
        result.warnings.append(LintIssue("W008", "## Target Call Chain still contains scaffold placeholder text"))

    has_out_of_scope = _section_text(text, "Out of Scope") is not None or _section_text(text, "Non-Goals") is not None
    if not has_out_of_scope:
        result.warnings.append(LintIssue("W004", "Missing '## Out of Scope' or '## Non-Goals' section (recommended)"))


_SEC_ROW = re.compile(SPEC_SEC_PATTERN, re.MULTILINE)


def _check_security_scope(text: str, result: LintResult) -> None:
    """E009 — Security Scope section must exist with SEC-* entries."""
    body = _section_text(text, SPEC_SECURITY_SCOPE_SECTION)
    if body is None:
        result.errors.append(LintIssue("E009", f"Missing '## {SPEC_SECURITY_SCOPE_SECTION}' section"))
        return
    if not _SEC_ROW.search(body):
        result.errors.append(LintIssue("E009", f"{SPEC_SECURITY_SCOPE_SECTION} section has no SEC-* entries"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_spec(spec_path: str) -> LintResult:
    """Validate a spec file and return a LintResult.

    Parameters
    ----------
    spec_path:
        Path to the spec Markdown file.

    Returns
    -------
    LintResult
        ``.passed`` is ``True`` iff there are zero ERROR-level issues.
    """
    raw = Path(spec_path).read_text(encoding="utf-8")
    # Strip fenced code blocks once so all checks operate on the same clean text.
    # This prevents headings inside code examples from confusing section detection.
    text = _strip_code_blocks(raw)
    result = LintResult()
    _check_metadata(text, result)
    _check_requirements_section(text, result)
    _check_acceptance_criteria(text, result, raw_text=raw)
    _check_optional_sections(text, result)
    _check_implementation_steps(text, result)
    _check_req_ac_coverage(text, result)  # STORY-slim-024: W007
    _check_security_scope(text, result)  # STORY-slim-025: E009
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_result(path: str, result: LintResult) -> str:
    lines = [path]
    for e in result.errors:
        loc = f" (line {e.line})" if e.line else ""
        lines.append(f"  [ERROR] {e.rule_id}: {e.message}{loc}")
    for w in result.warnings:
        loc = f" (line {w.line})" if w.line else ""
        lines.append(f"  [WARN]  {w.rule_id}: {w.message}{loc}")
    status = "PASS" if result.passed else f"FAIL ({len(result.errors)} error(s), {len(result.warnings)} warning(s))"
    lines.append(f"  Result: {status}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PactKit Spec Linter — structural validation for spec files")
    parser.add_argument("spec", nargs="?", help="Path to spec file to validate")
    parser.add_argument("--all", action="store_true", help="Validate all specs in specs dir")
    parser.add_argument(
        "--specs-dir",
        default="docs/specs",
        help="Directory containing spec files (default: docs/specs)",
    )
    args = parser.parse_args(argv)

    if args.all:
        specs_dir = Path(args.specs_dir)
        if not specs_dir.exists():
            print(f"Error: specs directory '{specs_dir}' not found", file=sys.stderr)
            return 1
        spec_files = sorted(specs_dir.glob("*.md"))
        if not spec_files:
            print(f"No .md files found in '{specs_dir}'")
            return 0
        any_failure = False
        for spec_file in spec_files:
            result = validate_spec(str(spec_file))
            print(_format_result(str(spec_file), result))
            if not result.passed:
                any_failure = True
        return 1 if any_failure else 0

    if not args.spec:
        parser.print_help()
        return 1

    result = validate_spec(args.spec)
    print(_format_result(args.spec, result))
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
