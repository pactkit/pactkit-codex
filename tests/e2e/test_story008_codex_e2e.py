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

    def test_10_prompt_files(self, codex_deploy):
        """R1: One rendered command prompt per registered command (10 — sprint excluded)."""
        prompts = list((codex_deploy / "prompts").glob("*.md"))
        assert len(prompts) == 10, f"Expected 10 prompts, got {len(prompts)}: {[p.name for p in prompts]}"

    def test_10_skill_dirs(self, codex_deploy):
        """R1: 10 embedded skill directories under skills/ (PDCA commands deploy as playbooks, not skills)."""
        skill_dirs = [d for d in (codex_deploy / "skills").iterdir() if d.is_dir()]
        # Codex deploys only embedded skills (10), not PDCA command skills (11)
        # which go to playbooks/ instead. VALID_SKILLS includes both (21).
        assert len(skill_dirs) == 10

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


class TestPromptIntegrity:
    """Additional integrity checks on deployed prompts."""

    def test_all_10_commands_present(self, codex_deploy):
        """All 10 PactKit commands are deployed (sprint excluded)."""
        expected = {
            "project-init.md", "project-plan.md", "project-act.md",
            "project-check.md", "project-done.md", "project-release.md",
            "project-pr.md", "project-hotfix.md",
            "project-design.md", "project-clarify.md",
        }
        actual = {f.name for f in (codex_deploy / "prompts").glob("*.md")}
        assert actual == expected, f"Missing: {expected - actual}, Extra: {actual - expected}"

    def test_prompts_have_frontmatter(self, codex_deploy):
        """Each prompt file starts with YAML frontmatter."""
        for f in (codex_deploy / "prompts").glob("*.md"):
            content = f.read_text()
            assert content.startswith("---"), f"{f.name} missing frontmatter"
            # Must have closing ---
            second_fence = content.index("---", 3)
            assert second_fence > 3, f"{f.name} has no closing frontmatter fence"

    def test_prompts_no_allowed_tools(self, codex_deploy):
        """Codex prompts must not have allowed-tools (Claude-specific)."""
        for f in (codex_deploy / "prompts").glob("*.md"):
            content = f.read_text()
            assert "allowed-tools:" not in content, f"{f.name} still has allowed-tools"

    def test_agents_md_under_20kb(self, codex_deploy):
        """AGENTS.md must be under 20KB budget."""
        agents = codex_deploy / "AGENTS.md"
        size = agents.stat().st_size
        assert size < 20 * 1024, f"AGENTS.md is {size} bytes (>{20*1024})"
