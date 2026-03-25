"""STORY-023: Test Quality Gate in QA Check."""
from pactkit.prompts.commands import COMMANDS_CONTENT


class TestQualityGatePhase:
    """project-check must include a Test Quality Gate phase."""

    def _get_check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_quality_gate_phase_exists(self):
        """R1: project-check must have a Phase 3.5 Test Quality Gate."""
        prompt = self._get_check_prompt()
        assert "Test Quality Gate" in prompt or "Test Quality" in prompt

    def test_quality_gate_between_spec_and_execution(self):
        """R1: Quality Gate must appear after Phase 3 and before Phase 4."""
        prompt = self._get_check_prompt()
        spec_phase_pos = prompt.find("Spec Verification")
        quality_gate_pos = prompt.find("Test Quality")
        execution_phase_pos = prompt.find("E2E Execution")
        assert spec_phase_pos > 0
        assert quality_gate_pos > 0
        assert execution_phase_pos > 0
        assert spec_phase_pos < quality_gate_pos < execution_phase_pos


class TestAntiPatternChecklist:
    """QA Agent must check for specific test anti-patterns."""

    def _get_check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_tautological_assertion_check(self):
        """R2: Must detect tautological assertions."""
        prompt = self._get_check_prompt()
        lower = prompt.lower()
        assert "tautolog" in lower or "assert true" in lower

    def test_over_mock_check(self):
        """R2: Must detect over-mocking."""
        prompt = self._get_check_prompt()
        lower = prompt.lower()
        assert "over-mock" in lower or "mock" in lower

    def test_happy_path_only_check(self):
        """R2: Must detect happy-path-only tests."""
        prompt = self._get_check_prompt()
        lower = prompt.lower()
        assert "happy" in lower or "happy-path" in lower

    def test_missing_assertion_check(self):
        """R2: Must detect tests with no assertions."""
        prompt = self._get_check_prompt()
        lower = prompt.lower()
        assert "missing assert" in lower or "no assert" in lower


class TestVerdictIntegration:
    """Phase 5 verdict must include Test Quality row."""

    def _get_check_prompt(self):
        return COMMANDS_CONTENT["project-check.md"]

    def test_verdict_has_test_quality_row(self):
        """R3: Verdict Scan Summary table must include Test Quality."""
        prompt = self._get_check_prompt()
        assert "Test Quality" in prompt
        # Verify it appears in the table area (near Security and Quality rows)
        verdict_pos = prompt.find("Scan Summary")
        test_quality_pos = prompt.find("Test Quality", verdict_pos)
        assert test_quality_pos > verdict_pos
