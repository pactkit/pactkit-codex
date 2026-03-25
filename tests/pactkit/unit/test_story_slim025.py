"""Tests for STORY-slim-025: Spec Generation Consistency — Prompt/Linter/Template Alignment."""

import re
from pathlib import Path

from pactkit.skills.spec_linter import validate_spec

# ---------------------------------------------------------------------------
# Helper: base spec with Security Scope (passes E001-E008, E009)
# ---------------------------------------------------------------------------

def _base_spec(**overrides):
    """Build a valid spec string, optionally overriding sections."""
    sections = {
        "metadata": """\
| Field | Value |
|-------|-------|
| ID | TEST-025 |
| Status | Draft |
| Priority | P2 |
| Release | 1.0.0 |""",
        "background": "## Background\n\nTest background.",
        "target_call_chain": "## Target Call Chain\n\n```\nA -> B\n```",
        "requirements": """\
## Requirements

### R1: First requirement
Something MUST happen.""",
        "acceptance_criteria": """\
## Acceptance Criteria

### AC1: Test R1
- **Given** a condition
- **When** R1 is tested
- **Then** it passes""",
        "security_scope": """\
## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | N/A | Test only |""",
        "out_of_scope": "## Out of Scope\n\n- Nothing.",
    }
    sections.update(overrides)
    return "\n\n".join(sections.values()) + "\n"


def _write_and_lint(tmp_path, spec_content):
    """Write spec to tmp_path and return LintResult."""
    p = tmp_path / "TEST-025.md"
    p.write_text(spec_content, encoding="utf-8")
    return validate_spec(str(p))


# ===========================================================================
# AC1: E009 fires on missing Security Scope (R1)
# ===========================================================================

class TestAC1E009MissingSecurityScope:

    def test_e009_fires_when_security_scope_absent(self, tmp_path):
        spec = _base_spec(security_scope="")
        result = _write_and_lint(tmp_path, spec)
        e009 = [e for e in result.errors if e.rule_id == "E009"]
        assert len(e009) == 1
        assert "Security Scope" in e009[0].message
        assert result.passed is False


# ===========================================================================
# AC2: E009 fires on Security Scope without SEC table (R1)
# ===========================================================================

class TestAC2E009NoSECTable:

    def test_e009_fires_when_no_sec_rows(self, tmp_path):
        spec = _base_spec(security_scope="## Security Scope\n\nSome prose but no SEC entries.")
        result = _write_and_lint(tmp_path, spec)
        e009 = [e for e in result.errors if e.rule_id == "E009"]
        assert len(e009) == 1
        assert "SEC-" in e009[0].message or "SEC" in e009[0].message


# ===========================================================================
# AC3: E009 passes on valid Security Scope (R1)
# ===========================================================================

class TestAC3E009ValidSecurityScope:

    def test_e009_passes_with_sec_table(self, tmp_path):
        spec = _base_spec()  # default has valid Security Scope
        result = _write_and_lint(tmp_path, spec)
        e009 = [e for e in result.errors if e.rule_id == "E009"]
        assert len(e009) == 0


# ===========================================================================
# AC4: SPEC_TEMPLATE includes all MUST sections (R2)
# ===========================================================================

