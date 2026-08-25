"""Tests for STORY-011: Per-Command Rule Loading — Extract Rules from AGENTS.md."""


import pytest

from pactkit_codex.deployer import CodexDeployer
from pactkit.profiles import get_profile
from pactkit.prompts.rules import (
    COMMAND_RULES_MAP,
    CREDENTIAL_SAFETY_FILE,
    RULES_FILES,
)


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    (tmp_path / "rules").mkdir()
    (tmp_path / "prompts").mkdir()
    return tmp_path


@pytest.fixture
def codex_profile():
    return get_profile("codex")


class TestAC1RulesDeployedAsFiles:
    """AC1: Rules deployed as separate files under ~/.codex/rules/."""

    def test_rule_files_created(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        rules_dir = codex_root / "rules"
        rule_files = list(rules_dir.glob("*.md"))
        assert len(rule_files) >= 7, f"Expected >=7 rule files, got {len(rule_files)}"

    def test_rule_files_non_empty(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").glob("*.md"):
            content = md_file.read_text()
            assert len(content) > 50, f"{md_file.name} is too short"

    def test_no_claude_paths_in_rules(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").glob("*.md"):
            content = md_file.read_text()
            assert "~/.claude/" not in content, f"{md_file.name} has ~/.claude/ path"

    def test_no_anthropic_model_refs(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").glob("*.md"):
            content = md_file.read_text()
            assert "claude-sonnet" not in content, f"{md_file.name} has model ref"
            assert "claude-opus" not in content, f"{md_file.name} has model ref"

    def test_command_routing_uses_codex_skill_names(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        content = (codex_root / "rules" / "pactkit.md").read_text()
        assert "commands/project-" not in content
        assert "`$project-plan`" in content
        assert "`$project-act`" in content
        assert "Subagent Team" not in content
        assert "subagent team" not in content.lower()
        assert "current Codex session" in content


class TestAC2CommandSkillsIncludeRuleRefs:
    """AC2: Deployed command SKILL.md files include @~/.codex/rules/ references."""

    def test_project_act_has_rule_refs(self, codex_root, codex_profile):
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        act_skill = skills_dir / "project-act" / "SKILL.md"
        assert act_skill.exists()
        content = act_skill.read_text()
        assert "@~/.codex/rules/pactkit.md" in content
        assert "@~/.codex/rules/02-mcp-integration.md" in content

    def test_project_clarify_minimal_rule_refs(self, codex_root, codex_profile):
        """project-clarify only needs core + credential references."""
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        clarify_skill = skills_dir / "project-clarify" / "SKILL.md"
        assert clarify_skill.exists()
        content = clarify_skill.read_text()
        assert "@~/.codex/rules/pactkit.md" in content
        assert f"@~/.codex/rules/{CREDENTIAL_SAFETY_FILE}" in content
        # Should NOT have architecture rules
        assert "@~/.codex/rules/04-architecture-principles.md" not in content


class TestAC3NoInlineRulesInAgentsMd:
    """AC3: AGENTS.md no longer contains inline rule text."""

    def test_no_inline_rule_markers(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_agents_md(codex_root, codex_profile)

        content = (codex_root / "AGENTS.md").read_text()
        # These are section headers from inlined rules — should be gone
        assert "## Core Protocol" not in content
        assert "## The Hierarchy of Truth" not in content
        assert "## Strict TDD" not in content
        assert "## Visual First" not in content

    def test_has_rules_reference_table(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_agents_md(codex_root, codex_profile)

        content = (codex_root / "AGENTS.md").read_text()
        assert "Rules Reference" in content or "rules/" in content


class TestAC4AgentsMdSizeBudget:
    """AC4: AGENTS.md under 10KB (SHOULD be under 8KB)."""

    def test_under_10kb(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_agents_md(codex_root, codex_profile)

        size = len((codex_root / "AGENTS.md").read_bytes())
        assert size < 10 * 1024, f"AGENTS.md is {size} bytes, exceeds 10KB"


class TestAC5CredentialSafetyInEveryCommand:
    """AC5: Every deployed command SKILL.md references 09-credential-safety.md."""

    def test_all_command_skills_have_credential_rule(self, codex_root, codex_profile):
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        for cmd_dir in skills_dir.iterdir():
            if not cmd_dir.is_dir():
                continue
            skill_md = cmd_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text()
                assert CREDENTIAL_SAFETY_FILE in content, (
                    f"{cmd_dir.name}/SKILL.md missing credential safety rule"
                )


class TestRulesMapConsistency:
    """Verify COMMAND_RULES_MAP uses RULES_FILES keys only."""

    def test_all_keys_valid(self):
        valid_keys = set(RULES_FILES.keys()) | {"credential"}
        for cmd, rules in COMMAND_RULES_MAP.items():
            for rule in rules:
                assert rule in valid_keys, f"{cmd} references unknown rule: {rule}"

    def test_credential_in_every_command(self):
        for cmd, rules in COMMAND_RULES_MAP.items():
            assert "credential" in rules, f"{cmd} missing credential rule"
