"""E2E tests for STORY-008: End-to-End Verification of Codex CLI Deployment.

Tests R1 (artifact creation), R4 (skill execution), R5 (TOML validity),
R7 (no leaked refs). Interactive tests (R2, R3, R6) require manual
verification in a live Codex CLI session.
"""

import subprocess
import sys
import tomllib

import pytest


@pytest.fixture()
def codex_deploy(tmp_path):
    """Deploy full Codex artifacts to a temp directory."""
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer().deploy(target=str(tmp_path))
    return tmp_path


class TestAC1ArtifactCreation:
    """AC1/R1: pactkit init --format codex creates all expected artifacts."""

    def test_agents_md_exists(self, codex_deploy):
        assert (codex_deploy / "AGENTS.md").is_file()

    def test_config_toml_exists(self, codex_deploy):
        assert (codex_deploy / "config.toml").is_file()

    def test_board_script_exists(self, codex_deploy):
        assert (codex_deploy / "skills/pactkit-board/scripts/board.py").is_file()

    def test_scaffold_script_exists(self, codex_deploy):
        assert (codex_deploy / "skills/pactkit-scaffold/scripts/scaffold.py").is_file()

    def test_visualize_script_exists(self, codex_deploy):
        assert (codex_deploy / "skills/pactkit-visualize/scripts/visualize.py").is_file()

    def test_20_skill_dirs(self, codex_deploy):
        """R1: 24 skill directories under skills/ (13 embedded + 11 PDCA commands, sprint excluded)."""
        skill_dirs = [d for d in (codex_deploy / "skills").iterdir() if d.is_dir()]
        assert len(skill_dirs) == 24, (
            f"Expected 24 skill dirs, got {len(skill_dirs)}: {[d.name for d in skill_dirs]}"
        )

    def test_10_command_skill_dirs(self, codex_deploy):
        """R1: 11 PDCA command skill directories (sprint excluded)."""
        expected_commands = {
            "project-init", "project-plan", "project-act",
            "project-check", "project-done", "project-release",
            "project-pr", "project-hotfix", "project-design", "project-clarify",
            "project-debug",
        }
        skill_dirs = {d.name for d in (codex_deploy / "skills").iterdir() if d.is_dir()}
        for cmd in expected_commands:
            assert cmd in skill_dirs, f"Missing command skill dir: {cmd}"

    def test_no_prompts_directory(self, codex_deploy):
        """R1: Legacy prompts/ directory is cleaned up — commands are now skills."""
        assert not (codex_deploy / "prompts").exists(), "Legacy prompts/ directory should not exist"

    def test_each_skill_has_skill_md(self, codex_deploy):
        """R1: Every skill directory has a SKILL.md file."""
        for skill_dir in (codex_deploy / "skills").iterdir():
            if skill_dir.is_dir():
                assert (skill_dir / "SKILL.md").is_file(), f"{skill_dir.name} missing SKILL.md"


class TestAC2NoLeakedRefs:
    """AC2/R7: No ~/.claude/ or Anthropic model references in deployed files."""

    def test_no_claude_paths(self, codex_deploy):
        """grep -r '~/.claude/' returns no matches."""
        for f in codex_deploy.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".toml", ".py", ".txt"):
                content = f.read_text(errors="replace")
                assert "~/.claude/" not in content, f"{f.relative_to(codex_deploy)} contains ~/.claude/"

    def test_no_anthropic_model_names(self, codex_deploy):
        """grep for claude-sonnet/haiku/opus returns no matches."""
        for f in codex_deploy.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".toml", ".py", ".txt"):
                content = f.read_text(errors="replace").lower()
                assert "claude-sonnet" not in content, f"{f.relative_to(codex_deploy)} has claude-sonnet"
                assert "claude-haiku" not in content, f"{f.relative_to(codex_deploy)} has claude-haiku"
                assert "claude-opus" not in content, f"{f.relative_to(codex_deploy)} has claude-opus"

    def test_no_opencode_paths(self, codex_deploy):
        """No ~/.config/opencode/ in deployed files."""
        for f in codex_deploy.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".toml", ".py", ".txt"):
                content = f.read_text(errors="replace")
                assert "~/.config/opencode/" not in content, (
                    f"{f.relative_to(codex_deploy)} contains ~/.config/opencode/"
                )


