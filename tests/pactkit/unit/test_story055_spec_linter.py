"""
STORY-055: PDCA Quality Gates Enhancement — Spec Linter W005 tests

Verify:
- R1.5: If '## Implementation Steps' section exists, validate table format
- W005 is NOT emitted when section is absent
- W005 is NOT emitted when section has a valid pipe-table
- W005 IS emitted when section exists but has no table
"""
from pathlib import Path

from pactkit.skills.spec_linter import validate_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_SPEC = """\
# STORY-055: Some Title

| Field     | Value |
|-----------|-------|
| ID        | STORY-055 |
| Status    | Draft |
| Priority  | P1 |
| Release   | 1.4.0 |

## Background

Some background.

## Target Call Chain

Some chain.

## Requirements

### R1: Some requirement

This MUST be satisfied.

## Acceptance Criteria

### AC1: Happy Path (R1)
**Given** a valid input
**When** R1 action is taken
**Then** the result is correct

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | N/A | Test only |

## Out of Scope

Not in scope.
"""

_IMPL_STEPS_VALID = """
## Implementation Steps

| Step | File | Action | Dependencies | Risk |
|------|------|--------|--------------|------|
| 1 | `src/foo.py` | Add feature | None | Low |
| 2 | `tests/test_foo.py` | Add tests | Step 1 | Low |
"""

_IMPL_STEPS_NO_TABLE = """
## Implementation Steps

1. Add a feature to foo.py
2. Add tests for the feature
"""


def _write_spec(tmp_path: Path, extra: str = "") -> Path:
    p = tmp_path / "TEST-055.md"
    p.write_text(_BASE_SPEC + extra, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# W005: Implementation Steps table format validation
# ---------------------------------------------------------------------------

class TestImplementationStepsLintRule:
    """W005: WARN if Implementation Steps section exists but has no pipe table."""

    def test_no_warn_when_impl_steps_absent(self, tmp_path):
        """W005 must NOT fire when ## Implementation Steps is absent."""
        spec_file = _write_spec(tmp_path, extra="")
        result = validate_spec(str(spec_file))
        w005_warns = [w for w in result.warnings if w.rule_id == "W005"]
        assert len(w005_warns) == 0, \
            "W005 must not warn when Implementation Steps section is absent"

    def test_no_warn_when_impl_steps_has_valid_table(self, tmp_path):
        """W005 must NOT fire when Implementation Steps has a valid pipe table."""
        spec_file = _write_spec(tmp_path, extra=_IMPL_STEPS_VALID)
        result = validate_spec(str(spec_file))
        w005_warns = [w for w in result.warnings if w.rule_id == "W005"]
        assert len(w005_warns) == 0, \
            "W005 must not warn when Implementation Steps has a valid pipe table"

    def test_warn_when_impl_steps_has_no_table(self, tmp_path):
        """W005 MUST fire when Implementation Steps section exists but has no table."""
        spec_file = _write_spec(tmp_path, extra=_IMPL_STEPS_NO_TABLE)
        result = validate_spec(str(spec_file))
        w005_warns = [w for w in result.warnings if w.rule_id == "W005"]
        assert len(w005_warns) >= 1, \
            "W005 must warn when Implementation Steps exists but has no pipe table"

    def test_warn_message_mentions_table_format(self, tmp_path):
        """W005 warning message should mention table format."""
        spec_file = _write_spec(tmp_path, extra=_IMPL_STEPS_NO_TABLE)
        result = validate_spec(str(spec_file))
        w005_warns = [w for w in result.warnings if w.rule_id == "W005"]
        assert len(w005_warns) >= 1
        msg = w005_warns[0].message.lower()
        assert 'table' in msg or 'step' in msg, \
            f"W005 message should mention table format, got: {w005_warns[0].message}"

    def test_spec_still_passes_with_impl_steps_valid_table(self, tmp_path):
        """Spec with valid Implementation Steps must still pass linting."""
        spec_file = _write_spec(tmp_path, extra=_IMPL_STEPS_VALID)
        result = validate_spec(str(spec_file))
        assert result.passed, \
            "Spec with valid Implementation Steps should pass lint"

    def test_spec_still_passes_with_impl_steps_no_table(self, tmp_path):
        """W005 is a WARN (not ERROR) — spec must still pass even without table."""
        spec_file = _write_spec(tmp_path, extra=_IMPL_STEPS_NO_TABLE)
        result = validate_spec(str(spec_file))
        assert result.passed, \
            "W005 is WARN-only — spec must still pass lint even with missing table"
