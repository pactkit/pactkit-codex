"""Tests for BUG-002: project-sprint should not be deployed to Codex CLI."""

import pytest


@pytest.fixture()
def codex_deploy(tmp_path):
    from pactkit.generators.deployer import _deploy_codex

    _deploy_codex(target=str(tmp_path))
    return tmp_path


class TestAC1SprintNotDeployed:
    """AC1: project-sprint.md not in prompts/, exactly 10 files."""

    def test_sprint_not_in_prompts(self, codex_deploy):
        assert not (codex_deploy / "prompts" / "project-sprint.md").exists()

    def test_exactly_10_prompts(self, codex_deploy):
        prompts = list((codex_deploy / "prompts").glob("*.md"))
        assert len(prompts) == 10, f"Expected 10, got {len(prompts)}: {[p.name for p in prompts]}"


class TestAC2AgentsMdNoSprint:
    """AC2: AGENTS.md has no project-sprint reference."""

    def test_no_sprint_in_agents_md(self, codex_deploy):
        content = (codex_deploy / "AGENTS.md").read_text()
        assert "project-sprint" not in content


class TestExclusionConstant:
    """R4: CODEX_EXCLUDED_PROMPTS is a module-level constant."""

    def test_constant_exists(self):
        from pactkit.generators.deployer import CODEX_EXCLUDED_PROMPTS

        assert isinstance(CODEX_EXCLUDED_PROMPTS, (set, frozenset))
        assert "project-sprint.md" in CODEX_EXCLUDED_PROMPTS
