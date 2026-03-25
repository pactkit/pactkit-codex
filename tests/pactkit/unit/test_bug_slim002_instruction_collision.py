"""BUG-slim-002: Rules-Commands Instruction Collision Causes Plan/Act Stall.

Tests verify that Rules and Commands no longer have overlapping instructions
that cause repeated execution, logical deadlocks, or cascading sub-flows.
"""

from pactkit.prompts.commands import COMMANDS_CONTENT
from pactkit.prompts.rules import RULES_MODULES


# ---------------------------------------------------------------------------
# R1: PDCA Command Exemption for Visual First
# ---------------------------------------------------------------------------
class TestR1VisualFirstPDCAExemption:
    """Rule 01 'Visual First' must include a PDCA exemption clause."""

    def test_core_rule_contains_pdca_exemption(self):
        core = RULES_MODULES["core"]
        assert "PDCA" in core, "Visual First must mention PDCA exemption"

    def test_core_rule_exemption_mentions_command_precedence(self):
        core = RULES_MODULES["core"]
        # The exemption should state that command's own visualize phases take precedence
        assert "command" in core.lower() or "playbook" in core.lower(), (
            "Visual First exemption must reference command/playbook precedence"
        )

    def test_visual_first_still_applies_to_free_conversation(self):
        """Visual First should still exist for non-PDCA usage."""
        core = RULES_MODULES["core"]
        assert "Visual First" in core or "visualize" in core, (
            "Visual First rule must still be present for free conversation"
        )


# ---------------------------------------------------------------------------
# R2: Plan-Phase Exemption for Operating Guidelines
# ---------------------------------------------------------------------------
class TestR2OperatingGuidelinesExemption:
    """Rule 02 Operating Guidelines must exempt Plan/Design from 'read Spec first'."""

    def test_hierarchy_rule_exempts_plan(self):
        hierarchy = RULES_MODULES["hierarchy"]
        assert "/project-plan" in hierarchy, (
            "Operating Guidelines must mention /project-plan exemption"
        )

    def test_hierarchy_rule_exempts_design(self):
        hierarchy = RULES_MODULES["hierarchy"]
        assert "/project-design" in hierarchy, (
            "Operating Guidelines must mention /project-design exemption"
        )

    def test_hierarchy_rule_still_requires_spec_read_for_act(self):
        """The 'read Spec before modifying code' rule should still exist."""
        hierarchy = RULES_MODULES["hierarchy"]
        assert "read the relevant Spec" in hierarchy or "read the Spec" in hierarchy.lower(), (
            "Operating Guidelines must still require reading Spec for Act/Check"
        )


# ---------------------------------------------------------------------------
# R3: Init Guard Downgrade to Suggestion-and-Stop
# ---------------------------------------------------------------------------
class TestR3InitGuardWarnAndStop:
    """Plan Phase 0.5 Init Guard must warn+STOP, not auto-execute /project-init."""

    def test_plan_does_not_auto_execute_init(self):
        plan = COMMANDS_CONTENT["project-plan.md"]
        assert "Execute the full `/project-init` flow" not in plan, (
            "Init Guard must NOT auto-execute /project-init"
        )

    def test_plan_init_guard_stops(self):
        plan = COMMANDS_CONTENT["project-plan.md"]
        # Should contain STOP instruction
        assert "STOP" in plan and "not initialized" in plan.lower(), (
            "Init Guard must STOP when markers are missing"
        )

    def test_plan_init_guard_suggests_manual_init(self):
        plan = COMMANDS_CONTENT["project-plan.md"]
        assert "/project-init" in plan, (
            "Init Guard must still mention /project-init as a suggestion"
        )


# ---------------------------------------------------------------------------
# R4: Clarify Gate Threshold Increase
# ---------------------------------------------------------------------------
class TestR4ClarifyGateThreshold:
    """Plan Phase 0.7 Clarify Gate must have a higher auto-trigger threshold."""

    def test_clarify_gate_requires_medium_for_auto_trigger(self):
        plan = COMMANDS_CONTENT["project-plan.md"]
        # Old: "2 High signals → Auto-trigger"
        # New: should require Medium signals too for auto-trigger
        assert "2 High" not in plan or "Medium" in plan.split("Auto-trigger")[0] if "Auto-trigger" in plan else True, (
            "Auto-trigger should require High + Medium signals, not just 2 High alone"
        )

    def test_single_sentence_is_low_signal(self):
        plan = COMMANDS_CONTENT["project-plan.md"]
        # "Single sentence input" should be Low, not Medium
        # Check that single sentence is not listed as [Medium]
        lines = plan.split("\n")
        for line in lines:
            if "Single sentence" in line or "< 15 words" in line:
                assert "[Low]" in line or "[low]" in line.lower(), (
                    f"Single sentence input should be [Low] signal, got: {line.strip()}"
                )
                break


# ---------------------------------------------------------------------------
# R5: Act Consistency Check Simplification
# ---------------------------------------------------------------------------
class TestR5ActConsistencyCheckSimplified:
    """Act Phase 0.6 must be a lightweight existence check."""

    def test_act_no_cross_reference_parsing(self):
        act = COMMANDS_CONTENT["project-act.md"]
        # Should NOT contain the heavy cross-reference alignment matrix
        assert "keyword overlap" not in act, (
            "Act Phase 0.6 must not do keyword overlap cross-referencing"
        )

    def test_act_no_alignment_matrix(self):
        act = COMMANDS_CONTENT["project-act.md"]
        assert "alignment matrix" not in act.lower(), (
            "Act Phase 0.6 must not output an alignment matrix"
        )

    def test_act_has_existence_check(self):
        act = COMMANDS_CONTENT["project-act.md"]
        # Should verify Spec and Board entry exist
        assert "exist" in act.lower(), (
            "Act Phase 0.6 must check file existence"
        )


# ---------------------------------------------------------------------------
# R6: Act Visualize Deduplication
# ---------------------------------------------------------------------------
class TestR6ActVisualizeDeduplicated:
    """Act Phase 1 should only run --focus, not full 3-mode visualize."""

    def test_act_phase1_uses_focus_only(self):
        act = COMMANDS_CONTENT["project-act.md"]
        # Phase 1 section should mention --focus
        # Find the Phase 1 section
        phase1_start = act.find("Phase 1:")
        phase2_start = act.find("Phase 2:")
        if phase1_start != -1 and phase2_start != -1:
            phase1_text = act[phase1_start:phase2_start]
            assert "--focus" in phase1_text, (
                "Act Phase 1 must use --focus for targeted visualize"
            )

    def test_act_phase1_does_not_run_three_modes(self):
        act = COMMANDS_CONTENT["project-act.md"]
        phase1_start = act.find("Phase 1:")
        phase2_start = act.find("Phase 2:")
        if phase1_start != -1 and phase2_start != -1:
            phase1_text = act[phase1_start:phase2_start]
            # Should NOT run all 3 modes in Phase 1
            assert "--mode class" not in phase1_text, (
                "Act Phase 1 must not run --mode class (deferred to Phase 4)"
            )
