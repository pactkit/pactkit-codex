"""Tests for STORY-042: Spec Linter — Non-AI Structural Validation Gate."""
import subprocess
import sys
from pathlib import Path

from pactkit.skills.spec_linter import LintIssue, LintResult, validate_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_SPEC = """\
# STORY-042: Some Title

| Field     | Value |
|-----------|-------|
| ID        | STORY-042 |
| Status    | Draft |
| Priority  | High |
| Release   | 1.4.0 |

## Background

Some background text.

## Target Call Chain

Some call chain.

## Requirements

### R1: First Requirement (MUST)

This requirement MUST be satisfied.

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

- Not in scope.
"""


def write_spec(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "TEST-001.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# LintResult / LintIssue dataclass sanity
# ---------------------------------------------------------------------------

class TestDataclasses:
    def test_lint_result_passed_when_no_errors(self):
        result = LintResult(errors=[], warnings=[])
        assert result.passed is True

    def test_lint_result_failed_when_errors(self):
        issue = LintIssue(rule_id="E001", message="Missing metadata table", line=None)
        result = LintResult(errors=[issue], warnings=[])
        assert result.passed is False

    def test_lint_issue_fields(self):
        issue = LintIssue(rule_id="W001", message="Missing background", line=3)
        assert issue.rule_id == "W001"
        assert issue.message == "Missing background"
        assert issue.line == 3


# ---------------------------------------------------------------------------
# E001 – Metadata table exists
# ---------------------------------------------------------------------------

class TestE001MetadataTable:
    def test_missing_metadata_table_raises_E001(self, tmp_path):
        spec = write_spec(tmp_path, "# STORY-001: Title\n\nSome text.\n")
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E001" in ids

    def test_valid_metadata_table_no_E001(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E001" not in ids


# ---------------------------------------------------------------------------
# E002 – Required metadata fields (ID, Status, Priority, Release)
# ---------------------------------------------------------------------------

class TestE002MetadataFields:
    def test_missing_ID_field_raises_E002(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("| ID        | STORY-042 |\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E002" in ids

    def test_missing_Status_field_raises_E002(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("| Status    | Draft |\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E002" in ids

    def test_all_required_fields_present_no_E002(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E002" not in ids


# ---------------------------------------------------------------------------
# E003 – ## Requirements section exists
# ---------------------------------------------------------------------------

class TestE003RequirementsSection:
    def test_missing_requirements_section_raises_E003(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Requirements\n", "## Reqmts\n")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E003" in ids

    def test_requirements_section_present_no_E003(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E003" not in ids


# ---------------------------------------------------------------------------
# E004 – At least one ### R{N}: subsection under Requirements
# ---------------------------------------------------------------------------

class TestE004RequirementSubsections:
    def test_no_R_subsection_raises_E004(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "### R1: First Requirement (MUST)\n\nThis requirement MUST be satisfied.\n",
            "Just some text without an R subsection.\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E004" in ids

    def test_R_subsection_present_no_E004(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E004" not in ids


# ---------------------------------------------------------------------------
# E005 – ## Acceptance Criteria section exists
# ---------------------------------------------------------------------------

class TestE005AcceptanceCriteria:
    def test_missing_AC_section_raises_E005(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Acceptance Criteria\n", "## Acceptance\n")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E005" in ids

    def test_AC_section_present_no_E005(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E005" not in ids


# ---------------------------------------------------------------------------
# E006 – At least one ### AC{N}: or ### Scenario {N}: subsection
# ---------------------------------------------------------------------------

class TestE006ACSubsections:
    def test_no_AC_subsection_raises_E006(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "### AC1: Happy Path (R1)\n**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "Just some text.\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E006" in ids

    def test_scenario_prefix_accepted_no_E006(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "### AC1: Happy Path (R1)\n**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "### Scenario 1: Happy Path (R1)\n**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E006" not in ids

    def test_AC_subsection_present_no_E006(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E006" not in ids


# ---------------------------------------------------------------------------
# E007 – AC contains Given/When/Then
# ---------------------------------------------------------------------------

class TestE007GivenWhenThen:
    def test_missing_given_raises_E007(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "**When** R1 action is taken\n**Then** the result is correct\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E007" in ids

    def test_missing_when_raises_E007(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "**Given** a valid input\n**Then** R1 result is correct\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E007" in ids

    def test_missing_then_raises_E007(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "**Given** a valid input\n**When** R1 action is taken\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E007" in ids

    def test_case_insensitive_keywords_no_E007(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "**Given** a valid input\n**When** R1 action is taken\n**Then** the result is correct\n",
            "given a valid input\nwhen R1 action is taken\nthen the result is correct\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E007" not in ids


# ---------------------------------------------------------------------------
# E008 – Release is not TBD
# ---------------------------------------------------------------------------

class TestE008ReleaseTBD:
    def test_TBD_release_raises_E008(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("| Release   | 1.4.0 |", "| Release   | TBD |")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E008" in ids

    def test_concrete_release_no_E008(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        ids = [e.rule_id for e in result.errors]
        assert "E008" not in ids


# ---------------------------------------------------------------------------
# WARN rules
# ---------------------------------------------------------------------------

class TestWarnRules:
    def test_W001_missing_background(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Background\n\nSome background text.\n\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [w.rule_id for w in result.warnings]
        assert "W001" in ids

    def test_W002_missing_call_chain(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Target Call Chain\n\nSome call chain.\n\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [w.rule_id for w in result.warnings]
        assert "W002" in ids

    def test_W003_no_rfc2119_keywords(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace(
            "### R1: First Requirement (MUST)\n\nThis requirement MUST be satisfied.\n",
            "### R1: First Requirement\n\nThis is some text with no RFC keywords.\n"
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [w.rule_id for w in result.warnings]
        assert "W003" in ids

    def test_W004_missing_out_of_scope(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Out of Scope\n\n- Not in scope.\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        ids = [w.rule_id for w in result.warnings]
        assert "W004" in ids

    def test_all_warnings_absent_on_complete_spec(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        assert result.warnings == []


# ---------------------------------------------------------------------------
# AC1 / AC2 / AC3: Integration scenarios
# ---------------------------------------------------------------------------

class TestCodeBlockFalsePositive:
    """Heading-like text inside fenced code blocks must not trip up section detection."""

    def test_heading_inside_code_block_not_confused_as_section(self, tmp_path):
        """## Acceptance Criteria inside a code fence must not shadow the real section."""
        content = MINIMAL_VALID_SPEC.replace(
            "## Requirements\n\n### R1: First Requirement (MUST)\n\nThis requirement MUST be satisfied.\n",
            "## Requirements\n\n### R1: First Requirement (MUST)\n\nExample output format:\n\n```markdown\n## Acceptance Criteria\n- [ ] AC1: fake\n```\n\nThis requirement MUST be satisfied.\n",
        )
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        # Real AC section exists and has Given/When/Then — should pass
        assert result.passed is True
        ids = [e.rule_id for e in result.errors]
        assert "E005" not in ids
        assert "E006" not in ids
        assert "E007" not in ids


class TestIntegrationScenarios:
    def test_AC1_error_spec_not_passed(self, tmp_path):
        """Missing ## Acceptance Criteria → errors → passed=False."""
        content = MINIMAL_VALID_SPEC.replace("## Acceptance Criteria\n", "## Acceptance\n")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        assert result.passed is False
        assert any(e.rule_id == "E005" for e in result.errors)

    def test_AC2_warn_only_spec_is_passed(self, tmp_path):
        """Missing Out of Scope only → warnings only → passed=True."""
        content = MINIMAL_VALID_SPEC.replace("## Out of Scope\n\n- Not in scope.\n", "")
        spec = write_spec(tmp_path, content)
        result = validate_spec(str(spec))
        assert result.passed is True
        assert any(w.rule_id == "W004" for w in result.warnings)

    def test_AC3_perfect_spec_passes_silently(self, tmp_path):
        """Complete, valid spec → no errors, no warnings."""
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        result = validate_spec(str(spec))
        assert result.passed is True
        assert result.errors == []
        assert result.warnings == []


# ---------------------------------------------------------------------------
# AC5: CLI – --all flag
# ---------------------------------------------------------------------------

_LINTER_PATH = str(Path(__file__).parents[2] / "src" / "pactkit" / "skills" / "spec_linter.py")


class TestCLI:
    def test_cli_single_file_pass(self, tmp_path):
        spec = write_spec(tmp_path, MINIMAL_VALID_SPEC)
        cmd = [sys.executable, _LINTER_PATH, str(spec)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0

    def test_cli_single_file_fail(self, tmp_path):
        content = MINIMAL_VALID_SPEC.replace("## Acceptance Criteria\n", "## Acceptance\n")
        spec = write_spec(tmp_path, content)
        cmd = [sys.executable, _LINTER_PATH, str(spec)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode != 0
        assert "E005" in result.stdout or "E005" in result.stderr

    def test_cli_all_flag(self, tmp_path):
        # Create two spec files in tmp_path
        (tmp_path / "STORY-A.md").write_text(MINIMAL_VALID_SPEC, encoding="utf-8")
        bad = MINIMAL_VALID_SPEC.replace("## Acceptance Criteria\n", "## Acceptance\n")
        (tmp_path / "STORY-B.md").write_text(bad, encoding="utf-8")
        cmd = [sys.executable, _LINTER_PATH, "--all", "--specs-dir", str(tmp_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Should exit non-zero because STORY-B has errors
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "STORY-B" in output
        assert "E005" in output
