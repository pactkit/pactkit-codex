"""Tests for BUG-017: /project-init playbook generates complete pactkit.yaml."""
from pactkit.prompts.commands import COMMANDS_CONTENT


class TestProjectInitPlaybook:
    """Test /project-init playbook content."""

    def test_playbook_exists(self):
        """Playbook should exist in COMMANDS_CONTENT."""
        assert "project-init.md" in COMMANDS_CONTENT

    def test_playbook_instructs_pactkit_init_cli(self):
        """Playbook should instruct to run pactkit init CLI, not manual yaml creation."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Should reference pactkit init or pactkit update CLI
        assert "pactkit init" in content or "pactkit update" in content
        # Should NOT have the old manual creation instruction
        assert "Content*: `stack: <detected>`, `version: 0.0.1`, `root: .`" not in content

    def test_playbook_checks_cli_availability(self):
        """Playbook should check if pactkit CLI is available."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Should have CLI availability check
        assert "pactkit version" in content or "command -v pactkit" in content

    def test_playbook_has_fallback_for_missing_cli(self):
        """Playbook should provide fallback when CLI is unavailable."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Should warn about missing CLI
        assert "pip install pactkit" in content

    def test_playbook_still_creates_project_claude_md(self):
        """Playbook should create CLAUDE.md (Claude Code) or AGENTS.md (OpenCode) (STORY-073)."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Should have conditional instruction for project instructions file
        assert ".claude/CLAUDE.md" in content
        assert "Project Instructions File" in content

    def test_playbook_uses_pactkit_update_for_existing_config(self):
        """Playbook should use pactkit update when config already exists."""
        content = COMMANDS_CONTENT["project-init.md"]
        # Should reference pactkit update for existing configs
        assert "pactkit update" in content
