"""Tests for STORY-slim-027: Proactive Quality Sweep.

AC1-AC15 covering substring bugs, schema mismatches, and workflow gaps.
"""
from __future__ import annotations

from unittest.mock import patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_spec(ac_section: str, bg: str = "Real background.", security: str = None) -> str:
    """Build a minimal valid spec with custom AC section."""
    sec = security or (
        "## Security Scope\n\n"
        "| Check | Applicable | Reason |\n"
        "|-------|------------|--------|\n"
        "| SEC-1 | N/A | test |\n"
    )
    return (
        "# TEST-001: Test Spec\n\n"
        "| Field | Value |\n"
        "|-------|-------|\n"
        "| ID | TEST-001 |\n"
        "| Status | Draft |\n"
        "| Priority | P1 |\n"
        "| Release | 1.0.0 |\n\n"
        "## Background\n\n"
        f"{bg}\n\n"
        "## Requirements\n\n"
        "### R1: Something (MUST)\n\n"
        "Description of R1.\n\n"
        "## Acceptance Criteria\n\n"
        f"{ac_section}\n\n"
        "## Target Call Chain\n\n"
        "Some call chain.\n\n"
        "## Implementation Steps\n\n"
        "| Step | File | Action | Dependencies | Risk |\n"
        "|------|------|--------|-------------|------|\n"
        "| 1 | `src/example.py` | Do something | None | Low |\n\n"
        f"{sec}\n\n"
        "## Out of Scope\n\n"
        "- Nothing\n"
    )


# ===========================================================================
# AC1 + AC2: issue_sync STORY-1 does not match STORY-10, exact match works
# ===========================================================================


class TestAC1IssueSync:
    """AC1: _search_issue('STORY-1') must NOT match title 'STORY-10: Some Feature'."""

    def test_story1_does_not_match_story10(self):
        from pactkit.issue_sync import _search_issue

        fake_issues = [{"title": "STORY-10: Some Feature", "number": 10, "url": "http://x/10"}]
        with patch("pactkit.issue_sync.subprocess") as mock_sub:
            import json
            mock_sub.run.return_value = type("R", (), {
                "returncode": 0, "stdout": json.dumps(fake_issues)
            })()
            result = _search_issue("STORY-1")
        assert result is None


class TestAC2IssueSyncExactMatch:
    """AC2: _search_issue('STORY-1') MUST match title 'STORY-1: Some Feature'."""

    def test_story1_matches_story1(self):
        from pactkit.issue_sync import _search_issue

        fake_issues = [{"title": "STORY-1: Some Feature", "number": 1, "url": "http://x/1"}]
        with patch("pactkit.issue_sync.subprocess") as mock_sub:
            import json
            mock_sub.run.return_value = type("R", (), {
                "returncode": 0, "stdout": json.dumps(fake_issues)
            })()
            result = _search_issue("STORY-1")
        assert result is not None
        assert result["number"] == 1


# ===========================================================================
# AC3: Security Scope in SPEC_REQUIRED_SECTIONS
# ===========================================================================


class TestAC3SecurityScopeRequired:
    """AC3: '## Security Scope' MUST be in SPEC_REQUIRED_SECTIONS, NOT in OPTIONAL."""

    def test_security_scope_in_required(self):
        from pactkit.schemas import SPEC_REQUIRED_SECTIONS
        assert "## Security Scope" in SPEC_REQUIRED_SECTIONS

    def test_security_scope_not_in_optional(self):
        from pactkit.schemas import SPEC_OPTIONAL_SECTIONS
        assert "## Security Scope" not in SPEC_OPTIONAL_SECTIONS


# ===========================================================================
# AC4 + AC5: E007 per-subsection Given/When/Then check
# ===========================================================================


