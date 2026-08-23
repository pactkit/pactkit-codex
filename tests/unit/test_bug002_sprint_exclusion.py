"""Sprint remains available in Codex through a sequential fallback."""

import pytest


@pytest.fixture()
def codex_deploy(tmp_path):
    from pactkit_codex.deployer import CodexDeployer

    CodexDeployer().deploy(target=str(tmp_path))
    return tmp_path


class TestAC1SprintFallback:

    def test_sprint_is_deployed(self, codex_deploy):
        assert (codex_deploy / "skills" / "project-sprint" / "SKILL.md").exists()

    def test_exactly_10_command_skill_dirs(self, codex_deploy):
        expected_commands = {
            "project-init", "project-plan", "project-act",
            "project-check", "project-done", "project-release",
            "project-pr", "project-hotfix", "project-design", "project-clarify",
        }
        skill_dirs = {d.name for d in (codex_deploy / "skills").iterdir() if d.is_dir()}
        command_dirs = skill_dirs & expected_commands
        assert len(command_dirs) == 10, (
            f"Expected 10 command skill dirs, got {len(command_dirs)}: {command_dirs}"
        )


class TestAC2AgentsMdNoSprint:
    """AC2: AGENTS.md has no project-sprint reference."""

    def test_no_sprint_in_agents_md(self, codex_deploy):
        content = (codex_deploy / "AGENTS.md").read_text()
        assert "project-sprint" not in content


class TestExclusionConstant:
    """R4: CODEX_EXCLUDED_COMMANDS is a module-level constant."""

    def test_constant_exists(self):
        from pactkit_codex.deployer import CODEX_EXCLUDED_COMMANDS

        assert isinstance(CODEX_EXCLUDED_COMMANDS, (set, frozenset))
        assert CODEX_EXCLUDED_COMMANDS == frozenset()
