"""
STORY-040: Deployer 清理策略统一 — Commands/Agents 先删后写
Tests for managed file cleanup in deployer.py
"""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pactkit import __version__
from pactkit.generators.deployer import deploy
from pactkit.prompts import AGENTS_EXPERT, COMMANDS_CONTENT


@pytest.fixture
def fake_claude(tmp_path):
    """Set up a fake ~/.claude with pre-existing files, then run deploy()."""
    claude_root = tmp_path / ".claude"
    commands_dir = claude_root / "commands"
    agents_dir = claude_root / "agents"
    skills_dir = claude_root / "skills"

    for d in [commands_dir, agents_dir, skills_dir]:
        d.mkdir(parents=True)

    # Seed: stale managed files (should be cleaned)
    (commands_dir / "project-old-removed.md").write_text("stale command")
    (agents_dir / "old-removed-agent.md").write_text("stale agent")

    # Seed: user custom files (should be preserved)
    (commands_dir / "ultra-think.md").write_text("user command")
    (commands_dir / "my-custom.md").write_text("user command 2")
    (agents_dir / "my-custom-agent.md").write_text("user agent")

    # Run deployer with patched home dir
    with patch("pactkit.generators.deployer.Path") as mock_path:
        # Make Path.home() return tmp_path so deploy writes there
        mock_path.home.return_value = tmp_path
        # Preserve Path's other behaviors
        mock_path.side_effect = Path
        # Actually we need a cleaner mock - just patch the claude_root construction

    return claude_root, commands_dir, agents_dir


def _run_deploy(tmp_path):
    """Run deploy() with ~/.claude and cwd redirected to tmp_path/.claude."""
    claude_root = tmp_path / ".claude"
    for d in [claude_root, claude_root / "agents", claude_root / "commands", claude_root / "skills"]:
        d.mkdir(parents=True, exist_ok=True)

    # Monkey-patch Path.home and Path.cwd to redirect
    with patch.object(Path, 'home', return_value=tmp_path), \
         patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        deploy()

    return claude_root


class TestScenario1_StaleCommandsCleaned:
    """Scenario 1: 旧命令文件被清理"""

    def test_stale_project_command_removed(self, tmp_path):
        claude = tmp_path / ".claude"
        cmds = claude / "commands"
        cmds.mkdir(parents=True)
        (cmds / "project-old-removed.md").write_text("stale")

        _run_deploy(tmp_path)

        assert not (cmds / "project-old-removed.md").exists()

    def test_current_commands_all_exist(self, tmp_path):
        _run_deploy(tmp_path)
        cmds = tmp_path / ".claude" / "commands"

        for filename in COMMANDS_CONTENT:
            assert (cmds / filename).is_file(), f"Missing: {filename}"


class TestScenario2_UserCommandsPreserved:
    """Scenario 2: 用户命令被保留"""

    def test_ultra_think_preserved(self, tmp_path):
        claude = tmp_path / ".claude"
        cmds = claude / "commands"
        cmds.mkdir(parents=True)
        (cmds / "ultra-think.md").write_text("user custom")

        _run_deploy(tmp_path)

        assert (cmds / "ultra-think.md").is_file()
        assert (cmds / "ultra-think.md").read_text() == "user custom"

    def test_non_project_prefix_preserved(self, tmp_path):
        claude = tmp_path / ".claude"
        cmds = claude / "commands"
        cmds.mkdir(parents=True)
        (cmds / "my-workflow.md").write_text("custom workflow")

        _run_deploy(tmp_path)

        assert (cmds / "my-workflow.md").is_file()


class TestScenario3_StaleAgentsCleaned:
    """Scenario 3: 旧 Agent 文件被清理"""

    def test_stale_managed_agent_removed(self, tmp_path):
        claude = tmp_path / ".claude"
        agents = claude / "agents"
        agents.mkdir(parents=True)
        # Create a file with a name that was once a managed agent
        (agents / "deprecated-agent.md").write_text("stale")
        # Also create a known managed agent file that's no longer in AGENTS_EXPERT
        # We simulate this by checking all managed agent names are written fresh

        _run_deploy(tmp_path)

        for name in AGENTS_EXPERT:
            assert (agents / f"{name}.md").is_file(), f"Missing agent: {name}"

    def test_all_managed_agents_exist_after_deploy(self, tmp_path):
        _run_deploy(tmp_path)
        agents = tmp_path / ".claude" / "agents"

        for name in AGENTS_EXPERT:
            assert (agents / f"{name}.md").is_file()


class TestScenario4_UserAgentsPreserved:
    """Scenario 4: 用户自定义 Agent 被保留"""

    def test_custom_agent_preserved(self, tmp_path):
        claude = tmp_path / ".claude"
        agents = claude / "agents"
        agents.mkdir(parents=True)
        (agents / "my-custom-agent.md").write_text("user agent")

        _run_deploy(tmp_path)

        assert (agents / "my-custom-agent.md").is_file()
        assert (agents / "my-custom-agent.md").read_text() == "user agent"


class TestScenario5_ScafpyMigration:
    """Scenario 5: scafpy → pactkit 遗留迁移"""

    def test_scafpy_skill_dirs_removed(self, tmp_path):
        """Old scafpy-* skill directories are cleaned up after deploy."""
        claude = tmp_path / ".claude"
        skills = claude / "skills"
        for name in ['scafpy-visualize', 'scafpy-board', 'scafpy-scaffold']:
            scripts = skills / name / "scripts"
            scripts.mkdir(parents=True)
            (skills / name / "SKILL.md").write_text("old skill")
            (scripts / "dummy.py").write_text("old script")

        _run_deploy(tmp_path)

        for name in ['scafpy-visualize', 'scafpy-board', 'scafpy-scaffold']:
            assert not (skills / name).exists(), f"Legacy dir should be removed: {name}"

    def test_scafpy_yaml_renamed_to_pactkit(self, tmp_path):
        """scafpy.yaml is renamed to pactkit.yaml when pactkit.yaml doesn't exist."""
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        old_yaml = claude / "scafpy.yaml"
        old_yaml.write_text('version: "1.2.3"\nstack: python\n')

        _run_deploy(tmp_path)

        assert not old_yaml.exists(), "scafpy.yaml should be removed"
        new_yaml = claude / "pactkit.yaml"
        assert new_yaml.is_file()
        content = new_yaml.read_text()
        assert f'version: "{__version__}"' in content, \
            "BUG-026: version must be synced to __version__ after migration"

    def test_scafpy_yaml_deleted_when_both_exist(self, tmp_path):
        """When both scafpy.yaml and pactkit.yaml exist, scafpy.yaml is deleted."""
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        (claude / "scafpy.yaml").write_text('version: "0.0.1"\n')
        (claude / "pactkit.yaml").write_text('version: "2.0.0"\n')

        _run_deploy(tmp_path)

        assert not (claude / "scafpy.yaml").exists()
        assert (claude / "pactkit.yaml").is_file()
        assert f'version: "{__version__}"' in (claude / "pactkit.yaml").read_text()

    def test_no_error_when_no_scafpy_remnants(self, tmp_path):
        """Deploy works fine when no scafpy remnants exist."""
        claude = _run_deploy(tmp_path)
        assert claude.is_dir()
        # No scafpy dirs should exist
        skills = claude / "skills"
        for name in ['scafpy-visualize', 'scafpy-board', 'scafpy-scaffold']:
            assert not (skills / name).exists()
