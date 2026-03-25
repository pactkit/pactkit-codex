"""Tests for STORY-063: PDCA Playbook Prompt Slimming.

Acceptance Criteria:
- AC1: Shared Protocols Exist in RULES_MODULES['shared']
- AC2: Sprint is Protocol-Only (< 3000 chars, preserves keywords)
- AC3: MCP Signatures Removed (no tool param teaching, business intent present)
- AC4: All Pre-existing Tests Pass (tested via regression, not here)
- AC5: Design Runs Spec Lint
- AC6: DEV_REF Ghost Resolved
- AC7: Total Prompt Size Reduced >= 15%
"""

import pytest


def _prompts():
    """Lazy import to pick up source changes."""
    import importlib

    import pactkit.prompts.commands as cmd_mod
    import pactkit.prompts.rules as rules_mod
    import pactkit.prompts.workflows as wf_mod

    importlib.reload(rules_mod)
    importlib.reload(wf_mod)
    importlib.reload(cmd_mod)
    return cmd_mod, wf_mod, rules_mod


# ---------------------------------------------------------------------------
# AC1: Shared Protocols Exist
# ---------------------------------------------------------------------------
class TestAC1SharedProtocols:
    def test_shared_key_exists(self):
        _, _, rules = _prompts()
        assert "shared" in rules.RULES_MODULES, (
            "RULES_MODULES must contain a 'shared' key"
        )

    def test_lazy_visualize_protocol(self):
        _, _, rules = _prompts()
        shared = rules.RULES_MODULES["shared"]
        assert "Lazy Visualize" in shared, (
            "Shared protocols must contain 'Lazy Visualize Protocol'"
        )

    def test_test_mapping_protocol(self):
        _, _, rules = _prompts()
        shared = rules.RULES_MODULES["shared"]
        assert "Test Mapping" in shared, (
            "Shared protocols must contain 'Test Mapping Protocol'"
        )

    def test_context_md_format(self):
        _, _, rules = _prompts()
        shared = rules.RULES_MODULES["shared"]
        assert "Context.md" in shared or "context.md" in shared, (
            "Shared protocols must contain 'Context.md Format'"
        )

    def test_shared_has_rules_file_mapping(self):
        """Shared module must have a corresponding file in RULES_FILES."""
        _, _, rules = _prompts()
        assert "shared" in rules.RULES_FILES, (
            "RULES_FILES must contain a 'shared' key"
        )


# ---------------------------------------------------------------------------
# AC2: Sprint is Protocol-Only
# ---------------------------------------------------------------------------
class TestAC2SprintProtocolOnly:
    def test_sprint_under_3000_chars(self):
        _, wf, _ = _prompts()
        assert len(wf.SPRINT_PROMPT) < 3000, (
            f"SPRINT_PROMPT is {len(wf.SPRINT_PROMPT)} chars, must be < 3000"
        )

    @pytest.mark.parametrize("keyword", [
        "TeamCreate", "TaskCreate", "SendMessage", "TeamDelete",
        "$ARGUMENTS", "Orchestrator",
    ])
    def test_sprint_preserves_keywords(self, keyword):
        _, wf, _ = _prompts()
        assert keyword in wf.SPRINT_PROMPT, (
            f"SPRINT_PROMPT must contain '{keyword}'"
        )

    def test_sprint_preserves_pdca_phases(self):
        _, wf, _ = _prompts()
        for phase in ["Plan", "Act", "Check", "Close"]:
            assert phase in wf.SPRINT_PROMPT, (
                f"SPRINT_PROMPT must contain '{phase}'"
            )

    def test_sprint_has_agent_types(self):
        _, wf, _ = _prompts()
        for agent in ["system-architect", "qa-engineer", "security-auditor", "repo-maintainer"]:
            assert agent in wf.SPRINT_PROMPT, (
                f"SPRINT_PROMPT must mention agent type '{agent}'"
            )

    def test_sprint_has_playbook_refs(self):
        _, wf, _ = _prompts()
        assert "project-plan.md" in wf.SPRINT_PROMPT or "project-plan" in wf.SPRINT_PROMPT
        assert "project-act.md" in wf.SPRINT_PROMPT or "project-act" in wf.SPRINT_PROMPT


