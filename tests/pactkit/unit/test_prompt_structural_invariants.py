"""
STORY-041 R4: Prompt Structural Invariants Test

Consolidated structural checks for prompt templates.
Each prompt module has a list of structural invariants that MUST be present.

This replaces scattered keyword-in-string tests with meaningful structural checks.
"""

import pytest

from pactkit import prompts

# ===========================================================================
# Structural Invariants Definitions
# ===========================================================================

# Rules: keyed by RULES_MODULES dict key
RULE_INVARIANTS = {
    "core": ["# Core Protocol", "Session Context", "Visual First"],
    "hierarchy": ["Hierarchy of Truth", "Tier 1", "Tier 2", "Tier 3"],
    "atlas": ["File Atlas", "docs/specs/", "sprint_board.md"],
    "routing": ["Command Reference", "Plan", "Act", "Check", "Done"],
    "workflow": ["Workflow Conventions", "Git Commit", "feat", "fix"],
    "mcp": ["MCP Integration", "Context7", "Memory MCP"],
}

# Commands: keyed by COMMANDS_CONTENT dict key
COMMAND_INVARIANTS = {
    "project-plan.md": ["Command: Plan", "Phase 0", "Phase 1"],
    "project-act.md": ["Command: Act", "TDD", "Phase 2", "Phase 3"],
    "project-check.md": ["Command: Check", "Security", "Quality"],
    "project-done.md": ["Command: Done", "Git Commit", "Regression"],
    "project-init.md": ["Command: Init", "Phase 0"],
    "project-sprint.md": ["Command: Sprint", "Orchestrator"],
    "project-hotfix.md": ["Command: Hotfix", "fast-fix"],
    "project-design.md": ["Command: Design", "PRD"],
}

# Agents: keyed by AGENTS_EXPERT dict key
AGENT_INVARIANTS = {
    "system-architect": ["System Architect", "design"],
    "senior-developer": ["Senior Developer", "TDD"],
    "qa-engineer": ["QA Engineer", "Quality"],
    "repo-maintainer": ["Repo Maintainer", "commit"],
}

# Skills: keyed by skill constant name
SKILL_INVARIANTS = {
    "SKILL_VISUALIZE_MD": ["pactkit-visualize", "visualize", "--mode"],
    "SKILL_BOARD_MD": ["pactkit-board", "add_story", "update_task"],
    "SKILL_SCAFFOLD_MD": ["pactkit-scaffold", "create_spec"],
    "SKILL_TRACE_MD": ["pactkit-trace", "call chain"],
    "SKILL_DRAW_MD": ["pactkit-draw", "Draw.io"],
    "SKILL_STATUS_MD": ["pactkit-status", "overview"],
    "SKILL_DOCTOR_MD": ["pactkit-doctor", "Diagnostic"],
    "SKILL_REVIEW_MD": ["pactkit-review", "SOLID"],
    "SKILL_RELEASE_MD": ["pactkit-release", "snapshot"],
}


# ===========================================================================
# Test Classes
# ===========================================================================


class TestRuleModuleInvariants:
    """Structural invariants for rule modules."""

    @pytest.mark.parametrize("rule_key,invariants", list(RULE_INVARIANTS.items()))
    def test_rule_has_invariants(self, rule_key, invariants):
        """Each rule module contains required structural elements."""
        content = prompts.RULES_MODULES.get(rule_key, "")
        for invariant in invariants:
            assert invariant in content, f"Rule '{rule_key}' missing: {invariant}"


class TestCommandModuleInvariants:
    """Structural invariants for command playbooks."""

    @pytest.mark.parametrize("cmd_key,invariants", list(COMMAND_INVARIANTS.items()))
    def test_command_has_invariants(self, cmd_key, invariants):
        """Each command playbook contains required structural elements."""
        content = prompts.COMMANDS_CONTENT.get(cmd_key, "")
        for invariant in invariants:
            assert invariant in content, f"Command '{cmd_key}' missing: {invariant}"


class TestAgentModuleInvariants:
    """Structural invariants for agent definitions."""

    @pytest.mark.parametrize("agent_name,invariants", list(AGENT_INVARIANTS.items()))
    def test_agent_has_invariants(self, agent_name, invariants):
        """Each agent definition contains required structural elements."""
        agent_cfg = prompts.AGENTS_EXPERT.get(agent_name)
        assert agent_cfg is not None, f"Agent {agent_name} not found"
        prompt = agent_cfg.get("prompt", "") + agent_cfg.get("desc", "")
        for invariant in invariants:
            assert invariant in prompt, f"Agent {agent_name} missing: {invariant}"


class TestSkillModuleInvariants:
    """Structural invariants for skill definitions."""

    @pytest.mark.parametrize("skill_key,invariants", list(SKILL_INVARIANTS.items()))
    def test_skill_has_invariants(self, skill_key, invariants):
        """Each skill definition contains required structural elements."""
        content = getattr(prompts, skill_key)
        for invariant in invariants:
            assert invariant in content, f"{skill_key} missing: {invariant}"


class TestPromptModuleCounts:
    """Verify expected counts of prompt modules."""

    def test_rule_count(self):
        """9 rule modules (added 09-sectional-write)."""
        assert len(prompts.RULES_MODULES) == 9

    def test_command_count(self):
        """STORY-051: Should have 11 command playbooks (added project-release, project-pr)."""
        assert len(prompts.COMMANDS_CONTENT) == 11

    def test_agent_count(self):
        """Should have 9 agent definitions."""
        assert len(prompts.AGENTS_EXPERT) == 9

    def test_skill_count(self):
        """Should have 10 skill definitions."""
        # Count skill constants
        skill_attrs = [a for a in dir(prompts) if a.startswith("SKILL_") and a.endswith("_MD")]
        assert len(skill_attrs) == 10
