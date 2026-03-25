"""
STORY-043: Active Clarify — Pre-Plan Requirement Disambiguation

Tests for:
- Phase 0.7 Clarify Gate inserted into project-plan.md
- New project-clarify.md command added to COMMANDS_CONTENT
- Routing table updated with /project-clarify entry
"""


def _commands():
    from pactkit.prompts import COMMANDS_CONTENT
    return COMMANDS_CONTENT


def _rules():
    from pactkit.prompts import RULES_MODULES
    return RULES_MODULES


# ===========================================================================
# Phase 0.7: Clarify Gate in project-plan.md
# ===========================================================================

class TestPlanPhase07ClarifyGate:
    """Phase 0.7 must be present in project-plan.md between Phase 0.5 and Phase 1."""

    def test_phase_07_exists_in_plan(self):
        """Phase 0.7 header exists in project-plan.md."""
        content = _commands()["project-plan.md"]
        assert "Phase 0.7" in content

    def test_phase_07_contains_clarify_gate(self):
        """Phase 0.7 is named 'Clarify Gate'."""
        content = _commands()["project-plan.md"]
        assert "Clarify Gate" in content

    def test_phase_07_contains_ambiguity_signals(self):
        """Phase 0.7 describes ambiguity detection signals."""
        content = _commands()["project-plan.md"]
        # Either references AMBIGUITY_SIGNALS by name or describes the signals inline
        has_signals_label = "AMBIGUITY_SIGNALS" in content
        has_signals_description = (
            "No quantitative metrics" in content
            or "ambiguity" in content.lower()
        )
        assert has_signals_label or has_signals_description

    def test_phase_07_contains_enriched_input(self):
        """Phase 0.7 uses the enriched_input concept."""
        content = _commands()["project-plan.md"]
        assert "enriched_input" in content

    def test_phase_07_contains_greenfield_force_trigger(self):
        """Phase 0.7 mentions Greenfield force-trigger behavior."""
        content = _commands()["project-plan.md"]
        has_greenfield_trigger = (
            "Greenfield Force-Trigger" in content
            or "greenfield" in content.lower()
        )
        assert has_greenfield_trigger

    def test_phase_07_mentions_skip_option(self):
        """Phase 0.7 allows users to skip clarification."""
        content = _commands()["project-plan.md"]
        assert "skip" in content.lower()

    def test_phase_07_is_between_phase_05_and_phase_1(self):
        """Phase 0.7 appears between Phase 0.5 and Phase 1 in document order."""
        content = _commands()["project-plan.md"]
        pos_05 = content.find("Phase 0.5")
        pos_07 = content.find("Phase 0.7")
        pos_1 = content.find("Phase 1:")
        assert pos_05 != -1, "Phase 0.5 must exist"
        assert pos_07 != -1, "Phase 0.7 must exist"
        assert pos_1 != -1, "Phase 1 must exist"
        assert pos_05 < pos_07 < pos_1, (
            f"Expected order Phase 0.5 ({pos_05}) < Phase 0.7 ({pos_07}) < Phase 1 ({pos_1})"
        )


# ===========================================================================
# project-clarify.md command
# ===========================================================================

class TestProjectClarifyCommand:
    """project-clarify.md must be present in COMMANDS_CONTENT."""

    def test_clarify_command_exists(self):
        """COMMANDS_CONTENT contains 'project-clarify.md'."""
        commands = _commands()
        assert "project-clarify.md" in commands

    def test_clarify_has_frontmatter(self):
        """project-clarify.md has YAML frontmatter (starts with '---')."""
        content = _commands()["project-clarify.md"]
        assert content.strip().startswith("---")

    def test_clarify_references_arguments(self):
        """project-clarify.md references $ARGUMENTS."""
        content = _commands()["project-clarify.md"]
        assert "$ARGUMENTS" in content

    def test_clarify_has_clarified_brief(self):
        """project-clarify.md contains 'Clarified Brief' output section."""
        content = _commands()["project-clarify.md"]
        assert "Clarified Brief" in content


# ===========================================================================
# Routing table: /project-clarify entry
# ===========================================================================

class TestRoutingTableClarifyEntry:
    """The routing table must include the /project-clarify command."""

    def test_routing_table_contains_project_clarify(self):
        """RULES_MODULES['routing'] references 'project-clarify'."""
        routing = _rules()["routing"]
        assert "project-clarify" in routing
