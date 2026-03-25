"""STORY-019: Bailout Protocol for TDD Environment Failures."""
import re

from pactkit.prompts.commands import COMMANDS_CONTENT


class TestBailoutProtocol:
    """Act TDD loop must have environment-failure bailout."""

    def _act_prompt(self):
        return COMMANDS_CONTENT["project-act.md"]

    def test_env_failure_detection_clause(self):
        """R1: TDD loop must mention environment-class errors."""
        prompt = self._act_prompt()
        assert "ModuleNotFoundError" in prompt
        assert "ConnectionError" in prompt

    def test_import_error_mentioned(self):
        """R1: ImportError should be listed as env-class error."""
        prompt = self._act_prompt()
        assert "ImportError" in prompt

    def test_no_modify_business_code_on_env_error(self):
        """R2: Bailout must forbid modifying business code on env errors."""
        prompt = self._act_prompt()
        # Must have instruction about not modifying business logic for env errors
        assert re.search(
            r"(do not|DO NOT|MUST NOT).{0,50}(business|source).{0,30}(code|logic)",
            prompt,
            re.IGNORECASE,
        )

    def test_resolve_dependency_first(self):
        """R2: Should attempt to resolve dependency before stopping."""
        prompt = self._act_prompt()
        assert "pip install" in prompt or "dependency" in prompt.lower()

    def test_loop_iteration_cap(self):
        """R3: TDD loop should have a max iteration count."""
        prompt = self._act_prompt()
        # Must mention iteration limit / max iterations / cap
        assert re.search(r"(iteration|loop).{0,30}(cap|limit|max)", prompt, re.IGNORECASE)

    def test_stop_on_cap_exceeded(self):
        """R3: Must STOP when cap is exceeded."""
        prompt = self._act_prompt()
        # Must have a stop instruction related to iteration cap
        assert re.search(r"(exceed|reach).{0,40}STOP", prompt, re.IGNORECASE)

    def test_normal_assertion_error_not_blocked(self):
        """S4: AssertionError (normal TDD red) must NOT trigger bailout."""
        prompt = self._act_prompt()
        assert "AssertionError" in prompt or "AssertionError" in prompt or "normal" in prompt.lower()

    def test_service_down_stop(self):
        """S3: ConnectionRefusedError should trigger STOP."""
        prompt = self._act_prompt()
        assert "ConnectionRefusedError" in prompt or "external service" in prompt.lower()
