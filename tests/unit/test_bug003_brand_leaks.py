"""Tests for BUG-003: Claude/Anthropic brand references leak into Codex files."""

import pytest


@pytest.fixture()
def codex_deploy(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer().deploy(target=str(tmp_path))
    return tmp_path


class TestAC1AgentsMdClean:
    """AC1: AGENTS.md has zero Claude model names."""

    def test_no_claude_model_names_in_agents(self, codex_deploy):
        content = (codex_deploy / "AGENTS.md").read_text().lower()
        assert "claude-sonnet" not in content
        assert "claude-haiku" not in content
        assert "claude-opus" not in content


class TestAC2NoBrandInCommandSkills:
    """AC2: No Claude Code brand in command skill SKILL.md files."""

    def _command_skill_files(self, codex_deploy):
        """Yield SKILL.md files from command skill dirs (project-* dirs)."""
        for d in (codex_deploy / "skills").iterdir():
            if d.is_dir() and d.name.startswith("project-"):
                skill_md = d / "SKILL.md"
                if skill_md.exists():
                    yield skill_md

    def test_no_claude_code_brand(self, codex_deploy):
        for f in self._command_skill_files(codex_deploy):
            content = f.read_text()
            assert "Claude Code" not in content, f"{f.parent.name}/SKILL.md contains 'Claude Code'"

    def test_no_claude_com_url(self, codex_deploy):
        for f in self._command_skill_files(codex_deploy):
            content = f.read_text()
            assert "claude.com" not in content, f"{f.parent.name}/SKILL.md contains 'claude.com'"


class TestAC3FullTreeClean:
    """AC3: Full deployed tree is Claude-free."""

    def test_no_claude_brand_anywhere(self, codex_deploy):
        """Scan all deployed files for 'claude' (case-insensitive)."""
        for f in codex_deploy.rglob("*"):
            if not f.is_file() or f.suffix not in (".md", ".toml", ".py", ".txt"):
                continue
            content = f.read_text(errors="replace").lower()
            # Check for Claude brand references (not just path prefixes)
            assert "claude code" not in content, f"{f.relative_to(codex_deploy)} has 'Claude Code'"
            assert "claude.com" not in content, f"{f.relative_to(codex_deploy)} has 'claude.com'"
            assert "claude-sonnet" not in content, f"{f.relative_to(codex_deploy)} has 'claude-sonnet'"
            assert "claude-haiku" not in content, f"{f.relative_to(codex_deploy)} has 'claude-haiku'"
            assert "claude-opus" not in content, f"{f.relative_to(codex_deploy)} has 'claude-opus'"

    def test_no_anthropic_brand_anywhere(self, codex_deploy):
        """Scan all deployed .md files for 'Anthropic' brand (not in URLs)."""
        for f in codex_deploy.rglob("*.md"):
            if not f.is_file():
                continue
            content = f.read_text(errors="replace")
            # Check for standalone Anthropic brand (not part of technical refs)
            assert "Anthropic" not in content, f"{f.relative_to(codex_deploy)} has 'Anthropic'"
