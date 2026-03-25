"""Tests for STORY-slim-026: Plan Spec Generation — Scaffold-First, AI-Fill Pattern."""

import re


def _get_plan_prompt():
    """Return the project-plan.md prompt content."""
    from pactkit.prompts.commands import COMMANDS_CONTENT
    return COMMANDS_CONTENT["project-plan.md"]


def _extract_phase(prompt, phase_label):
    """Extract text for a given phase (e.g., 'Phase 3.2a') until the next phase heading."""
    pattern = rf"(## 🎬 {re.escape(phase_label)}.*?)(?=## 🎬|## 🛡️|$)"
    m = re.search(pattern, prompt, re.DOTALL)
    return m.group(1) if m else ""


# ===========================================================================
# AC1: Phase 3.2a calls scaffold before AI writes (R1)
# ===========================================================================

class TestAC1ScaffoldFirst:

    def test_phase_32a_starts_with_scaffold_cmd(self):
        """Phase 3.2a first instruction MUST be {SCAFFOLD_CMD} create_spec."""
        phase = _extract_phase(_get_plan_prompt(), "Phase 3.2a")
        assert phase, "Phase 3.2a not found in plan prompt"
        # The first numbered instruction should reference scaffold create_spec
        assert "{SCAFFOLD_CMD} create_spec" in phase

    def test_phase_32a_has_read_after_scaffold(self):
        """After scaffold, the prompt MUST instruct to Read the file."""
        phase = _extract_phase(_get_plan_prompt(), "Phase 3.2a")
        scaffold_idx = phase.find("{SCAFFOLD_CMD} create_spec")
        read_idx = phase.lower().find("read")
        assert scaffold_idx > 0
        assert read_idx > scaffold_idx, "Read must come after scaffold call"


# ===========================================================================
# AC2: Phase 3.2a-c use Edit not Write (R2)
# ===========================================================================

class TestAC2EditNotWrite:

    def test_phase_32a_uses_edit(self):
        """Phase 3.2a MUST use Edit/replace, not Create file or Write."""
        phase = _extract_phase(_get_plan_prompt(), "Phase 3.2a")
        phase_lower = phase.lower()
        # Should contain edit/replace instructions
        assert "edit" in phase_lower or "replace" in phase_lower
        # Should NOT contain "Create file" as instruction for spec file
        assert "Create file" not in phase

    def test_phase_32b_no_write(self):
        """Phase 3.2b MUST NOT say Write or Create file for spec."""
        phase = _extract_phase(_get_plan_prompt(), "Phase 3.2b")
        assert "Create file" not in phase

    def test_phase_32c_no_write(self):
        """Phase 3.2c MUST NOT say Write or Create file for spec."""
        phase = _extract_phase(_get_plan_prompt(), "Phase 3.2c")
        assert "Create file" not in phase


# ===========================================================================
# AC3: No inline markdown format examples in Phase 3.2a-c (R3)
# ===========================================================================

class TestAC3NoFormatFences:

    def _phases_32abc_text(self):
        prompt = _get_plan_prompt()
        return (
            _extract_phase(prompt, "Phase 3.2a")
            + _extract_phase(prompt, "Phase 3.2b")
            + _extract_phase(prompt, "Phase 3.2c")
        )

    def test_no_metadata_table_format(self):
        """No fenced code block containing metadata table format."""
        text = self._phases_32abc_text()
        # Should not contain the old metadata table format example
        assert "| Field | Value |" not in text or "```" not in text.split("| Field | Value |")[0][-50:]
        # More precise: no fenced block with Field/Value table
        fenced = re.findall(r"```.*?```", text, re.DOTALL)
        for block in fenced:
            assert "| Field | Value |" not in block, f"Metadata table format in fenced block: {block[:80]}"

    def test_no_implementation_steps_format(self):
        """No fenced code block containing Implementation Steps table format."""
        text = self._phases_32abc_text()
        fenced = re.findall(r"```.*?```", text, re.DOTALL)
        for block in fenced:
            assert "| Step | File |" not in block, f"Impl Steps table in fenced block: {block[:80]}"

    def test_no_security_scope_format(self):
        """No fenced code block containing Security Scope table format."""
        text = self._phases_32abc_text()
        fenced = re.findall(r"```.*?```", text, re.DOTALL)
        for block in fenced:
            assert "| Check | Applicable |" not in block, f"Security Scope table in fenced block: {block[:80]}"


# ===========================================================================
# AC4: Design workflow unchanged (R5)
# ===========================================================================

class TestAC4DesignUnchanged:

    def test_design_prompt_contains_scaffold(self):
        """Design workflow MUST still reference {SCAFFOLD_CMD} create_spec."""
        from pactkit.prompts.workflows import DESIGN_PROMPT
        assert "{SCAFFOLD_CMD} create_spec" in DESIGN_PROMPT


# ===========================================================================
# AC5: Plan prompt character count stable or reduced (R6)
# ===========================================================================

class TestAC5CharCount:

    def test_plan_prompt_not_longer_than_baseline(self):
        """Plan prompt SHOULD be shorter or equal to 9817 chars (pre-change baseline)."""
        prompt = _get_plan_prompt()
        assert len(prompt) <= 9817, f"Plan prompt grew to {len(prompt)} chars (baseline: 9817)"
