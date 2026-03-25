"""Tests for STORY-061: Remove Redundant <thinking> Block Instructions from PDCA Playbooks.

AC1: No thinking instructions in commands.py
AC2: No thinking instructions in workflows.py
AC3: Phase 0 sections preserved with numbered steps
AC4: test_design_command.py test updated (verified by running that test)
AC5: All existing tests pass (verified by regression)
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


THINKING_INSTRUCTION = '> **INSTRUCTION**: Output a `<thinking>` block'


# --- AC1: No thinking instructions in commands.py ---

class TestNoThinkingInCommands:
    """commands.py COMMANDS_CONTENT must not contain thinking instructions."""

    def test_no_thinking_instruction_in_any_command(self):
        """No command playbook should have a thinking instruction line."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        for name, content in COMMANDS_CONTENT.items():
            assert THINKING_INSTRUCTION not in content, (
                f"Found thinking instruction in COMMANDS_CONTENT['{name}']"
            )

    def test_plan_no_thinking(self):
        """project-plan.md must not have thinking instruction."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        assert THINKING_INSTRUCTION not in COMMANDS_CONTENT["project-plan.md"]

    def test_check_no_thinking(self):
        """project-check.md must not have thinking instruction."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        assert THINKING_INSTRUCTION not in COMMANDS_CONTENT["project-check.md"]

    def test_done_no_thinking(self):
        """project-done.md must not have thinking instruction."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        assert THINKING_INSTRUCTION not in COMMANDS_CONTENT["project-done.md"]

    def test_init_no_thinking(self):
        """project-init.md must not have thinking instruction."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        assert THINKING_INSTRUCTION not in COMMANDS_CONTENT["project-init.md"]


# --- AC2: No thinking instructions in workflows.py ---

class TestNoThinkingInWorkflows:
    """Workflow prompts must not contain thinking instructions."""

    def test_no_thinking_in_trace(self):
        from pactkit.prompts.workflows import TRACE_PROMPT
        assert THINKING_INSTRUCTION not in TRACE_PROMPT

    def test_no_thinking_in_draw(self):
        from pactkit.prompts.workflows import DRAW_PROMPT_TEMPLATE
        assert THINKING_INSTRUCTION not in DRAW_PROMPT_TEMPLATE

    def test_no_thinking_in_sprint(self):
        from pactkit.prompts.workflows import SPRINT_PROMPT
        assert THINKING_INSTRUCTION not in SPRINT_PROMPT

    def test_no_thinking_in_review(self):
        from pactkit.prompts.workflows import REVIEW_PROMPT
        assert THINKING_INSTRUCTION not in REVIEW_PROMPT

    def test_no_thinking_in_hotfix(self):
        from pactkit.prompts.workflows import HOTFIX_PROMPT
        assert THINKING_INSTRUCTION not in HOTFIX_PROMPT

    def test_no_thinking_in_design(self):
        from pactkit.prompts.workflows import DESIGN_PROMPT
        assert THINKING_INSTRUCTION not in DESIGN_PROMPT


# --- AC3: Phase 0 sections preserved ---

class TestPhase0Preserved:
    """Phase 0 sections must still exist with numbered analysis steps."""

    def test_commands_phase0_preserved(self):
        """Each command with Phase 0 must still have numbered steps."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        commands_with_phase0 = [
            "project-plan.md", "project-check.md",
            "project-done.md", "project-init.md",
        ]
        for name in commands_with_phase0:
            content = COMMANDS_CONTENT[name]
            assert 'Phase 0' in content, f"Phase 0 missing in {name}"
            assert '1.' in content, f"Numbered steps missing in {name}"

    def test_workflows_phase0_preserved(self):
        """Each workflow with Phase 0 must still have content after the header."""
        from pactkit.prompts import workflows
        workflow_names = [
            'TRACE_PROMPT', 'DRAW_PROMPT_TEMPLATE', 'SPRINT_PROMPT',
            'REVIEW_PROMPT', 'HOTFIX_PROMPT', 'DESIGN_PROMPT',
        ]
        for name in workflow_names:
            content = getattr(workflows, name)
            assert 'Phase 0' in content, f"Phase 0 missing in {name}"
