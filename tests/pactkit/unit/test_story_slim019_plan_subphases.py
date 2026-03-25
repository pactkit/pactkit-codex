"""Tests for STORY-slim-019: Split Plan Phase 3.2 into sub-steps.

Verifies the project-plan prompt template has 4 sub-phases (3.2a-3.2d)
with explicit output checkpoints, while preserving all required content.
"""

from pactkit.prompts import COMMANDS_CONTENT

PLAN = COMMANDS_CONTENT["project-plan.md"]


class TestSubPhaseStructure:
    """R1: Phase 3.2 must be split into 4 sub-phases."""

    def test_has_phase_3_2a(self):
        assert "Phase 3.2a" in PLAN

    def test_has_phase_3_2b(self):
        assert "Phase 3.2b" in PLAN

    def test_has_phase_3_2c(self):
        assert "Phase 3.2c" in PLAN

    def test_has_phase_3_2d(self):
        assert "Phase 3.2d" in PLAN

    def test_subphases_in_order(self):
        a = PLAN.index("Phase 3.2a")
        b = PLAN.index("Phase 3.2b")
        c = PLAN.index("Phase 3.2c")
        d = PLAN.index("Phase 3.2d")
        assert a < b < c < d


class TestOutputCheckpoints:
    """R1: Each sub-phase must have an output checkpoint."""

    def test_3_2a_checkpoint(self):
        assert "Spec skeleton filled" in PLAN or "Spec skeleton written" in PLAN

    def test_3_2b_checkpoint(self):
        assert "Acceptance criteria written" in PLAN

    def test_3_2c_checkpoint(self):
        assert "Security scope filled" in PLAN or "Security scope appended" in PLAN

    def test_3_2d_checkpoint(self):
        assert "Spec lint passed" in PLAN


class TestPreservedContent:
    """R1+R3: All original required content must still be present."""

    def test_metadata_table_instructions(self):
        assert "Metadata Table" in PLAN

    def test_requirements_section_rfc2119(self):
        assert "RFC 2119" in PLAN

    def test_acceptance_criteria_given_when_then(self):
        assert "Given/When/Then" in PLAN

    def test_release_field_from_yaml(self):
        assert "Release" in PLAN and "pyproject.toml" in PLAN

    def test_implementation_steps_optional(self):
        assert "Implementation Steps" in PLAN

    def test_security_scope_sec_scope_cli(self):
        assert "pactkit sec-scope" in PLAN

    def test_spec_lint_self_check(self):
        assert "pactkit spec-lint" in PLAN

    def test_target_call_chain(self):
        assert "Target Call Chain" in PLAN


class TestNoSideEffects:
    """R3: Other phases must not be altered."""

    def test_phase_0_intact(self):
        assert "Phase 0: The Thinking Process" in PLAN

    def test_phase_0_5_intact(self):
        assert "Phase 0.5: Init Guard" in PLAN

    def test_phase_0_7_intact(self):
        assert "Phase 0.7: Clarify Gate" in PLAN

    def test_phase_1_intact(self):
        assert "Phase 1: Archaeology" in PLAN

    def test_phase_2_intact(self):
        assert "Phase 2: Design" in PLAN

    def test_phase_3_1_intact(self):
        assert "Phase 3.1: Story ID Generation" in PLAN

    def test_phase_3_3_intact(self):
        assert "Phase 3.3: Board, Memory" in PLAN