class TestR5ConfigToml:
    """R5: config.toml is valid TOML and has expected structure."""

    def test_valid_toml(self, codex_deploy):
        """config.toml parses without error."""
        with open(codex_deploy / "config.toml", "rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict)

    def test_has_mcp_section(self, codex_deploy):
        """config.toml includes MCP server entries."""
        with open(codex_deploy / "config.toml", "rb") as f:
            data = tomllib.load(f)
        assert "mcp" in data or "mcp_servers" in data or any(
            "context7" in str(v) for v in data.values()
        ), "No MCP configuration found in config.toml"


class TestAC5SkillExecution:
    """AC5/R4: board.py executes under subprocess (simulates sandbox)."""

    def test_board_help_exits_zero(self, codex_deploy):
        """board.py --help exits with code 0."""
        board_script = codex_deploy / "skills/pactkit-board/scripts/board.py"
        result = subprocess.run(
            [sys.executable, str(board_script), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"board.py --help failed: {result.stderr}"

    def test_board_help_prints_usage(self, codex_deploy):
        """board.py --help prints recognizable usage text."""
        board_script = codex_deploy / "skills/pactkit-board/scripts/board.py"
        result = subprocess.run(
            [sys.executable, str(board_script), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        assert "usage" in output.lower() or "board" in output.lower(), (
            f"board.py --help did not print usage: {output[:200]}"
        )


class TestCommandSkillIntegrity:
    """Additional integrity checks on deployed command skills."""

    def test_all_10_commands_present_as_skills(self, codex_deploy):
        """All 10 PactKit commands are deployed as skills/ dirs (sprint excluded)."""
        expected = {
            "project-init", "project-plan", "project-act",
            "project-check", "project-done", "project-release",
            "project-pr", "project-hotfix",
            "project-design", "project-clarify",
        }
        skill_dirs = {d.name for d in (codex_deploy / "skills").iterdir() if d.is_dir()}
        assert expected.issubset(skill_dirs), (
            f"Missing command skills: {expected - skill_dirs}"
        )

    def test_sprint_not_in_skills(self, codex_deploy):
        """project-sprint must not be deployed as a skill."""
        assert not (codex_deploy / "skills" / "project-sprint").exists()

    def test_command_skills_have_skill_md(self, codex_deploy):
        """Each command skill directory has a SKILL.md file."""
        expected_commands = {
            "project-init", "project-plan", "project-act",
            "project-check", "project-done", "project-release",
            "project-pr", "project-hotfix", "project-design", "project-clarify",
        }
        for cmd in expected_commands:
            skill_md = codex_deploy / "skills" / cmd / "SKILL.md"
            assert skill_md.is_file(), f"{cmd}/SKILL.md missing"

    def test_command_skills_have_rules_references(self, codex_deploy):
        """Each command SKILL.md has @~/.codex/rules/ references at the top."""
        expected_commands = {
            "project-init", "project-plan", "project-act",
            "project-check", "project-done", "project-release",
            "project-pr", "project-hotfix", "project-design", "project-clarify",
        }
        for cmd in expected_commands:
            skill_md = codex_deploy / "skills" / cmd / "SKILL.md"
            content = skill_md.read_text()
            assert "@~/.codex/rules/" in content, f"{cmd}/SKILL.md missing @~/.codex/rules/ references"

    def test_agents_md_under_20kb(self, codex_deploy):
        """AGENTS.md must be under 20KB budget."""
        agents = codex_deploy / "AGENTS.md"
        size = agents.stat().st_size
        assert size < 20 * 1024, f"AGENTS.md is {size} bytes (>{20*1024})"