class TestAC4E007PerSubsection:
    """AC4: E007 fires for AC2 (missing When/Then) but NOT for AC1 (complete)."""

    def test_e007_fires_for_incomplete_ac(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec

        ac = (
            "### AC1: Complete (R1)\n\n"
            "- **Given** precondition\n"
            "- **When** action\n"
            "- **Then** result\n\n"
            "### AC2: Incomplete (R1)\n\n"
            "- **Given** precondition only"
        )
        spec_file = tmp_path / "test.md"
        spec_file.write_text(_make_spec(ac))

        result = validate_spec(str(spec_file))
        e007s = [e for e in result.errors if e.rule_id == "E007"]
        assert len(e007s) >= 1
        # Must mention AC2
        assert any("AC2" in e.message for e in e007s)
        # Must NOT mention AC1
        assert not any("AC1" in e.message for e in e007s)


class TestAC5E007AllValid:
    """AC5: E007 does NOT fire when every AC has Given, When, Then."""

    def test_e007_passes_all_valid(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec

        ac = (
            "### AC1: First (R1)\n\n"
            "- **Given** precondition\n"
            "- **When** action\n"
            "- **Then** result\n\n"
            "### AC2: Second (R1)\n\n"
            "- **Given** precondition\n"
            "- **When** action\n"
            "- **Then** result"
        )
        spec_file = tmp_path / "test.md"
        spec_file.write_text(_make_spec(ac))

        result = validate_spec(str(spec_file))
        e007s = [e for e in result.errors if e.rule_id == "E007"]
        assert len(e007s) == 0


# ===========================================================================
# AC6 + AC7: Placeholder detection (W008 or extended W001/W002)
# ===========================================================================


class TestAC6BackgroundPlaceholder:
    """AC6: Warning when Background contains scaffold placeholder text."""

    def test_detects_background_placeholder(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec

        ac = (
            "### AC1: Scenario (R1)\n\n"
            "- **Given** precondition\n"
            "- **When** action\n"
            "- **Then** result"
        )
        spec_file = tmp_path / "test.md"
        spec_file.write_text(_make_spec(ac, bg="(Description of the problem or feature)"))

        result = validate_spec(str(spec_file))
        placeholder_warns = [w for w in result.warnings if "placeholder" in w.message.lower()]
        assert len(placeholder_warns) >= 1


class TestAC7TargetCallChainPlaceholder:
    """AC7: Warning when Target Call Chain contains scaffold placeholder text."""

    def test_detects_call_chain_placeholder(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec

        ac = (
            "### AC1: Scenario (R1)\n\n"
            "- **Given** precondition\n"
            "- **When** action\n"
            "- **Then** result"
        )
        # Use _make_spec but override target call chain via direct string building
        spec_text = (
            "# TEST-001: Test Spec\n\n"
            "| Field | Value |\n"
            "|-------|-------|\n"
            "| ID | TEST-001 |\n"
            "| Status | Draft |\n"
            "| Priority | P1 |\n"
            "| Release | 1.0.0 |\n\n"
            "## Background\n\nReal background content.\n\n"
            "## Requirements\n\n### R1: Something (MUST)\n\nDescription.\n\n"
            "## Acceptance Criteria\n\n" + ac + "\n\n"
            "## Target Call Chain\n\n(Trace call chain here)\n\n"
            "## Implementation Steps\n\n"
            "| Step | File | Action | Dependencies | Risk |\n"
            "|------|------|--------|-------------|------|\n"
            "| 1 | `src/example.py` | Do something | None | Low |\n\n"
            "## Security Scope\n\n"
            "| Check | Applicable | Reason |\n"
            "|-------|------------|--------|\n"
            "| SEC-1 | N/A | test |\n\n"
            "## Out of Scope\n\n- Nothing\n"
        )
        spec_file = tmp_path / "test.md"
        spec_file.write_text(spec_text)

        result = validate_spec(str(spec_file))
        placeholder_warns = [w for w in result.warnings if "placeholder" in w.message.lower()]
        assert len(placeholder_warns) >= 1


# ===========================================================================
# AC8: Design prompt includes sec-scope
# ===========================================================================


class TestAC8DesignSecScope:
    """AC8: DESIGN_PROMPT contains sec-scope reference."""

    def test_design_prompt_has_sec_scope(self):
        from pactkit.prompts.workflows import DESIGN_PROMPT
        assert "sec-scope" in DESIGN_PROMPT or "sec_scope" in DESIGN_PROMPT


# ===========================================================================
# AC9: Act prompt includes lint step
# ===========================================================================


class TestAC9ActLint:
    """AC9: Act prompt Phase 3 contains lint instruction."""

    def test_act_prompt_has_lint(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        act = COMMANDS_CONTENT["project-act.md"]
        assert "lint" in act.lower()


# ===========================================================================
# AC10: Act prompt moves story to In Progress
# ===========================================================================


class TestAC10ActInProgress:
    """AC10: Act prompt references moving story to In Progress."""

    def test_act_prompt_has_in_progress(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        act = COMMANDS_CONTENT["project-act.md"]
        assert "In Progress" in act


# ===========================================================================
# AC11: create_skill uses base_dir for path
# ===========================================================================


class TestAC11CreateSkillPath:
    """AC11: create_skill() SKILL.md uses base_dir or {SKILLS_ROOT}, not hardcoded ~/.claude/skills."""

    def test_create_skill_no_hardcoded_path(self, tmp_path):
        from pactkit.skills.scaffold import create_skill

        result = create_skill("test-skill", "A test skill", base_dir=str(tmp_path))
        assert "Skill" in result  # success marker

        skill_md = (tmp_path / "test-skill" / "SKILL.md").read_text()
        # Must NOT contain the hardcoded path
        assert "~/.claude/skills" not in skill_md


# ===========================================================================
# AC12: GWT uses word boundary
# ===========================================================================


class TestAC12GWTWordBoundary:
    """AC12: 'whenever' should NOT satisfy the 'when' keyword check."""

    def test_whenever_does_not_match_when(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec

        ac = (
            "### AC1: Scenario (R1)\n\n"
            "- **Given** precondition\n"
            "- whenever something happens\n"
            "- **Then** result"
        )
        spec_file = tmp_path / "test.md"
        spec_file.write_text(_make_spec(ac))

        result = validate_spec(str(spec_file))
        e007s = [e for e in result.errors if e.rule_id == "E007"]
        # "when" should be reported as missing (not matched by "whenever")
        missing_when = any("WHEN" in e.message.upper() or "when" in e.message.lower() for e in e007s)
        assert missing_when, f"Expected E007 for missing 'when', got: {[e.message for e in e007s]}"


# ===========================================================================
# AC13: SPEC_OPTIONAL_SECTIONS includes Non-Goals
# ===========================================================================


class TestAC13NonGoals:
    """AC13: Non-Goals appears in SPEC_OPTIONAL_SECTIONS or related constant."""

    def test_non_goals_in_optional(self):
        from pactkit.schemas import SPEC_OPTIONAL_SECTIONS
        has_non_goals = any("Non-Goals" in s for s in SPEC_OPTIONAL_SECTIONS)
        assert has_non_goals, f"Non-Goals not found in SPEC_OPTIONAL_SECTIONS: {SPEC_OPTIONAL_SECTIONS}"


# ===========================================================================
# AC14: Fallback RFC pattern derived from tuple
# ===========================================================================


class TestAC14FallbackRFC:
    """AC14: Fallback RFC pattern uses SPEC_RFC_KEYWORDS, not hardcoded string."""

    def test_fallback_not_hardcoded(self):
        import inspect

        from pactkit.skills import spec_linter

        source = inspect.getsource(spec_linter)
        # Find the fallback block (after "except ImportError:")
        fallback_idx = source.find("except ImportError:")
        assert fallback_idx > 0, "Fallback block not found"
        fallback_block = source[fallback_idx:fallback_idx + 2000]

        # The fallback SPEC_RFC_PATTERN should derive from SPEC_RFC_KEYWORDS
        # It should NOT contain a hardcoded literal like (MUST|SHOULD|MAY|...)
        # Instead it should use join() or similar dynamic construction
        assert "SPEC_RFC_KEYWORDS" in fallback_block or "join" in fallback_block, \
            "Fallback RFC pattern should derive from SPEC_RFC_KEYWORDS tuple, not hardcoded"


# ===========================================================================
# AC15: Existing tests pass (regression) — tested by running pytest
# ===========================================================================


class TestAC15Regression:
    """AC15: Placeholder — actual regression tested by running full pytest suite."""

    def test_placeholder(self):
        # This is verified by the full test suite run, not by a unit test
        pass