class TestAC4SpecTemplateSections:

    def test_template_passes_lint_except_e008(self, tmp_path):
        """SPEC_TEMPLATE should only fail E008 (Release=TBD) and W008 (placeholders)."""
        from pactkit.schemas import SPEC_TEMPLATE
        content = SPEC_TEMPLATE.format(id="TEST-TPL", title="Template Test")
        p = tmp_path / "TEST-TPL.md"
        p.write_text(content, encoding="utf-8")
        result = validate_spec(str(p))
        non_e008_errors = [e for e in result.errors if e.rule_id != "E008"]
        assert non_e008_errors == [], f"Unexpected errors: {non_e008_errors}"
        # STORY-slim-027 R4: W008 placeholder warnings are expected for unfilled template
        non_w008_warnings = [w for w in result.warnings if w.rule_id != "W008"]
        assert non_w008_warnings == [], f"Unexpected warnings: {non_w008_warnings}"

    def test_template_has_security_scope(self):
        from pactkit.schemas import SPEC_TEMPLATE
        assert "## Security Scope" in SPEC_TEMPLATE

    def test_template_has_target_call_chain(self):
        from pactkit.schemas import SPEC_TEMPLATE
        assert "## Target Call Chain" in SPEC_TEMPLATE

    def test_template_has_implementation_steps(self):
        from pactkit.schemas import SPEC_TEMPLATE
        assert "## Implementation Steps" in SPEC_TEMPLATE

    def test_scaffold_template_matches_schemas(self):
        """scaffold.py _SPEC_TEMPLATE must be identical to schemas.py SPEC_TEMPLATE."""
        from pactkit.schemas import SPEC_TEMPLATE
        scaffold_path = Path(__file__).resolve().parents[2] / "src" / "pactkit" / "skills" / "scaffold.py"
        scaffold_src = scaffold_path.read_text(encoding="utf-8")
        # Extract _SPEC_TEMPLATE from scaffold source
        match = re.search(r'_SPEC_TEMPLATE = """\\\n(.*?)"""', scaffold_src, re.DOTALL)
        assert match is not None, "_SPEC_TEMPLATE not found in scaffold.py"
        scaffold_template = match.group(1)
        # schemas SPEC_TEMPLATE is the raw string without the triple-quote wrapper
        assert scaffold_template == SPEC_TEMPLATE


# ===========================================================================
# AC5: Phase 3.2d prompt requires 0 warnings (R3)
# ===========================================================================

class TestAC5Phase32dPromptText:

    def test_phase_32d_requires_zero_warnings(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        plan_prompt = COMMANDS_CONTENT["project-plan.md"]
        assert "0 errors AND 0 warnings" in plan_prompt or "0 errors and 0 warnings" in plan_prompt.lower()

    def test_phase_32d_mentions_warning(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        plan_prompt = COMMANDS_CONTENT["project-plan.md"]
        # Should mention WARNING, not just ERROR
        phase_32d_idx = plan_prompt.find("Phase 3.2d")
        assert phase_32d_idx > 0
        phase_32d_text = plan_prompt[phase_32d_idx:phase_32d_idx + 500]
        assert "WARNING" in phase_32d_text or "warning" in phase_32d_text.lower()


# ===========================================================================
# AC6: R1 not falsely covered by R10 (R4, R7)
# ===========================================================================

class TestAC6MultiDigitRN:

    def test_r1_not_covered_by_r10(self, tmp_path):
        """R1 must NOT be considered covered just because R10 appears in AC."""
        spec = _base_spec(
            requirements="""\
## Requirements

### R1: First requirement
Something MUST happen.

### R10: Tenth requirement
Something SHOULD happen.""",
            acceptance_criteria="""\
## Acceptance Criteria

### AC1: Test R10 only
- **Given** a condition
- **When** R10 is tested
- **Then** it passes""",
        )
        result = _write_and_lint(tmp_path, spec)
        w007 = [w for w in result.warnings if w.rule_id == "W007"]
        w007_ids = [w.message for w in w007]
        assert any("R1" in m for m in w007_ids), f"R1 should be flagged, got: {w007_ids}"
        assert not any("R10" in m for m in w007_ids), f"R10 should NOT be flagged, got: {w007_ids}"


# ===========================================================================
# AC7: Non-R-prefix text does not suppress W007 (R4, R7)
# ===========================================================================

class TestAC7NonRPrefixText:

    def test_error1_does_not_cover_r1(self, tmp_path):
        spec = _base_spec(
            acceptance_criteria="""\
## Acceptance Criteria

### AC1: Test something
- **Given** ERROR1 is handled
- **When** CR1 appears
- **Then** it passes""",
        )
        result = _write_and_lint(tmp_path, spec)
        w007 = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007) == 1
        assert "R1" in w007[0].message


# ===========================================================================
# AC8: RFC keyword word-boundary — MAYONNAISE (R5, R7)
# ===========================================================================

class TestAC8RFCWordBoundary:

    def test_mayonnaise_does_not_match_may(self, tmp_path):
        spec = _base_spec(
            requirements="""\
## Requirements

### R1: Handle MAYONNAISE dispenser
The system handles MAYONNAISE dispensing.""",
            acceptance_criteria="""\
## Acceptance Criteria

### AC1: Test something else
- **Given** a condition
- **When** something is tested
- **Then** it passes""",
        )
        result = _write_and_lint(tmp_path, spec)
        w007 = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007) == 1
        assert "(MAY)" not in w007[0].message
        # No RFC keyword found — emphasis should be empty
        assert ")" not in w007[0].message or "AC reference" == w007[0].message.split(")")[-1].strip()


