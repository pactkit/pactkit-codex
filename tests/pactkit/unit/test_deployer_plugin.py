"""
STORY-005: Plugin Distribution — Claude Code Plugin format deployment
Tests for plugin and marketplace output modes in deployer.py
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pactkit.generators.deployer import deploy
from pactkit.prompts import AGENTS_EXPERT, COMMANDS_CONTENT
from pactkit.prompts.rules import RULES_FILES, RULES_MODULES

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_deploy_plugin(tmp_path):
    """Run deploy() in plugin format mode."""
    out = tmp_path / "pactkit-plugin"
    deploy(format="plugin", target=str(out))
    return out


def _run_deploy_marketplace(tmp_path):
    """Run deploy() in marketplace format mode."""
    out = tmp_path / "pactkit-marketplace"
    deploy(format="marketplace", target=str(out))
    return out


def _run_deploy_classic(tmp_path):
    """Run deploy() in classic format mode (default)."""
    out = tmp_path / ".claude"
    deploy(format="classic", target=str(out))
    return out


# ===========================================================================
# Scenario 1: Plugin directory generation
# ===========================================================================

class TestPluginDirectoryStructure:
    """Acceptance Criteria Scenario 1: Plugin 目录生成"""

    def test_plugin_json_exists(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        assert (out / ".claude-plugin" / "plugin.json").is_file()

    def test_claude_md_exists(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        assert (out / "CLAUDE.md").is_file()

    def test_all_agents_deployed(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        agents_dir = out / "agents"
        assert agents_dir.is_dir()
        for name in AGENTS_EXPERT:
            assert (agents_dir / f"{name}.md").is_file(), f"Missing agent: {name}"

    def test_all_commands_deployed(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        commands_dir = out / "commands"
        assert commands_dir.is_dir()
        for filename in COMMANDS_CONTENT:
            assert (commands_dir / filename).is_file(), f"Missing command: {filename}"

    def test_all_skills_deployed(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        skills_dir = out / "skills"
        for skill_name in ['pactkit-visualize', 'pactkit-board', 'pactkit-scaffold']:
            skill_dir = skills_dir / skill_name
            assert (skill_dir / "SKILL.md").is_file(), f"Missing SKILL.md in {skill_name}"
            assert (skill_dir / "scripts").is_dir(), f"Missing scripts/ in {skill_name}"

    def test_no_rules_directory(self, tmp_path):
        """Plugin mode should NOT create a rules/ directory."""
        out = _run_deploy_plugin(tmp_path)
        assert not (out / "rules").exists()

    def test_no_pactkit_yaml(self, tmp_path):
        """Plugin mode should NOT create pactkit.yaml."""
        out = _run_deploy_plugin(tmp_path)
        assert not (out / "pactkit.yaml").exists()


# ===========================================================================
# Scenario 2: plugin.json content correctness
# ===========================================================================

class TestPluginJson:
    """Acceptance Criteria Scenario 2: plugin.json 内容正确"""

    def test_required_fields(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        assert data["name"] == "pactkit"
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
        assert isinstance(data["description"], str)
        assert len(data["description"]) > 0

    def test_license_is_mit(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        assert data["license"] == "MIT"

    def test_version_matches_package(self, tmp_path):
        from pactkit import __version__
        out = _run_deploy_plugin(tmp_path)
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == __version__

    def test_optional_metadata_fields(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        data = json.loads((out / ".claude-plugin" / "plugin.json").read_text())
        assert "author" in data
        assert "homepage" in data
        assert "repository" in data
        assert "keywords" in data


# ===========================================================================
# Scenario 3: CLAUDE.md self-contained (inline rules)
# ===========================================================================

class TestPluginClaudeMd:
    """Acceptance Criteria Scenario 3: CLAUDE.md 自包含"""

    def test_no_at_import_references(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        assert "@~/.claude/" not in content

    def test_contains_core_protocol(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        assert "# Core Protocol" in content
        assert "Strict TDD" in content

    def test_contains_hierarchy_of_truth(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        assert "# The Hierarchy of Truth" in content

    def test_contains_all_rule_modules(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        for key, module_content in RULES_MODULES.items():
            # Check the first heading line of each module is present
            first_line = module_content.strip().split('\n')[0]
            assert first_line in content, f"Missing rule module: {key} (expected: {first_line})"

    def test_has_constitution_header(self, tmp_path):
        out = _run_deploy_plugin(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        assert "PactKit Global Constitution" in content


# ===========================================================================
# Scenario 4: Classic mode unchanged
# ===========================================================================

class TestClassicModeUnchanged:
    """Acceptance Criteria Scenario 4: Classic 模式不受影响"""

    def test_classic_claude_md_no_global_rule_imports(self, tmp_path):
        """STORY-slim-011: CLAUDE.md no longer has global rule @imports."""
        out = _run_deploy_classic(tmp_path)
        content = (out / "CLAUDE.md").read_text()
        assert "@~/.claude/rules/" not in content
        assert "@./docs/product/context.md" in content

    def test_classic_has_rules_dir(self, tmp_path):
        out = _run_deploy_classic(tmp_path)
        rules = out / "rules"
        assert rules.is_dir()
        for filename in RULES_FILES.values():
            assert (rules / filename).is_file(), f"Missing rule: {filename}"

    def test_classic_no_plugin_dir(self, tmp_path):
        out = _run_deploy_classic(tmp_path)
        assert not (out / ".claude-plugin").exists()

    def test_default_format_is_classic(self, tmp_path):
        """deploy() without format param behaves as classic."""
        out = tmp_path / ".claude"
        deploy(target=str(out))
        content = (out / "CLAUDE.md").read_text()
        assert "PactKit Global Constitution" in content
        assert not (out / ".claude-plugin").exists()


# ===========================================================================
# Scenario 5: Marketplace repository generation
# ===========================================================================

class TestMarketplaceGeneration:
    """Acceptance Criteria Scenario 5: Marketplace 仓库生成"""

    def test_marketplace_json_exists(self, tmp_path):
        out = _run_deploy_marketplace(tmp_path)
        assert (out / "marketplace.json").is_file()

    def test_marketplace_json_content(self, tmp_path):
        out = _run_deploy_marketplace(tmp_path)
        data = json.loads((out / "marketplace.json").read_text())
        assert data["name"] == "pactkit"
        assert "owner" in data
        assert isinstance(data["plugins"], list)
        assert len(data["plugins"]) == 1
        assert data["plugins"][0]["name"] == "pactkit"
        assert data["plugins"][0]["source"] == "./pactkit-plugin"

    def test_marketplace_contains_plugin_subdir(self, tmp_path):
        out = _run_deploy_marketplace(tmp_path)
        plugin_dir = out / "pactkit-plugin"
        assert plugin_dir.is_dir()
        assert (plugin_dir / ".claude-plugin" / "plugin.json").is_file()
        assert (plugin_dir / "CLAUDE.md").is_file()
        assert (plugin_dir / "agents").is_dir()
        assert (plugin_dir / "commands").is_dir()
        assert (plugin_dir / "skills").is_dir()


# ===========================================================================
# CLI --format argument
# ===========================================================================

class TestCliFormatArgument:
    """R1: CLI 新增 --format 参数"""

    def test_cli_format_plugin(self, tmp_path):
        """pactkit init --format plugin -t <dir> produces plugin output."""
        from pactkit.cli import main
        out = tmp_path / "out"
        with patch("sys.argv", ["pactkit", "init", "--format", "plugin", "-t", str(out)]):
            main()
        assert (out / ".claude-plugin" / "plugin.json").is_file()

    def test_cli_format_marketplace(self, tmp_path):
        """pactkit init --format marketplace -t <dir> produces marketplace output."""
        from pactkit.cli import main
        out = tmp_path / "out"
        with patch("sys.argv", ["pactkit", "init", "--format", "marketplace", "-t", str(out)]):
            main()
        assert (out / "marketplace.json").is_file()

    def test_cli_format_classic(self, tmp_path):
        """pactkit init --format classic -t <dir> produces classic output."""
        from pactkit.cli import main
        out = tmp_path / "out"
        with patch("sys.argv", ["pactkit", "init", "--format", "classic", "-t", str(out)]):
            main()
        assert (out / "CLAUDE.md").is_file()
        assert "PactKit Global Constitution" in (out / "CLAUDE.md").read_text()

    def test_cli_default_format_is_classic(self, tmp_path):
        """pactkit init -t <dir> (no --format) defaults to classic."""
        from pactkit.cli import main
        out = tmp_path / "out"
        with patch("sys.argv", ["pactkit", "init", "-t", str(out)]):
            main()
        assert not (out / ".claude-plugin").exists()
        assert (out / "CLAUDE.md").is_file()
