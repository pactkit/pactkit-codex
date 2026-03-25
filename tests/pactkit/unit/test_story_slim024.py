"""Tests for STORY-slim-024: Spec Lint W007 — Requirement-AC Coverage Check."""

import tempfile

from pactkit.skills.spec_linter import validate_spec


class TestAC1W007FiresOnUnreferencedRN:
    """AC1: W007 fires when R{N} is not referenced by any AC."""

    def test_unreferenced_r3_triggers_w007(self):
        """R3 not referenced in any AC should trigger W007."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-001 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST happen.

### R2: Second requirement
Something SHOULD happen.

### R3: Third requirement
Something MAY happen.

## Acceptance Criteria

### AC1: Test R1
Given a condition
When R1 is tested
Then it passes

### AC2: Test R2
Given another condition
When R2 is verified
Then it works
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 1
        assert "R3" in w007_warnings[0].message


class TestAC2NoW007WhenAllCovered:
    """AC2: No W007 when all R{N} are covered by AC."""

    def test_all_covered_no_w007(self):
        """When every R{N} is referenced, no W007 should be emitted."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-002 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST happen.

### R2: Second requirement
Something SHOULD happen.

## Acceptance Criteria

### AC1: Test R1 and R2
Given a condition
When R1 is tested and R2 is verified
Then both pass
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 0


class TestAC3CaseInsensitiveMatching:
    """AC3: R{N} matching should be case insensitive."""

    def test_lowercase_r1_is_covered(self):
        """'r1' in AC body should count as coverage for R1."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-003 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST happen.

## Acceptance Criteria

### AC1: Test lowercase reference
Given a condition
When r1 is tested (lowercase)
Then it passes
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 0


class TestAC4W007DoesNotBlock:
    """AC4: W007 is a warning, does not cause lint failure."""

    def test_w007_does_not_fail(self):
        """Spec with only W007 should still pass (warnings don't block)."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-004 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST happen.

## Acceptance Criteria

### AC1: Test something else
Given a condition
When something is tested
Then it passes

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | N/A | Test only |
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        # W007 should be emitted (R1 not referenced)
        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 1
        # But result should still pass (warnings don't block)
        assert result.passed is True


class TestAC5RFC2119Emphasis:
    """AC5: W007 message should indicate RFC 2119 keyword in unreferenced req."""

    def test_should_indicator_in_message(self):
        """Uncovered SHOULD requirement should have (SHOULD) in warning message."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-005 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST happen.

### R2: Second requirement
Something SHOULD happen but might be forgotten.

## Acceptance Criteria

### AC1: Test R1 only
Given a condition
When R1 is tested
Then it passes
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 1
        assert "R2" in w007_warnings[0].message
        assert "(SHOULD)" in w007_warnings[0].message

    def test_must_indicator_in_message(self):
        """Uncovered MUST requirement should have (MUST) in warning message."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-006 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: First requirement
Something MUST be implemented.

## Acceptance Criteria

### AC1: Test something else
Given a condition
When something unrelated is tested
Then it passes
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 1
        assert "R1" in w007_warnings[0].message
        assert "(MUST)" in w007_warnings[0].message

    def test_may_indicator_in_message(self):
        """Uncovered MAY requirement should have (MAY) in warning message."""
        spec = """\
| Field | Value |
|-------|-------|
| ID | TEST-007 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |

## Background
Test background.

## Requirements

### R1: Optional feature
Something MAY be implemented optionally.

## Acceptance Criteria

### AC1: Test something else
Given a condition
When something unrelated is tested
Then it passes
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(spec)
            f.flush()
            result = validate_spec(f.name)

        w007_warnings = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007_warnings) == 1
        assert "R1" in w007_warnings[0].message
        assert "(MAY)" in w007_warnings[0].message
