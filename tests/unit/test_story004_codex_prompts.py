"""Tests for STORY-004: Deploy PDCA Commands as Codex Skills.

Tests that deploy_codex_command_skills() creates all command skill dirs,
each with a SKILL.md containing @~/.codex/rules/ references, no Claude
paths, and no Anthropic model names.
"""

import pytest


@pytest.fixture
def skills_dir(tmp_path):
    """Temporary skills directory."""
    d = tmp_path / "skills"
    d.mkdir()
    return d


EXPECTED_COMMANDS = [
    "project-init",
    "project-plan",
    "project-act",
    "project-check",
    "project-done",
    "project-hotfix",
    "project-design",
    "project-clarify",
    "project-release",
    "project-pr",
    "project-debug",
    "project-sprint",
]

ARGUMENT_COMMANDS = {"project-act", "project-check", "project-done", "project-hotfix", "project-clarify"}


class TestCodexCommandSkills:
    """AC1-AC7: Deploy command playbooks as Codex skill dirs."""

    def _deploy(self, skills_dir):
        """Helper to deploy command skills."""
        from pactkit_codex.deployer import CodexDeployer
        from pactkit.profiles import get_profile

        profile = get_profile("codex")
        return CodexDeployer.deploy_codex_command_skills(skills_dir, profile)

    def test_ac1_all_12_skill_dirs_present(self, skills_dir):
        """AC1: All canonical command skill dirs are present."""
        count = self._deploy(skills_dir)
        assert count == 12
        for cmd in EXPECTED_COMMANDS:
            assert (skills_dir / cmd).is_dir(), f"Missing skill dir: {cmd}"

    def test_ac1_only_expected_dirs(self, skills_dir):
        """AC1: No extra command dirs beyond the canonical 12."""
        self._deploy(skills_dir)
        dirs = sorted(d.name for d in skills_dir.iterdir() if d.is_dir())
        assert dirs == sorted(EXPECTED_COMMANDS)

    def test_ac1_each_dir_has_skill_md(self, skills_dir):
        """AC1: Every command skill dir has a SKILL.md file."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            assert (skills_dir / cmd / "SKILL.md").is_file(), f"{cmd}/SKILL.md missing"

    def test_ac2_rules_references_present(self, skills_dir):
        """AC2: Each SKILL.md has @~/.codex/rules/ references at the top."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            assert "@~/.codex/rules/" in content, f"{cmd}/SKILL.md missing @~/.codex/rules/ references"

    def test_ac3_no_claude_paths(self, skills_dir):
        """AC3: No ~/.claude/ paths remain."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            assert "~/.claude/" not in content, f"{cmd}/SKILL.md contains ~/.claude/"

    def test_ac4_no_anthropic_model_names(self, skills_dir):
        """AC4: No Anthropic model names remain."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            content_lower = content.lower()
            assert "claude-sonnet" not in content_lower, f"{cmd}/SKILL.md has claude-sonnet"
            assert "claude-haiku" not in content_lower, f"{cmd}/SKILL.md has claude-haiku"
            assert "claude-opus" not in content_lower, f"{cmd}/SKILL.md has claude-opus"

    def test_ac5_codex_paths_in_skills(self, skills_dir):
        """AC5: Skills paths point to Codex location (~/.codex/)."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            if "~/.claude/skills/" in content:
                pytest.fail(f"{cmd}/SKILL.md still has ~/.claude/skills/")

    def test_ac6_no_allowed_tools_anywhere(self, skills_dir):
        """AC6: No allowed-tools field in any SKILL.md file."""
        self._deploy(skills_dir)
        all_content = ""
        for cmd in EXPECTED_COMMANDS:
            all_content += (skills_dir / cmd / "SKILL.md").read_text()
        assert "allowed-tools:" not in all_content

    def test_ac7_no_multiagent_spawning(self, skills_dir):
        """AC7: No multi-agent spawning syntax."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            assert "Agent(model=" not in content, f"{cmd}/SKILL.md has Agent(model="

    def test_credential_rule_in_every_command(self, skills_dir):
        """Each command SKILL.md references the credential safety rule."""
        self._deploy(skills_dir)
        for cmd in EXPECTED_COMMANDS:
            content = (skills_dir / cmd / "SKILL.md").read_text()
            assert "09-credential-safety.md" in content, (
                f"{cmd}/SKILL.md missing credential safety rule reference"
            )
