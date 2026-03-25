"""
BUG-028: Ghost DEV_REF Residual in Check and Review — Regression Guard

Verify:
- AC1: Check playbook has no ghost DEV_REF_* or TEST_REF_* name references
- AC2: Review skill (REVIEW_PROMPT) has no ghost DEV_REF_* or TEST_REF_* name references
- AC3: Regression guard — no COMMANDS_CONTENT value or workflow prompt contains
       unresolvable DEV_REF_* or TEST_REF_* name references (deployer.py never injects them)
"""
import re

import pytest

from pactkit import prompts

# Ghost ref pattern: DEV_REF_* or TEST_REF_* appearing as a NAME reference
# (i.e., the constant name in prose, not a discussion about the concept).
# Matches: DEV_REF_FRONTEND, DEV_REF_BACKEND, TEST_REF_PYTHON, TEST_REF_NODE, etc.
GHOST_REF_PATTERN = re.compile(r'\bDEV_REF_[A-Z]+\b|\bTEST_REF_[A-Z]+\b')


class TestAC1CheckNoGhostRefs:
    """AC1: Check playbook has no ghost refs."""

    def test_check_playbook_no_dev_ref(self):
        """Check playbook must not contain DEV_REF_* name references."""
        check = prompts.COMMANDS_CONTENT['project-check.md']
        matches = GHOST_REF_PATTERN.findall(check)
        assert matches == [], (
            f"Check playbook contains ghost refs: {matches}. "
            "deployer.py never injects their content."
        )


class TestAC2ReviewNoGhostRefs:
    """AC2: Review skill (REVIEW_PROMPT) has no ghost refs."""

    def test_review_prompt_no_dev_ref(self):
        """REVIEW_PROMPT must not contain DEV_REF_* or TEST_REF_* name references."""
        matches = GHOST_REF_PATTERN.findall(prompts.REVIEW_PROMPT)
        assert matches == [], (
            f"REVIEW_PROMPT contains ghost refs: {matches}. "
            "deployer.py never injects their content."
        )


class TestAC3RegressionGuard:
    """AC3: No COMMANDS_CONTENT value or workflow prompt contains ghost refs."""

    @pytest.mark.parametrize("cmd_key", list(prompts.COMMANDS_CONTENT.keys()))
    def test_command_no_ghost_refs(self, cmd_key):
        """No command playbook should contain unresolvable DEV_REF_*/TEST_REF_* refs."""
        content = prompts.COMMANDS_CONTENT[cmd_key]
        matches = GHOST_REF_PATTERN.findall(content)
        assert matches == [], (
            f"Command '{cmd_key}' contains ghost refs: {matches}. "
            "deployer.py never injects their content."
        )

    def test_review_prompt_no_ghost_refs(self):
        """REVIEW_PROMPT should not contain ghost refs (redundant with AC2 but part of guard)."""
        matches = GHOST_REF_PATTERN.findall(prompts.REVIEW_PROMPT)
        assert matches == [], (
            f"REVIEW_PROMPT contains ghost refs: {matches}"
        )

    def test_design_prompt_no_ghost_refs(self):
        """DESIGN_PROMPT should not contain ghost refs."""
        matches = GHOST_REF_PATTERN.findall(prompts.DESIGN_PROMPT)
        assert matches == [], (
            f"DESIGN_PROMPT contains ghost refs: {matches}"
        )

    def test_sprint_prompt_no_ghost_refs(self):
        """SPRINT_PROMPT should not contain ghost refs."""
        matches = GHOST_REF_PATTERN.findall(prompts.SPRINT_PROMPT)
        assert matches == [], (
            f"SPRINT_PROMPT contains ghost refs: {matches}"
        )

    def test_hotfix_prompt_no_ghost_refs(self):
        """HOTFIX_PROMPT should not contain ghost refs."""
        matches = GHOST_REF_PATTERN.findall(prompts.HOTFIX_PROMPT)
        assert matches == [], (
            f"HOTFIX_PROMPT contains ghost refs: {matches}"
        )
