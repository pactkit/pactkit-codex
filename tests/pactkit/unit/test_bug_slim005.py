"""Tests for BUG-slim-005: Cross-Flow Residual Gaps."""

from __future__ import annotations


def _get_hotfix_prompt() -> str:
    from pactkit.prompts.workflows import HOTFIX_PROMPT
    return HOTFIX_PROMPT


def _get_act_prompt() -> str:
    from pactkit.prompts.commands import COMMANDS_CONTENT
    return COMMANDS_CONTENT["project-act.md"]


def _get_check_prompt() -> str:
    from pactkit.prompts.commands import COMMANDS_CONTENT
    return COMMANDS_CONTENT["project-check.md"]


def _get_lang_profiles() -> dict:
    from pactkit.prompts.workflows import LANG_PROFILES
    return LANG_PROFILES


# --- AC1: Hotfix context update ---

class TestAC1HotfixContext:
    def test_hotfix_has_pactkit_context(self):
        """R1: HOTFIX_PROMPT must contain 'pactkit context'."""
        prompt = _get_hotfix_prompt()
        assert "pactkit context" in prompt

    def test_hotfix_phase_35_exists(self):
        """R1: Phase 3.5 session context update section exists."""
        prompt = _get_hotfix_prompt()
        assert "Phase 3.5" in prompt or "Session Context" in prompt


# --- AC2: Hotfix board ref ---

class TestAC2HotfixBoardRef:
    def test_hotfix_board_update_references_board_cmd(self):
        """R2: Hotfix board update step must reference {BOARD_CMD} update_task."""
        prompt = _get_hotfix_prompt()
        assert "{BOARD_CMD}" in prompt
        assert "update_task" in prompt


# --- AC3: Act board ref ---

class TestAC3ActBoardRef:
    def test_act_board_update_references_board_cmd(self):
        """R3: Act Phase 4.2 must reference {BOARD_CMD} update_task."""
        prompt = _get_act_prompt()
        assert "{BOARD_CMD}" in prompt
        assert "update_task" in prompt


# --- AC4: lint-testcase in Check ---

class TestAC4LintTestcase:
    def test_check_prompt_references_lint_testcase(self):
        """R4: Check prompt must reference pactkit lint-testcase."""
        prompt = _get_check_prompt()
        assert "lint-testcase" in prompt


# --- AC5: Dead keys removed ---

class TestAC5DeadKeysRemoved:
    DEAD_KEYS = {"test_dir", "package_file", "e2e_test_pattern"}

    def test_python_no_dead_keys(self):
        profiles = _get_lang_profiles()
        assert self.DEAD_KEYS.isdisjoint(profiles["python"].keys())

    def test_node_no_dead_keys(self):
        profiles = _get_lang_profiles()
        assert self.DEAD_KEYS.isdisjoint(profiles["node"].keys())

    def test_go_no_dead_keys(self):
        profiles = _get_lang_profiles()
        assert self.DEAD_KEYS.isdisjoint(profiles["go"].keys())

    def test_java_no_dead_keys(self):
        profiles = _get_lang_profiles()
        assert self.DEAD_KEYS.isdisjoint(profiles["java"].keys())


# --- AC6: Consumed keys intact ---

class TestAC6ConsumedKeysIntact:
    from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
    CONSUMED_KEYS = LANG_PROFILE_REQUIRED_KEYS

    def test_python_has_consumed_keys(self):
        profiles = _get_lang_profiles()
        assert self.CONSUMED_KEYS.issubset(profiles["python"].keys())

    def test_node_has_consumed_keys(self):
        profiles = _get_lang_profiles()
        assert self.CONSUMED_KEYS.issubset(profiles["node"].keys())

    def test_go_has_consumed_keys(self):
        profiles = _get_lang_profiles()
        assert self.CONSUMED_KEYS.issubset(profiles["go"].keys())

    def test_java_has_consumed_keys(self):
        profiles = _get_lang_profiles()
        assert self.CONSUMED_KEYS.issubset(profiles["java"].keys())