# ---------------------------------------------------------------------------
# AC3: MCP Signatures Removed
# ---------------------------------------------------------------------------
class TestAC3MCPSignaturesRemoved:
    def test_no_mcp_create_entities_param_teaching(self):
        cmd, _, _ = _prompts()
        all_content = "\n".join(cmd.COMMANDS_CONTENT.values())
        assert "mcp__memory__create_entities with:" not in all_content, (
            "MCP tool parameter teaching must be removed"
        )

    def test_no_mcp_search_nodes_param_teaching(self):
        cmd, _, _ = _prompts()
        all_content = "\n".join(cmd.COMMANDS_CONTENT.values())
        assert "mcp__memory__search_nodes with" not in all_content, (
            "MCP tool parameter teaching must be removed"
        )

    def test_business_intent_store_present(self):
        cmd, _, _ = _prompts()
        plan = cmd.COMMANDS_CONTENT["project-plan.md"]
        lower = plan.lower()
        assert "store" in lower and ("design context" in lower or "memory mcp" in lower), (
            "Plan must preserve business intent for storing to Memory MCP"
        )

    def test_business_intent_load_present(self):
        cmd, _, _ = _prompts()
        act = cmd.COMMANDS_CONTENT["project-act.md"]
        lower = act.lower()
        assert "load" in lower and ("prior context" in lower or "memory mcp" in lower), (
            "Act must preserve business intent for loading from Memory MCP"
        )


# ---------------------------------------------------------------------------
# AC5: Design Runs Spec Lint
# ---------------------------------------------------------------------------
class TestAC5DesignSpecLint:
    def test_design_has_spec_lint_reference(self):
        _, wf, _ = _prompts()
        assert "spec_linter" in wf.DESIGN_PROMPT or "Spec Lint" in wf.DESIGN_PROMPT, (
            "DESIGN_PROMPT Phase 3 must reference spec_linter or Spec Lint"
        )


# ---------------------------------------------------------------------------
# AC6: DEV_REF Ghost Resolved
# ---------------------------------------------------------------------------
class TestAC6DevRefGhostResolved:
    def test_act_no_specific_dev_ref_names(self):
        """Act must NOT reference specific unreachable variable names."""
        cmd, _, _ = _prompts()
        act = cmd.COMMANDS_CONTENT["project-act.md"]
        # Should not have specific ghost references like DEV_REF_BACKEND
        assert "DEV_REF_BACKEND" not in act, (
            "Ghost reference DEV_REF_BACKEND must be removed from Act"
        )
        assert "DEV_REF_FRONTEND" not in act, (
            "Ghost reference DEV_REF_FRONTEND must be removed from Act"
        )
        assert "TEST_REF_PYTHON" not in act, (
            "Ghost reference TEST_REF_PYTHON must be removed from Act"
        )

    def test_act_still_has_stack_reference_concept(self):
        """Act must still reference the stack reference concept for test compatibility."""
        cmd, _, _ = _prompts()
        act = cmd.COMMANDS_CONTENT["project-act.md"]
        # test_stack_references.py:219 requires DEV_REF or TEST_REF or Stack Reference
        assert (
            "DEV_REF" in act
            or "TEST_REF" in act
            or "Stack Reference" in act
            or "stack reference" in act
        ), "Act must contain stack reference concept for test compatibility"

    def test_act_still_has_stack_detection(self):
        """Act must still mention detecting stacks for test compatibility."""
        cmd, _, _ = _prompts()
        act = cmd.COMMANDS_CONTENT["project-act.md"]
        lower = act.lower()
        assert "detect" in lower or "identify" in lower
        assert "stack" in lower or "language" in lower or "project type" in lower


# ---------------------------------------------------------------------------
# AC7: Total Prompt Size Reduced >= 15%
# ---------------------------------------------------------------------------
BASELINE_TOTAL_CHARS = 73511


class TestAC7PromptSizeReduced:
    def test_total_size_reduced_15_percent(self):
        cmd, _, _ = _prompts()
        total = sum(len(v) for v in cmd.COMMANDS_CONTENT.values())
        threshold = int(BASELINE_TOTAL_CHARS * 0.85)
        assert total <= threshold, (
            f"Total prompt size is {total} chars ({100 - total * 100 // BASELINE_TOTAL_CHARS}% reduction), "
            f"need at least 15% reduction to {threshold} chars"
        )
