"""
STORY-069: OpenCode Deployment Format Support
Tests for `pactkit init --format opencode` deployment mode.
"""

import json
from unittest.mock import patch

from pactkit.config import VALID_AGENTS, VALID_COMMANDS, VALID_SKILLS
from pactkit.generators.deployer import VALID_FORMATS, deploy

# ===========================================================================
# R1: New --format opencode deployment mode
# ===========================================================================


class TestR1OpenCodeFormatExists:
    """R1: --format opencode mode MUST be available."""

    def test_opencode_in_valid_formats(self):
        """'opencode' is in VALID_FORMATS."""
        assert "opencode" in VALID_FORMATS

    def test_deploy_accepts_opencode_format(self, tmp_path):
        """deploy(format='opencode') does not raise."""
        out = tmp_path / "opencode-test"
        deploy(format="opencode", target=str(out))
        assert out.exists()


# ===========================================================================
# R2: Global deployment — ~/.config/opencode/
# ===========================================================================


class TestR2GlobalDeployment:
    """R2: Global deployment writes correct directory structure."""

    def test_agents_md_exists(self, tmp_path):
        """AGENTS.md is created."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        assert (out / "AGENTS.md").is_file()

    def test_agents_dir_exists(self, tmp_path):
        """agents/ directory is created."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        assert (out / "agents").is_dir()

    def test_commands_dir_exists(self, tmp_path):
        """commands/ directory is created."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        assert (out / "commands").is_dir()

    def test_skills_dir_exists(self, tmp_path):
        """skills/ directory is created."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        assert (out / "skills").is_dir()

    def test_all_agents_deployed(self, tmp_path):
        """All agents are deployed."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        agents_dir = out / "agents"
        deployed = {f.stem for f in agents_dir.glob("*.md")}
        assert deployed == VALID_AGENTS

    def test_all_commands_deployed(self, tmp_path):
        """All commands are deployed."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        commands_dir = out / "commands"
        deployed = {f.stem for f in commands_dir.glob("*.md")}
        assert deployed == VALID_COMMANDS

    def test_all_skills_deployed(self, tmp_path):
        """All skills are deployed."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        skills_dir = out / "skills"
        deployed = {d.name for d in skills_dir.iterdir() if d.is_dir()}
        assert deployed == VALID_SKILLS


# ===========================================================================
# R3: Project-level deployment — via /project-init (BUG-035)
# ===========================================================================


class TestR3ProjectDeployment:
    """R3: Global deployment creates opencode.json with instructions (STORY-071 R7).

    Note: Previously (BUG-035), opencode.json was NOT created by global deployment.
    STORY-071 R7 changed this: global deployment now creates opencode.json with
    instructions: ["rules/*.md"] for modular rule loading.
    """

    def test_opencode_json_at_global(self, tmp_path):
        """opencode.json IS created by global deployment (STORY-071 R7)."""
        out = tmp_path / "project"
        deploy(format="opencode", target=str(out))
        assert (out / "opencode.json").is_file()


# ===========================================================================
# R7: Agent tools format conversion (STORY-069 R7)
# ===========================================================================


class TestR7AgentToolsFormat:
    """R7: Agent tools converted to OpenCode record format."""

    def test_agent_tools_is_record(self, tmp_path):
        """Agent tools should be record format, not string."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        agent_content = (out / "agents" / "system-architect.md").read_text()
        # Should NOT have "tools: Read, Write" string format
        assert "tools: Read" not in agent_content
        assert "tools: [" not in agent_content
        # Should have record format with indented keys
        assert "tools:" in agent_content
        assert "read: true" in agent_content or "write: true" in agent_content


# ===========================================================================
# R4: AGENTS.md with inline rules
# ===========================================================================


class TestR4AgentsMdInlineRules:
    """R4: AGENTS.md is slim header, rules loaded via instructions (STORY-071 R6)."""

    def test_agents_md_no_at_import(self, tmp_path):
        """AGENTS.md does not contain @~/.claude/ references."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        content = (out / "AGENTS.md").read_text()
        assert "@~/.claude/" not in content
        assert "@~/.config/opencode/" not in content

    def test_agents_md_has_pactkit_header(self, tmp_path):
        """AGENTS.md contains PactKit header (slim version)."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        content = (out / "AGENTS.md").read_text()
        assert "PactKit" in content

    def test_rules_in_separate_files(self, tmp_path):
        """Core Protocol and Hierarchy of Truth are in rules/ directory."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        rules_dir = out / "rules"
        assert rules_dir.is_dir()
        # Check core protocol exists in rules/
        rule_files = {f.name for f in rules_dir.glob("*.md")}
        assert "01-core-protocol.md" in rule_files
        assert "02-hierarchy-of-truth.md" in rule_files


# ===========================================================================
# R5: Skills path rewriting
# ===========================================================================


class TestR5SkillsPathRewriting:
    """R5: Skills paths rewritten to ~/.config/opencode/skills."""

    def test_skill_md_uses_opencode_path(self, tmp_path):
        """SKILL.md references use ~/.config/opencode/skills."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        # Check any scripted skill
        skill_md = out / "skills" / "pactkit-visualize" / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            assert "~/.claude/skills" not in content
            # Path should be rewritten to opencode
            assert "~/.config/opencode/skills" in content or "${OPENCODE_ROOT}/skills" in content

    def test_agents_md_uses_opencode_path(self, tmp_path):
        """AGENTS.md skill references use opencode paths."""
        out = tmp_path / "opencode"
        deploy(format="opencode", target=str(out))
        content = (out / "AGENTS.md").read_text()
        assert "~/.claude/skills" not in content


# ===========================================================================
# R6: opencode.json generation (via helper, for /project-init use)
# ===========================================================================


class TestR6OpenCodeJsonGeneration:
    """R6: opencode.json helper has correct structure (BUG-035: project-level file)."""

    def test_opencode_json_has_schema(self, tmp_path):
        """opencode.json contains $schema field."""
        from pactkit.generators.deployer import _deploy_opencode_json

        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "$schema" in data
        assert "opencode.ai" in data["$schema"]

    def test_opencode_json_has_instructions(self, tmp_path):
        """opencode.json contains instructions field."""
        from pactkit.generators.deployer import _deploy_opencode_json

        _deploy_opencode_json(tmp_path)
        data = json.loads((tmp_path / "opencode.json").read_text())
        assert "instructions" in data
        assert isinstance(data["instructions"], list)

    def test_opencode_json_no_api_key(self, tmp_path):
        """opencode.json does NOT contain apiKey or provider secrets."""
        from pactkit.generators.deployer import _deploy_opencode_json

        _deploy_opencode_json(tmp_path)
        content = (tmp_path / "opencode.json").read_text()
        assert "apiKey" not in content
        assert "api_key" not in content
        assert "API_KEY" not in content


# ===========================================================================
# R11: CLI --format opencode
# ===========================================================================


class TestR11CliFormatOpenCode:
    """R11: CLI --format includes opencode option."""

    def test_cli_format_opencode(self, tmp_path):
        """pactkit init --format opencode works via CLI (STORY-071: creates opencode.json)."""
        from pactkit.cli import main

        out = tmp_path / "cli-out"
        with patch("sys.argv", ["pactkit", "init", "--format", "opencode", "-t", str(out)]):
            main()
        assert (out / "AGENTS.md").is_file()
        # STORY-071 R7: opencode.json IS created with instructions
        assert (out / "opencode.json").is_file()
