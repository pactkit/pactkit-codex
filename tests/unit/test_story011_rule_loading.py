"""Tests for STORY-011: Per-Command Rule Loading — Extract Rules from AGENTS.md."""


import pytest

from pactkit_codex.deployer import CodexDeployer
from pactkit.profiles import get_profile
from pactkit.prompts.rules import (
    COMMAND_CONDITIONAL_RULES_MAP,
    COMMAND_RULES_MAP,
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
    """AC1: Only Runtime is global; other rules are stored on demand."""

    def test_rule_files_created(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        global_files = list((codex_root / "rules").rglob("*.md"))
        assert [path.name for path in global_files] == ["pactkit-runtime.md"]
        assert not (codex_root / "skills" / "_rules").exists()

    def test_rule_files_non_empty(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").rglob("*.md"):
            content = md_file.read_text()
            assert len(content) > 50, f"{md_file.name} is too short"

    def test_no_claude_paths_in_rules(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").rglob("*.md"):
            content = md_file.read_text()
            assert "~/.claude/" not in content, f"{md_file.name} has ~/.claude/ path"

    def test_no_anthropic_model_refs(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        for md_file in (codex_root / "rules").rglob("*.md"):
            content = md_file.read_text()
            assert "claude-sonnet" not in content, f"{md_file.name} has model ref"
            assert "claude-opus" not in content, f"{md_file.name} has model ref"

    def test_command_routing_uses_codex_skill_names(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_rules(codex_root / "rules", codex_profile)

        content = (codex_root / "rules" / "pactkit-runtime.md").read_text()
        assert "commands/project-" not in content
        assert "Subagent Team" not in content
        assert "subagent team" not in content.lower()
        assert "current host and current session" in content


class TestAC2CommandSkillsIncludeRules:
    """AC2: Deployed command SKILL.md files contain their active rules."""

    def test_project_act_has_inline_rules(self, codex_root, codex_profile):
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        act_skill = skills_dir / "project-act" / "SKILL.md"
        assert act_skill.exists()
        content = act_skill.read_text()
        assert "## Active PactKit Contract" in content
        assert "# PDCA Lifecycle" in content
        assert "# Act Contract" in content
        assert "# External Tools" not in content
        assert "# Capability Design" not in content
        assert "@~/.codex/rules/" not in content
        assert "references/rules/capability-design.md" in content
        for rule_id in COMMAND_CONDITIONAL_RULES_MAP["project-act"]:
            assert (
                skills_dir / "project-act" / "references" / "rules"
                / f"{rule_id}.md"
            ).is_file()
        assert (
            skills_dir / "project-act" / "references" / "guides" / "caching.md"
        ).is_file()

    def test_project_clarify_has_only_its_inline_contract(self, codex_root, codex_profile):
        """project-clarify only needs core + credential references."""
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        clarify_skill = skills_dir / "project-clarify" / "SKILL.md"
        assert clarify_skill.exists()
        content = clarify_skill.read_text()
        assert "# PDCA Lifecycle" in content
        # project-clarify carries its own phase contract (phase-clarify), not
        # Plan's — stale expectation fixed against the registry ground truth
        # (STORY-slim-20260911b2bbd79889e0 C2: the acceptance job exposed it).
        assert "# Clarify Contract" in content
        assert "# Plan Contract" not in content
        assert "# Credential Safety" not in content
        assert "@~/.codex/rules/" not in content
        assert "# Capability Design" not in content


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

    def test_identifies_runtime_without_loading_a_rule_catalog(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_agents_md(codex_root, codex_profile)

        content = (codex_root / "AGENTS.md").read_text()
        assert "# PactKit Runtime Contract" in content
        assert "## Current Session" in content
        assert "Rules Reference" not in content
        assert "PDCA Routing Table" not in content


class TestAC4AgentsMdSizeBudget:
    """AC4: AGENTS.md under 10KB (SHOULD be under 8KB)."""

    def test_under_10kb(self, codex_root, codex_profile):
        CodexDeployer.deploy_codex_agents_md(codex_root, codex_profile)

        size = len((codex_root / "AGENTS.md").read_bytes())
        assert size < 10 * 1024, f"AGENTS.md is {size} bytes, exceeds 10KB"


class TestAC5CredentialSafetyIsGlobal:
    """AC5: Credential safety lives once in the global Runtime."""

    def test_commands_do_not_duplicate_global_credential_rule(self, codex_root, codex_profile):
        skills_dir = codex_root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        CodexDeployer.deploy_codex_command_skills(skills_dir, codex_profile)

        for cmd_dir in skills_dir.iterdir():
            if not cmd_dir.is_dir():
                continue
            skill_md = cmd_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text()
                assert "# Credential Safety" not in content


class TestRulesMapConsistency:
    """Verify COMMAND_RULES_MAP uses RULES_FILES keys only."""

    def test_all_keys_valid(self):
        valid_keys = set(RULES_FILES.keys()) | {"credential"}
        for cmd, rules in COMMAND_RULES_MAP.items():
            for rule in rules:
                assert rule in valid_keys, f"{cmd} references unknown rule: {rule}"

    def test_runtime_in_every_command(self):
        for cmd, rules in COMMAND_RULES_MAP.items():
            assert "runtime" in rules, f"{cmd} missing runtime rule"