# ===========================================================================
# AC9: All 7 RFC keywords detected (R5, R7)
# ===========================================================================

class TestAC9AllRFCKeywords:

    KEYWORDS = ["MUST", "SHOULD", "MAY", "SHALL", "REQUIRED", "RECOMMENDED", "OPTIONAL"]

    def test_each_rfc_keyword_detected(self, tmp_path):
        for kw in self.KEYWORDS:
            spec = _base_spec(
                requirements=f"""\
## Requirements

### R1: Requirement with {kw}
The system {kw} do something.""",
                acceptance_criteria="""\
## Acceptance Criteria

### AC1: Test something else
- **Given** a condition
- **When** something unrelated is tested
- **Then** it passes""",
            )
            result = _write_and_lint(tmp_path, spec)
            w007 = [w for w in result.warnings if w.rule_id == "W007"]
            assert len(w007) == 1, f"Expected 1 W007 for keyword {kw}, got {len(w007)}"
            assert f"({kw})" in w007[0].message, f"Expected ({kw}) in message, got: {w007[0].message}"

    def test_no_keyword_gives_empty_emphasis(self, tmp_path):
        spec = _base_spec(
            requirements="""\
## Requirements

### R1: Plain requirement
The system does something without any RFC keyword.""",
            acceptance_criteria="""\
## Acceptance Criteria

### AC1: Test something else
- **Given** a condition
- **When** something unrelated is tested
- **Then** it passes""",
        )
        result = _write_and_lint(tmp_path, spec)
        w007 = [w for w in result.warnings if w.rule_id == "W007"]
        assert len(w007) == 1
        # No parenthetical emphasis
        assert "(" not in w007[0].message


# ===========================================================================
# AC10: W003 and W007 use same detection mechanism (R5)
# ===========================================================================

class TestAC10SameDetectionMechanism:

    def test_no_plain_kw_in_string_in_w007(self):
        """W007 must not use plain 'kw in string' for RFC detection."""
        import inspect

        from pactkit.skills.spec_linter import _check_req_ac_coverage
        source = inspect.getsource(_check_req_ac_coverage)
        # Should NOT contain the old pattern: kw for kw in SPEC_RFC_KEYWORDS if kw in
        assert "if kw in" not in source, "W007 still uses plain 'kw in' substring matching"


# ===========================================================================
# AC11: _REQ_ID_PATTERN documented or unified (R6)
# ===========================================================================

class TestAC11ReqIdPatternDocumented:

    def test_req_id_pattern_has_comment(self):
        src = (Path(__file__).resolve().parents[2] / "src" / "pactkit" / "skills" / "spec_linter.py").read_text(encoding="utf-8")
        idx = src.find("_REQ_ID_PATTERN")
        assert idx > 0
        # Check surrounding ~3 lines for a comment about SPEC_REQUIREMENT_PATTERN or whitespace
        context = src[max(0, idx - 200):idx + 200]
        has_doc = ("SPEC_REQUIREMENT_PATTERN" in context or
                   "whitespace" in context.lower() or
                   "\\s+" in context)
        assert has_doc, "_REQ_ID_PATTERN lacks documentation about divergence from SPEC_REQUIREMENT_PATTERN"


# ===========================================================================
# AC13: Sectional write rule says 300 (R8)
# ===========================================================================

class TestAC13SectionalWriteRule:

    def test_applies_to_says_300(self):
        from pactkit.prompts.rules import RULES_MODULES
        sectional = RULES_MODULES["sectional"]
        assert "over 300 lines" in sectional
        assert "over 150 lines" not in sectional
