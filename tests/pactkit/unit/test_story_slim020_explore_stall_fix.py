"""Tests for STORY-slim-020: Fix Explore subagent stall during Plan Phase 1.

Verifies:
- Phase 1 has scope-limiting instructions and delegation template
- code-explorer maxTurns reduced to 15
- Other phases unchanged
"""

from pactkit.prompts import AGENTS_EXPERT, COMMANDS_CONTENT

PLAN = COMMANDS_CONTENT["project-plan.md"]
EXPLORER = AGENTS_EXPERT["code-explorer"]


class TestR1ScopeLimiting:
    """R1: Phase 1 must have scope-limiting instructions."""

    def test_file_count_limit_mentioned(self):
        """Phase 1 must recommend a file-count limit for subagent delegation."""
        # Must mention limiting files to read
        assert "file" in PLAN.lower() and ("limit" in PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")].lower()
                                           or "at most" in PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")].lower())

    def test_scope_guidance_in_phase1(self):
        """Phase 1 must instruct providing specific directory/function scope."""
        phase1 = PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")]
        has_scope = ("directory" in phase1.lower() or "scope" in phase1.lower()
                     or "target" in phase1.lower())
        assert has_scope, "Phase 1 must mention directory/scope/target for subagent"


class TestR2MaxTurns:
    """R2: code-explorer maxTurns must be reduced."""

    def test_max_turns_is_15(self):
        assert EXPLORER["maxTurns"] == 15

    def test_max_turns_not_50(self):
        assert EXPLORER["maxTurns"] != 50


class TestR3DelegationTemplate:
    """R3: Phase 1 must include a delegation template."""

    def test_delegation_template_present(self):
        phase1 = PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")]
        assert "Explore" in phase1, "Phase 1 must mention Explore subagent"

    def test_template_has_example_prompt(self):
        phase1 = PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")]
        # Must show an example of how to formulate the prompt
        has_example = ("example" in phase1.lower() or "prompt=" in phase1.lower()
                       or "at most" in phase1.lower())
        assert has_example, "Phase 1 must include an example delegation prompt"

    def test_template_specifies_output_format(self):
        phase1 = PLAN[PLAN.index("Phase 1"):PLAN.index("Phase 2")]
        has_output = ("return" in phase1.lower() or "output" in phase1.lower()
                      or "report" in phase1.lower())
        assert has_output, "Phase 1 must specify expected output from subagent"


class TestR4NoSideEffects:
    """R4: Other phases must not be altered."""

    def test_phase_0_intact(self):
        assert "Phase 0: The Thinking Process" in PLAN

    def test_phase_0_5_intact(self):
        assert "Phase 0.5: Init Guard" in PLAN

    def test_phase_0_7_intact(self):
        assert "Phase 0.7: Clarify Gate" in PLAN

    def test_phase_2_intact(self):
        assert "Phase 2: Design" in PLAN

    def test_phase_3_1_intact(self):
        assert "Phase 3.1: Story ID Generation" in PLAN

    def test_phase_3_2a_intact(self):
        assert "Phase 3.2a" in PLAN

    def test_phase_3_3_intact(self):
        assert "Phase 3.3: Board, Memory" in PLAN

    def test_explorer_boundaries_intact(self):
        """code-explorer core protocol must not be changed."""
        assert "Read-only operations" in EXPLORER["prompt"]
        assert "Do not write code" in EXPLORER["prompt"]
        assert "Do not modify Specs" in EXPLORER["prompt"]
