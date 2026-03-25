"""
STORY-044: Pre-Act Consistency Check

Tests for:
- Phase 0.6 Consistency Check inserted into project-act.md (between Phase 0.5 and Phase 1)
- pactkit-analyze skill added to skills content
"""


def _commands():
    from pactkit.prompts import COMMANDS_CONTENT
    return COMMANDS_CONTENT


def _skills():
    """Return all skill-related content from pactkit.prompts.skills."""
    import pactkit.prompts.skills as skills_module
    return vars(skills_module)


# ===========================================================================
# Phase 0.6: Consistency Check in project-act.md
# ===========================================================================

class TestActPhase06ConsistencyCheck:
    """Phase 0.6 must be present in project-act.md between Phase 0.5 and Phase 1."""

    def test_phase_06_exists_in_act(self):
        """Phase 0.6 header exists in project-act.md."""
        content = _commands()["project-act.md"]
        assert "Phase 0.6" in content

    def test_phase_06_contains_consistency_check(self):
        """Phase 0.6 is named 'Consistency Check'."""
        content = _commands()["project-act.md"]
        assert "Consistency Check" in content

    def test_phase_06_is_non_blocking(self):
        """Phase 0.6 explicitly states it is non-blocking."""
        content = _commands()["project-act.md"]
        has_non_blocking = (
            "NON-BLOCKING" in content
            or "Non-blocking" in content
            or "non-blocking" in content
            or "advisory" in content.lower()
        )
        assert has_non_blocking

    def test_phase_06_mentions_spec_board_alignment(self):
        """Phase 0.6 mentions Spec <-> Board alignment."""
        content = _commands()["project-act.md"]
        has_alignment = (
            "Spec ↔ Board" in content
            or "Spec <-> Board" in content
            or ("Spec" in content and "Board" in content and "Alignment" in content)
            or ("Spec" in content and "Board" in content and "alignment" in content.lower())
        )
        assert has_alignment

    def test_phase_06_mentions_test_case_coverage(self):
        """Phase 0.6 mentions Test Case coverage."""
        content = _commands()["project-act.md"]
        assert "Test Case" in content or "test case" in content.lower()

    def test_phase_06_always_continues_to_phase_1(self):
        """Phase 0.6 always continues to Phase 1 regardless of findings."""
        content = _commands()["project-act.md"]
        # It should say "Continue" or "proceed" to Phase 1
        has_continue = (
            "Continue" in content
            or "proceed" in content.lower()
        )
        assert has_continue

    def test_phase_06_is_between_phase_05_and_phase_1(self):
        """Phase 0.6 appears between Phase 0.5 and Phase 1 in document order."""
        content = _commands()["project-act.md"]
        pos_05 = content.find("Phase 0.5")
        pos_06 = content.find("Phase 0.6")
        pos_1 = content.find("Phase 1:")
        assert pos_05 != -1, "Phase 0.5 must exist"
        assert pos_06 != -1, "Phase 0.6 must exist"
        assert pos_1 != -1, "Phase 1 must exist"
        assert pos_05 < pos_06 < pos_1, (
            f"Expected order Phase 0.5 ({pos_05}) < Phase 0.6 ({pos_06}) < Phase 1 ({pos_1})"
        )


# ===========================================================================
# pactkit-analyze skill
# ===========================================================================

class TestPactKitAnalyzeSkill:
    """pactkit-analyze skill must exist in the skills module."""

    def test_skill_analyze_md_exists(self):
        """SKILL_ANALYZE_MD variable exists in pactkit.prompts.skills."""
        skill_vars = _skills()
        assert "SKILL_ANALYZE_MD" in skill_vars

    def test_skill_analyze_md_has_content(self):
        """SKILL_ANALYZE_MD is a non-empty string."""
        skill_vars = _skills()
        analyze_md = skill_vars["SKILL_ANALYZE_MD"]
        assert isinstance(analyze_md, str)
        assert len(analyze_md.strip()) > 0

    def test_skill_analyze_md_references_pactkit_analyze(self):
        """SKILL_ANALYZE_MD references 'pactkit-analyze' as the skill name."""
        skill_vars = _skills()
        analyze_md = skill_vars["SKILL_ANALYZE_MD"]
        assert "pactkit-analyze" in analyze_md
