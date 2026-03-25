"""
STORY-070: OpenCode Format Compliance — Fix Spec-Implementation Gaps
Tests for OpenCode-native agent/command format conversion.
"""

import re  # noqa: I001
from unittest.mock import patch

from pactkit.generators.deployer import deploy


# ===========================================================================
# AC1: Command frontmatter conversion
# ===========================================================================


class TestAC1CommandFrontmatter:
    """AC1: Commands use OpenCode frontmatter (agent: build, no allowed-tools)."""

    def _extract_frontmatter(self, content):
        """Extract YAML frontmatter from content that may have rule headers.

        STORY-slim-011: OpenCode commands have inline rule content before the
        --- frontmatter block. Find the --- block containing 'description:'.
        """
        import re
        matches = list(re.finditer(r'---\n(.*?)\n---', content, re.DOTALL))
        assert matches, f"No frontmatter found in content starting with: {content[:80]}"
        for m in matches:
            if "description:" in m.group(1):
                return m.group(1)
        return matches[-1].group(1)

    def test_command_has_agent_build(self, tmp_path):
        """Command frontmatter contains 'agent: build'."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "commands" / "project-plan.md").read_text()
        frontmatter = self._extract_frontmatter(content)
        assert "agent: build" in frontmatter

    def test_command_no_allowed_tools(self, tmp_path):
        """Command frontmatter does NOT contain 'allowed-tools'."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "commands" / "project-plan.md").read_text()
        frontmatter = self._extract_frontmatter(content)
        assert "allowed-tools" not in frontmatter

    def test_all_commands_converted(self, tmp_path):
        """All command files use OpenCode frontmatter."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        commands_dir = out / "commands"
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            frontmatter = self._extract_frontmatter(content)
            assert "allowed-tools" not in frontmatter, f"{cmd_file.name} still has allowed-tools"
            assert "agent: build" in frontmatter, f"{cmd_file.name} missing agent: build"

    def test_command_body_preserved(self, tmp_path):
        """Command body content is preserved after frontmatter conversion."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "commands" / "project-plan.md").read_text()
        # Body should still contain the command content
        assert "# Command: Plan" in content

    def test_classic_format_unchanged(self, tmp_path):
        """Classic format still uses allowed-tools (not converted)."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "commands" / "project-plan.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        assert "allowed-tools" in frontmatter


# ===========================================================================
# AC2: Agent mode: subagent and no name field
# ===========================================================================


class TestAC2AgentMode:
    """AC2: Agent files have mode: subagent and no name field."""

    def test_agent_has_mode_subagent(self, tmp_path):
        """Agent frontmatter contains 'mode: subagent'."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        assert "mode: subagent" in frontmatter

    def test_agent_no_name_field(self, tmp_path):
        """Agent frontmatter does NOT contain 'name:' field."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        # Check that there's no 'name:' line in frontmatter
        for line in frontmatter.strip().split("\n"):
            assert not line.strip().startswith("name:"), f"Found unexpected name field: {line}"

    def test_all_agents_have_mode(self, tmp_path):
        """All agent files have mode: subagent."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        agents_dir = out / "agents"
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            parts = content.split("---", 2)
            frontmatter = parts[1]
            assert "mode: subagent" in frontmatter, f"{agent_file.name} missing mode: subagent"

    def test_classic_format_keeps_name(self, tmp_path):
        """Classic format still includes name field (not converted)."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        assert "name: system-architect" in frontmatter


# ===========================================================================
# AC3: Agent Claude Code fields cleaned
# ===========================================================================


class TestAC3AgentFieldCleanup:
    """AC3: Claude Code-specific fields removed in OpenCode format."""

    def test_no_permission_mode(self, tmp_path):
        """Agent frontmatter does NOT contain permissionMode."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        assert "permissionMode" not in frontmatter

    def test_no_memory_field(self, tmp_path):
        """Agent frontmatter does NOT contain memory field."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        # 'memory' should not appear as a frontmatter key
        for line in frontmatter.strip().split("\n"):
            assert not line.strip().startswith("memory:"), f"Found unexpected memory field: {line}"

    def test_no_skills_field(self, tmp_path):
        """Agent frontmatter does NOT contain skills field."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        for line in frontmatter.strip().split("\n"):
            assert not line.strip().startswith("skills:"), f"Found unexpected skills field: {line}"

    def test_all_agents_cleaned(self, tmp_path):
        """All agent files have Claude Code fields removed."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        agents_dir = out / "agents"
        claude_fields = ["permissionMode", "memory:", "skills:"]
        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            parts = content.split("---", 2)
            frontmatter = parts[1]
            for field in claude_fields:
                # Check each line to avoid false positives from body content
                for line in frontmatter.strip().split("\n"):
                    stripped = line.strip()
                    if field.endswith(":"):
                        assert not stripped.startswith(field), f"{agent_file.name} has {field} in frontmatter"
                    else:
                        assert field not in stripped, f"{agent_file.name} has {field} in frontmatter"


# ===========================================================================
# AC4: Agent model inherit omitted
# ===========================================================================


class TestAC4AgentModelInherit:
    """AC4: model field omitted when value is 'inherit'."""

    def test_no_model_inherit(self, tmp_path):
        """Agent frontmatter does NOT contain 'model: inherit'."""
        out = tmp_path / "oc"
        deploy(format="opencode", target=str(out))
        # Default pactkit.yaml has agent_models, but without config override,
        # deploy uses all defaults which resolve to 'inherit'
        content = (out / "agents" / "system-architect.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        assert "model: inherit" not in frontmatter


# ===========================================================================
# AC5: upgrade command supports opencode
# ===========================================================================


class TestAC5UpgradeOpenCode:
    """AC5: pactkit upgrade --format opencode works."""

    def test_upgrade_accepts_opencode(self, tmp_path):
        """pactkit upgrade --format opencode deploys successfully."""
        from pactkit.cli import main

        out = tmp_path / "upgrade-out"
        with patch("sys.argv", ["pactkit", "upgrade", "--format", "opencode", "-t", str(out)]):
            main()
        assert (out / "AGENTS.md").is_file()
        assert (out / "agents").is_dir()


# ===========================================================================
# AC6: No regression in classic format
# ===========================================================================


class TestAC6ClassicRegression:
    """AC6: Classic format behavior unchanged."""

    def test_classic_agents_have_name(self, tmp_path):
        """Classic agents still have name field."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "agents" / "senior-developer.md").read_text()
        assert "name: senior-developer" in content

    def test_classic_commands_have_allowed_tools(self, tmp_path):
        """Classic commands still have allowed-tools."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "commands" / "project-act.md").read_text()
        assert "allowed-tools" in content

    def test_classic_agents_have_simple_tools(self, tmp_path):
        """Classic agents still use string tools format."""
        out = tmp_path / "classic"
        deploy(format="classic", target=str(out))
        content = (out / "agents" / "senior-developer.md").read_text()
        parts = content.split("---", 2)
        frontmatter = parts[1]
        # Classic should have tools as string, not record
        assert "tools: Read" in frontmatter or "tools: [" in frontmatter or re.search(r"tools:.*Read", frontmatter)
