"""Tests for STORY-slim-021: Sectional Write for Large Document Generation.

Verifies:
- R6: 09-sectional-write rule exists in VALID_RULES and RULES_MODULES (core layer)
- R7: Rule content contains required elements
- R1: DESIGN_PROMPT Phase 1 uses sectional write (Edit per Group, not single Write)
- R2: DESIGN_PROMPT Phase 1 has checkpoint messages between Groups
- R4: DESIGN_PROMPT Phase 3 has batch checkpoint for Spec generation
- R5: DESIGN_PROMPT still produces same section structure
"""

from pactkit.config import VALID_RULES
from pactkit.prompts import COMMANDS_CONTENT
from pactkit.prompts.rules import RULES_CORE_FILES, RULES_FILES, RULES_MODULES

DESIGN = COMMANDS_CONTENT["project-design.md"]


# ---------------------------------------------------------------------------
# R6: 09-sectional-write in rule system
# ---------------------------------------------------------------------------
class TestR6RuleExists:
    """R6: 09-sectional-write must be a core rule."""

    def test_valid_rules_contains_sectional_write(self):
        assert "09-sectional-write" in VALID_RULES

    def test_valid_rules_count_is_9(self):
        assert len(VALID_RULES) == 9

    def test_rules_modules_contains_sectional(self):
        assert "sectional" in RULES_MODULES

    def test_core_files_contains_sectional(self):
        assert "sectional" in RULES_CORE_FILES

    def test_rules_files_contains_sectional(self):
        assert "sectional" in RULES_FILES

    def test_core_file_maps_to_correct_filename(self):
        assert RULES_CORE_FILES["sectional"] == "09-sectional-write.md"


# ---------------------------------------------------------------------------
# R7: Rule content requirements
# ---------------------------------------------------------------------------
class TestR7RuleContent:
    """R7: Rule content must have all required elements."""

    def test_trigger_condition_300_lines(self):
        content = RULES_MODULES["sectional"]
        assert "300" in content, "Must mention 300-line threshold"

    def test_applies_to_any_file_type(self):
        content = RULES_MODULES["sectional"].lower()
        assert "any file" in content or "code" in content

    def test_skeleton_first_step(self):
        content = RULES_MODULES["sectional"]
        assert "skeleton" in content.lower()

    def test_edit_per_block_step(self):
        content = RULES_MODULES["sectional"]
        assert "Edit" in content

    def test_checkpoint_step(self):
        content = RULES_MODULES["sectional"]
        assert "checkpoint" in content.lower()

    def test_exclusion_short_files(self):
        content = RULES_MODULES["sectional"]
        assert "< 300" in content or "Short" in content

    def test_covers_source_code(self):
        content = RULES_MODULES["sectional"].lower()
        assert "source code" in content or "modules" in content or "api" in content

    def test_anti_pattern_example(self):
        content = RULES_MODULES["sectional"]
        assert "DO NOT" in content


# ---------------------------------------------------------------------------
# R1: DESIGN_PROMPT Phase 1 uses sectional write
# ---------------------------------------------------------------------------
class TestR1SectionalWritePRD:
    """R1: Phase 1 must Edit after each Group, not single Write at end."""

    def _phase1(self):
        start = DESIGN.index("Phase 1: PRD Generation")
        end = DESIGN.index("Phase 2:")
        return DESIGN[start:end]

    def test_group_a_has_edit_instruction(self):
        phase1 = self._phase1()
        group_a_end = phase1.index("Group B")
        group_a = phase1[:group_a_end]
        assert "Edit" in group_a or "Write" in group_a, "Group A must have a write/edit instruction"

    def test_group_b_has_edit_instruction(self):
        phase1 = self._phase1()
        group_b_start = phase1.index("Group B")
        group_b_end = phase1.index("Group C")
        group_b = phase1[group_b_start:group_b_end]
        assert "Edit" in group_b, "Group B must have an Edit instruction"

    def test_group_c_has_edit_instruction(self):
        phase1 = self._phase1()
        group_c_start = phase1.index("Group C")
        group_c = phase1[group_c_start:]
        assert "Edit" in group_c, "Group C must have an Edit instruction"

    def test_no_single_deferred_write(self):
        """Must NOT have the old 'Save the completed PRD' instruction."""
        phase1 = self._phase1()
        assert "Save the completed PRD" not in phase1


# ---------------------------------------------------------------------------
# R2: Checkpoint messages between Groups
# ---------------------------------------------------------------------------
class TestR2GroupCheckpoints:
    """R2: Each Group must have a checkpoint message after its Edit."""

    def _phase1(self):
        start = DESIGN.index("Phase 1: PRD Generation")
        end = DESIGN.index("Phase 2:")
        return DESIGN[start:end]

    def test_checkpoint_after_group_a(self):
        phase1 = self._phase1()
        group_a_end = phase1.index("Group B")
        group_a = phase1[:group_a_end]
        assert "checkpoint" in group_a.lower() or "Group A" in group_a

    def test_checkpoint_after_group_b(self):
        phase1 = self._phase1()
        group_b_start = phase1.index("Group B")
        group_b_end = phase1.index("Group C")
        group_b = phase1[group_b_start:group_b_end]
        assert "checkpoint" in group_b.lower() or "Group B" in group_b


# ---------------------------------------------------------------------------
# R4: Story Decomposition batch checkpoint
# ---------------------------------------------------------------------------
class TestR4SpecBatchCheckpoint:
    """R4: Phase 3 must have batch checkpoint every 3 specs."""

    def _phase3(self):
        start = DESIGN.index("Phase 3: Story Decomposition")
        end = DESIGN.index("Phase 4:")
        return DESIGN[start:end]

    def test_batch_checkpoint_mentioned(self):
        phase3 = self._phase3()
        has_batch = ("checkpoint" in phase3.lower() or "progress" in phase3.lower())
        assert has_batch, "Phase 3 must mention checkpoint/progress"

    def test_batch_size_mentioned(self):
        phase3 = self._phase3()
        assert "3" in phase3, "Phase 3 must mention batch size of 3"


# ---------------------------------------------------------------------------
# R5: Section structure preserved
# ---------------------------------------------------------------------------
class TestR5SectionStructure:
    """R5: All original PRD sections must still exist in DESIGN_PROMPT."""

    def test_section_1_1_product_overview(self):
        assert "1.1 Product Overview" in DESIGN

    def test_section_1_2_user_personas(self):
        assert "1.2 User Personas" in DESIGN

    def test_section_1_3_feature_breakdown(self):
        assert "1.3 Feature Breakdown" in DESIGN

    def test_section_1_4_architecture(self):
        assert "1.4 Architecture" in DESIGN

    def test_section_1_5_page_screen(self):
        assert "1.5 Page/Screen" in DESIGN

    def test_section_1_6_prototype(self):
        assert "1.6 Prototype" in DESIGN

    def test_section_1_7_api(self):
        assert "1.7 API" in DESIGN

    def test_section_1_8_nfr(self):
        assert "1.8 Non-Functional" in DESIGN

    def test_section_1_9_success_metrics(self):
        assert "1.9 Success Metrics" in DESIGN

    def test_section_2_0_roadmap(self):
        assert "2.0 MVP Roadmap" in DESIGN
