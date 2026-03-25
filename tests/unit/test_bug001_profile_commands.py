"""Tests for BUG-001: Codex FormatProfile should mark has_custom_commands=True."""

from pactkit_codex.profiles import get_profile


class TestAC1ProfileMetadata:
    """AC1: Profile has correct commands metadata."""

    def test_has_custom_commands_true(self):
        profile = get_profile("codex")
        assert profile.has_custom_commands is True

    def test_commands_dir_is_prompts(self):
        profile = get_profile("codex")
        assert profile.commands_dir == "~/.codex/prompts"
