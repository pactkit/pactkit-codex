"""Tests for STORY-004: Convert 11 Command Playbooks to Codex Prompts."""


import pytest
import yaml


@pytest.fixture
def prompts_dir(tmp_path):
    """Temporary prompts directory."""
    d = tmp_path / "prompts"
    d.mkdir()
    return d


EXPECTED_FILES = [
    "project-init.md",
    "project-plan.md",
    "project-act.md",
    "project-check.md",
    "project-done.md",
    "project-hotfix.md",
    "project-design.md",
    "project-clarify.md",
    "project-release.md",
    "project-pr.md",
    # project-sprint.md excluded — requires multi-agent (BUG-002)
]

ARGUMENT_COMMANDS = {"project-act", "project-check", "project-done", "project-hotfix", "project-clarify"}


class TestCodexPrompts:
    """AC1-AC7: Convert command playbooks to Codex prompts."""

    def _deploy(self, prompts_dir):
        """Helper to deploy prompts."""
        from pactkit.generators.deployer import _deploy_codex_prompts
        from pactkit.profiles import get_profile

        profile = get_profile("codex")
        return _deploy_codex_prompts(prompts_dir, profile)

    def test_ac1_all_10_files_present(self, prompts_dir):
        """AC1: All 10 prompt files are present (sprint excluded)."""
        count = self._deploy(prompts_dir)
        assert count == 10
        for filename in EXPECTED_FILES:
            assert (prompts_dir / filename).exists(), f"Missing: {filename}"

    def test_ac1_only_expected_files(self, prompts_dir):
        """AC1: No extra files beyond the 10."""
        self._deploy(prompts_dir)
        files = sorted(f.name for f in prompts_dir.glob("*.md"))
        assert files == sorted(EXPECTED_FILES)

    def test_ac2_frontmatter_codex_compatible(self, prompts_dir):
        """AC2: description present, no allowed-tools, argument-hint where needed."""
        self._deploy(prompts_dir)
        for filename in EXPECTED_FILES:
            content = (prompts_dir / filename).read_text()
            assert content.startswith("---"), f"{filename} missing frontmatter"
            # Parse frontmatter
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{filename} malformed frontmatter"
            fm = yaml.safe_load(parts[1])
            assert "description" in fm, f"{filename} missing description"
            assert "allowed-tools" not in fm, f"{filename} has allowed-tools"

            cmd = filename.removesuffix(".md")
            if cmd in ARGUMENT_COMMANDS:
                assert "argument-hint" in fm, f"{filename} missing argument-hint"

    def test_ac3_no_claude_paths(self, prompts_dir):
        """AC3: No ~/.claude/ paths remain."""
        self._deploy(prompts_dir)
        for filename in EXPECTED_FILES:
            content = (prompts_dir / filename).read_text()
            assert "~/.claude/" not in content, f"{filename} contains ~/.claude/"

    def test_ac4_no_anthropic_model_names(self, prompts_dir):
        """AC4: No Anthropic model names remain."""
        self._deploy(prompts_dir)
        for filename in EXPECTED_FILES:
            content = (prompts_dir / filename).read_text()
            content_lower = content.lower()
            # Check for claude model patterns, but skip the word "claude" when
            # it's part of file names like "CLAUDE.md" or "CLAUDE.local.md"
            assert "claude-sonnet" not in content_lower, f"{filename} has claude-sonnet"
            assert "claude-haiku" not in content_lower, f"{filename} has claude-haiku"
            assert "claude-opus" not in content_lower, f"{filename} has claude-opus"

    def test_ac5_skills_paths_codex(self, prompts_dir):
        """AC5: Skills paths point to Codex location."""
        self._deploy(prompts_dir)
        for filename in EXPECTED_FILES:
            content = (prompts_dir / filename).read_text()
            if "~/.claude/skills/" in content:
                pytest.fail(f"{filename} still has ~/.claude/skills/")

    def test_ac6_no_allowed_tools_anywhere(self, prompts_dir):
        """AC6: No allowed-tools field in any file."""
        self._deploy(prompts_dir)
        all_content = ""
        for filename in EXPECTED_FILES:
            all_content += (prompts_dir / filename).read_text()
        assert "allowed-tools:" not in all_content

    def test_ac7_no_multiagent_spawning(self, prompts_dir):
        """AC7: No multi-agent spawning syntax."""
        self._deploy(prompts_dir)
        for filename in EXPECTED_FILES:
            content = (prompts_dir / filename).read_text()
            assert "Agent(model=" not in content, f"{filename} has Agent(model="
