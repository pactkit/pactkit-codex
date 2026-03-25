"""Document structure schemas — single source of truth for all PactKit document formats.

All document creation/parsing/validation code MUST reference constants from this module.
Do NOT hardcode section headers, field names, or format patterns elsewhere.

When modifying a schema:
    1. Update the constant in this file
    2. All consumers auto-pick up the change (spec_linter, board.py, scaffold, playbooks)
    3. Run full test suite to verify consistency

When adding a new document type:
    1. Add a clearly-separated section below (use the ─── separator style)
    2. Define all structural constants (headers, patterns, formats)
    3. Add the type to the SCHEMA_REGISTRY at the bottom
"""

# ─── Spec Schema ────────────────────────────────────────────────────────────

SPEC_REQUIRED_METADATA_FIELDS = ("ID", "Status", "Priority", "Release")

SPEC_REQUIRED_SECTIONS = ("## Requirements", "## Acceptance Criteria", "## Security Scope")

SPEC_OPTIONAL_SECTIONS = (
    "## Background",
    "## Target Call Chain",
    "## Implementation Steps",
    "## Out of Scope",
    "## Non-Goals",
)

# E004: requirement subsection pattern
SPEC_REQUIREMENT_PATTERN = r"### R\d+[:\s]"

# E006: acceptance criteria subsection pattern
SPEC_AC_PATTERN = r"### AC\d+[:\s]|### Scenario\s+\d+[:\s]"

# E007: Given/When/Then keywords (stored as-is; linter lowercases for matching)
SPEC_GIVEN_WHEN_THEN = ("Given", "When", "Then")

# W003: RFC 2119 keywords for requirement strength
SPEC_RFC_KEYWORDS = ("MUST", "SHOULD", "MAY", "SHALL", "REQUIRED", "RECOMMENDED", "OPTIONAL")

# Compiled RFC2119 pattern (for use in spec_linter)
import re as _re  # noqa: E402

SPEC_RFC_PATTERN = _re.compile(r"\b(" + "|".join(SPEC_RFC_KEYWORDS) + r")\b")

# E009: Security Scope section name and SEC-* entry pattern
SPEC_SECURITY_SCOPE_SECTION = "Security Scope"
SPEC_SEC_PATTERN = r"\|\s*SEC-"

# ─── Spec Template ──────────────────────────────────────────────────────────
# Used by scaffold.py create_spec(). Must be consistent with spec_linter rules.
# IMPORTANT: scaffold.py (deployed as standalone script) inlines a copy of this
# template. When updating here, also update src/pactkit/skills/scaffold.py.

SPEC_TEMPLATE = """\
# {id}: {title}

| Field | Value |
|-------|-------|
| ID | {id} |
| Status | Draft |
| Priority | P1 |
| Release | TBD |

## Background

(Description of the problem or feature)

## Requirements

### R1: (Requirement Name) (MUST)

(Description)

## Acceptance Criteria

### AC1: (Scenario Name) (R1)

- **Given** (precondition)
- **When** (action)
- **Then** (expected result)

## Target Call Chain

(Trace call chain here)

## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|-------------|------|
| 1 | `src/example.py` | (Description) | None | Low |

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | N/A | (Reason) |

## Out of Scope

- (Items explicitly excluded)
"""

# ─── Spec Status Values ──────────────────────────────────────────────────────

SPEC_VALID_STATUSES = ("Draft", "In Progress", "Done")

# ─── LANG_PROFILES Key Schema ───────────────────────────────────────────────
# Canonical key set for LANG_PROFILES entries in workflows.py.
# All test files MUST import this instead of hardcoding their own key lists.

LANG_PROFILE_REQUIRED_KEYS = frozenset({
    "test_runner",
    "file_ext",
    "source_dirs",
    "test_map_pattern",
    "lint_command",
})

