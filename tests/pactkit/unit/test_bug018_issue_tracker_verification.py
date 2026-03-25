"""Tests for BUG-018: Issue Tracker verification in Done command.

AC5: Prompt template contains verification step before closure.
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestAC5PromptTemplateContainsVerification:
    """AC5: Done command template contains verification step."""

    def test_done_command_has_phase_355(self):
        """Done command has Phase 3.5.5 verification step."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'Phase 3.5.5' in done_content or '3.5.5' in done_content

    def test_verification_step_before_closure(self):
        """Verification step appears before closure step."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        # Find positions
        verification_pos = done_content.find('Issue Tracker Verification')
        closure_pos = done_content.find('Issue Tracker Closure')
        assert verification_pos != -1, "Verification step not found"
        assert closure_pos != -1, "Closure step not found"
        assert verification_pos < closure_pos, "Verification must come before closure"

    def test_verification_includes_gh_issue_list_search(self):
        """Verification step includes gh issue list --search instruction."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'gh issue list' in done_content
        assert '--search' in done_content or 'search' in done_content.lower()

    def test_verification_includes_backfill_creation(self):
        """Verification step includes backfill issue creation logic."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        # Should mention creating an issue if not found
        assert 'gh issue create' in done_content
        assert 'backfill' in done_content.lower() or 'Backfill' in done_content

    def test_verification_includes_board_update(self):
        """Verification step includes Sprint Board update instruction."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        # Should mention updating board with issue link
        assert 'Sprint Board' in done_content
        assert 'issue link' in done_content.lower() or 'issue URL' in done_content

    def test_verification_checks_provider_config(self):
        """Verification step checks issue_tracker.provider config."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        # Find the verification section
        verification_start = done_content.find('Issue Tracker Verification')
        if verification_start != -1:
            # Check within the verification section
            verification_section = done_content[verification_start:verification_start + 1500]
            assert 'issue_tracker' in verification_section or 'provider' in verification_section

    def test_verification_handles_provider_none(self):
        """Verification step skips silently when provider is none."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        verification_start = done_content.find('Issue Tracker Verification')
        if verification_start != -1:
            verification_section = done_content[verification_start:verification_start + 1500]
            # Should mention skipping for none
            assert 'none' in verification_section.lower() or 'skip' in verification_section.lower()

    def test_verification_handles_cli_unavailable(self):
        """Verification step handles gh CLI unavailable gracefully."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        verification_start = done_content.find('Issue Tracker Verification')
        if verification_start != -1:
            verification_section = done_content[verification_start:verification_start + 1500]
            # Should mention warning and continue
            assert 'warning' in verification_section.lower() or 'unavailable' in verification_section.lower()
