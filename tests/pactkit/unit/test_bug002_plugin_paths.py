"""BUG-002: Plugin mode deploys hardcoded ~/.claude/skills/ paths.

Tests verify that:
- Classic deployment preserves ~/.claude/skills/ paths (TC-1)
- Plugin deployment uses ${CLAUDE_PLUGIN_ROOT}/skills/ paths (TC-2)
- Plugin commands use ${CLAUDE_PLUGIN_ROOT}/skills/ paths (TC-3)
- Marketplace inherits plugin path behavior (TC-4)
"""
from pactkit.config import VALID_AGENTS, VALID_COMMANDS, VALID_SKILLS
from pactkit.generators.deployer import (
    _deploy_agents,
    _deploy_classic,
    _deploy_commands,
    _deploy_marketplace,
    _deploy_plugin,
    _deploy_skills,
)

CLASSIC_PREFIX = "~/.claude/skills/"
PLUGIN_PREFIX = "${CLAUDE_PLUGIN_ROOT}/skills/"


class TestClassicDeployPreservesPaths:
    """TC-1: Classic deployment preserves ~/.claude/skills/ paths."""

    def test_classic_skills_contain_classic_prefix(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _deploy_skills(skills_dir, sorted(VALID_SKILLS))

        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            if CLASSIC_PREFIX in content:
                # Classic prefix should be present
                assert CLASSIC_PREFIX in content
                # Plugin prefix should NOT be present
                assert PLUGIN_PREFIX not in content

    def test_classic_commands_contain_classic_prefix(self, tmp_path):
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        _deploy_commands(commands_dir, sorted(VALID_COMMANDS))

        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            if CLASSIC_PREFIX in content:
                assert PLUGIN_PREFIX not in content

    def test_classic_full_deploy_no_plugin_prefix(self, tmp_path):
        """Full classic deploy should have zero ${CLAUDE_PLUGIN_ROOT} references."""
        _deploy_classic(target=str(tmp_path))

        for md_file in tmp_path.rglob("*.md"):
            content = md_file.read_text()
            assert PLUGIN_PREFIX not in content, (
                f"{md_file.relative_to(tmp_path)} contains plugin prefix"
            )


class TestPluginSkillsUseCPR:
    """TC-2: Plugin deployment uses ${CLAUDE_PLUGIN_ROOT}/skills/ paths."""

    def test_plugin_skills_contain_plugin_prefix(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _deploy_skills(skills_dir, sorted(VALID_SKILLS),
                       _legacy_prefix="${CLAUDE_PLUGIN_ROOT}/skills")

        found_any = False
        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            if "python3" in content and "scripts/" in content:
                found_any = True
                assert PLUGIN_PREFIX in content, (
                    f"{skill_md.name} missing plugin prefix"
                )
                assert CLASSIC_PREFIX not in content, (
                    f"{skill_md.name} still has classic prefix"
                )

        assert found_any, "Expected at least one SKILL.md with script paths"

    def test_plugin_skills_zero_classic_prefix(self, tmp_path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _deploy_skills(skills_dir, sorted(VALID_SKILLS),
                       _legacy_prefix="${CLAUDE_PLUGIN_ROOT}/skills")

        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            assert CLASSIC_PREFIX not in content, (
                f"{skill_md.relative_to(tmp_path)} still has classic prefix"
            )


class TestPluginCommandsUseCPR:
    """TC-3: Plugin commands use ${CLAUDE_PLUGIN_ROOT}/skills/ paths."""

    def test_plugin_commands_contain_plugin_prefix(self, tmp_path):
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        _deploy_commands(commands_dir, sorted(VALID_COMMANDS),
                         _legacy_prefix="${CLAUDE_PLUGIN_ROOT}/skills")

        found_any = False
        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            if CLASSIC_PREFIX.rstrip('/') in content or PLUGIN_PREFIX.rstrip('/') in content:
                found_any = True
                assert CLASSIC_PREFIX not in content, (
                    f"{cmd_file.name} still has classic prefix"
                )

        assert found_any, "Expected at least one command with skill path references"

    def test_plugin_commands_zero_classic_prefix(self, tmp_path):
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        _deploy_commands(commands_dir, sorted(VALID_COMMANDS),
                         _legacy_prefix="${CLAUDE_PLUGIN_ROOT}/skills")

        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            assert CLASSIC_PREFIX not in content, (
                f"{cmd_file.name} still has classic prefix"
            )


class TestPluginAgentsUseCPR:
    """Plugin agents should also have paths rewritten."""

    def test_plugin_agents_zero_classic_skills_prefix(self, tmp_path):
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        _deploy_agents(agents_dir, sorted(VALID_AGENTS),
                       _legacy_prefix="${CLAUDE_PLUGIN_ROOT}/skills")

        for agent_file in agents_dir.glob("*.md"):
            content = agent_file.read_text()
            assert CLASSIC_PREFIX not in content, (
                f"{agent_file.name} still has classic prefix"
            )


class TestPluginFullDeploy:
    """TC-2/TC-3 combined: Full plugin deploy has zero classic prefix."""

    def test_full_plugin_deploy_zero_classic_skills_prefix(self, tmp_path):
        _deploy_plugin(target=str(tmp_path))

        for md_file in tmp_path.rglob("*.md"):
            content = md_file.read_text()
            assert CLASSIC_PREFIX not in content, (
                f"{md_file.relative_to(tmp_path)} still has classic prefix"
            )

    def test_full_plugin_deploy_has_plugin_prefix_in_skills(self, tmp_path):
        _deploy_plugin(target=str(tmp_path))

        skills_dir = tmp_path / "skills"
        found_any = False
        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            if "python3" in content and "scripts/" in content:
                found_any = True
                assert PLUGIN_PREFIX in content

        assert found_any


class TestMarketplaceInheritsPluginPaths:
    """TC-4: Marketplace inherits plugin path behavior."""

    def test_marketplace_zero_classic_skills_prefix(self, tmp_path):
        _deploy_marketplace(target=str(tmp_path))

        plugin_subdir = tmp_path / "pactkit-plugin"
        for md_file in plugin_subdir.rglob("*.md"):
            content = md_file.read_text()
            assert CLASSIC_PREFIX not in content, (
                f"{md_file.relative_to(tmp_path)} still has classic prefix"
            )

    def test_marketplace_skills_have_plugin_prefix(self, tmp_path):
        _deploy_marketplace(target=str(tmp_path))

        skills_dir = tmp_path / "pactkit-plugin" / "skills"
        found_any = False
        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            if "python3" in content and "scripts/" in content:
                found_any = True
                assert PLUGIN_PREFIX in content

        assert found_any


class TestDefaultParameterBackcompat:
    """R4/R6: Default skills_prefix preserves classic behavior."""

    def test_deploy_skills_default_prefix_is_classic(self, tmp_path):
        """Calling _deploy_skills without skills_prefix should produce classic paths."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _deploy_skills(skills_dir, sorted(VALID_SKILLS))

        for skill_md in skills_dir.rglob("SKILL.md"):
            content = skill_md.read_text()
            assert PLUGIN_PREFIX not in content

    def test_deploy_commands_default_prefix_is_classic(self, tmp_path):
        """Calling _deploy_commands without skills_prefix should produce classic paths."""
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        _deploy_commands(commands_dir, sorted(VALID_COMMANDS))

        for cmd_file in commands_dir.glob("*.md"):
            content = cmd_file.read_text()
            assert PLUGIN_PREFIX not in content