# ─── Sprint Board Schema ─────────────────────────────────────────────────────
# board.py (deployed as standalone skill script) maintains inline copies of these
# constants. When updating here, also update src/pactkit/skills/board.py.

BOARD_SECTION_BACKLOG = "## 📋 Backlog"
BOARD_SECTION_IN_PROGRESS = "## 🔄 In Progress"
BOARD_SECTION_DONE = "## ✅ Done"
BOARD_SECTIONS = (BOARD_SECTION_BACKLOG, BOARD_SECTION_IN_PROGRESS, BOARD_SECTION_DONE)

BOARD_TASK_UNCHECKED = "- [ ] "
BOARD_TASK_CHECKED = "- [x] "

# Story entry format: "- **STORY-slim-007**: Title [P1]"
BOARD_STORY_PREFIX = "- **"

# ─── context.md Schema ───────────────────────────────────────────────────────
# Canonical format for docs/product/context.md.
# Used by _render_prompt() via {CONTEXT_SECTIONS} template variable.
# Every /project-* command that writes context.md MUST use these sections.

CONTEXT_HEADER = "# Project Context (Auto-generated)"

CONTEXT_SECTIONS = (
    "## Sprint Status",
    "## Current Stories",
    "## Recent Completions",
    "## Active Branches",
    "## Key Decisions",
    "## Next Recommended Action",
)

# Rendered section list for use in playbook templates ({CONTEXT_SECTIONS} variable)
CONTEXT_SECTIONS_TEXT = "\n".join(f"- `{s}`" for s in CONTEXT_SECTIONS)

# ─── lessons.md Schema ───────────────────────────────────────────────────────

LESSONS_TABLE_HEADER = "| Date | Lesson | Context |"
LESSONS_TABLE_SEPARATOR = "|------|--------|---------|"
LESSONS_ROW_FORMAT = "| {date} | {lesson} | {context} |"

# ─── Test Case Schema ─────────────────────────────────────────────────────────

TEST_CASE_TITLE_FORMAT = "# Test Cases: {id} — {description}"
TEST_CASE_SCENARIO_PATTERN = r"## TC-\d+[:\s]"
TEST_CASE_KEYWORDS = ("**Given**", "**When**", "**Then**")

# File naming: docs/test_cases/{ID}_case.md
TEST_CASE_FILE_PATTERN = "{id}_case.md"

# ─── Schema Registry ─────────────────────────────────────────────────────────
# Used by `pactkit schema` CLI command for discovery.

SCHEMA_REGISTRY = {
    "spec": {
        "description": "Feature specification / bug report",
        "required_metadata": SPEC_REQUIRED_METADATA_FIELDS,
        "required_sections": SPEC_REQUIRED_SECTIONS,
        "optional_sections": SPEC_OPTIONAL_SECTIONS,
        "patterns": {
            "requirement": SPEC_REQUIREMENT_PATTERN,
            "acceptance_criteria": SPEC_AC_PATTERN,
        },
        "keywords": {
            "rfc2119": SPEC_RFC_KEYWORDS,
            "given_when_then": SPEC_GIVEN_WHEN_THEN,
        },
    },
    "board": {
        "description": "Sprint board (docs/product/sprint_board.md)",
        "sections": BOARD_SECTIONS,
        "task_unchecked": BOARD_TASK_UNCHECKED,
        "task_checked": BOARD_TASK_CHECKED,
    },
    "context": {
        "description": "Session context (docs/product/context.md)",
        "header": CONTEXT_HEADER,
        "sections": CONTEXT_SECTIONS,
    },
    "lessons": {
        "description": "Lessons learned (docs/architecture/governance/lessons.md)",
        "table_header": LESSONS_TABLE_HEADER,
        "row_format": LESSONS_ROW_FORMAT,
    },
    "testcase": {
        "description": "Test cases (docs/test_cases/{ID}_case.md)",
        "title_format": TEST_CASE_TITLE_FORMAT,
        "keywords": TEST_CASE_KEYWORDS,
    },
}
