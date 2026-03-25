"""Tests for STORY-065: Sprint Stage A Model Consistency.

Verifies:
- Stage A is split into A1-Plan (opus) and A2-Act (sonnet)
- Both sub-stages retain isolation="worktree"
- Phase 0 reads agent_models from pactkit.yaml with fallback defaults
- Reference table has separate Plan and Act rows
- Pre-existing Stage A/B/C isolation tests still pass (AC5 — covered by test_story048)
"""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _stage_a_section():
    from pactkit.prompts import SPRINT_PROMPT
    a_start = SPRINT_PROMPT.find('Stage A')
    b_start = SPRINT_PROMPT.find('Stage B', a_start)
    assert a_start != -1, "Stage A not found in SPRINT_PROMPT"
    assert b_start != -1, "Stage B not found after Stage A"
    return SPRINT_PROMPT[a_start:b_start]


def _phase0_section():
    from pactkit.prompts import SPRINT_PROMPT
    p0_start = SPRINT_PROMPT.find('Phase 0')
    p1_start = SPRINT_PROMPT.find('Phase 1', p0_start)
    assert p0_start != -1, "Phase 0 not found in SPRINT_PROMPT"
    return SPRINT_PROMPT[p0_start:p1_start]


# ---------------------------------------------------------------------------
# AC1: Stage A1 (Plan) uses opus
# ---------------------------------------------------------------------------

class TestAC1PlanModel:
    def test_stage_a_contains_opus(self):
        """Stage A section must specify opus for the Plan sub-stage."""
        section = _stage_a_section()
        assert 'model: opus' in section or 'model="opus"' in section, (
            "Stage A section must contain 'model: opus' for Plan sub-stage. "
            f"Got:\n{section}"
        )

    def test_stage_a1_exists(self):
        """Stage A must have an A1 sub-stage."""
        section = _stage_a_section()
        assert 'A1' in section, "Stage A1 (Plan) sub-stage not found in Stage A section"


# ---------------------------------------------------------------------------
# AC2: Stage A2 (Act) uses sonnet
# ---------------------------------------------------------------------------

class TestAC2ActModel:
    def test_stage_a_contains_sonnet_for_act(self):
        """Stage A section must specify sonnet for the Act sub-stage."""
        section = _stage_a_section()
        assert 'model: sonnet' in section or 'model="sonnet"' in section, (
            "Stage A section must contain 'model: sonnet' for Act sub-stage. "
            f"Got:\n{section}"
        )

    def test_stage_a2_exists(self):
        """Stage A must have an A2 sub-stage."""
        section = _stage_a_section()
        assert 'A2' in section, "Stage A2 (Act) sub-stage not found in Stage A section"


# ---------------------------------------------------------------------------
# AC3: Both sub-stages retain isolation
# ---------------------------------------------------------------------------

class TestAC3IsolationPreserved:
    def test_stage_a1_has_isolation(self):
        """Stage A1 (Plan) must retain isolation."""
        section = _stage_a_section()
        a1_start = section.find('A1')
        a2_start = section.find('A2', a1_start)
        assert a1_start != -1 and a2_start != -1, "A1/A2 markers not found"
        a1_section = section[a1_start:a2_start]
        assert 'isolation' in a1_section, (
            f"Stage A1 section missing 'isolation':\n{a1_section}"
        )

    def test_stage_a2_has_isolation(self):
        """Stage A2 (Act) must retain isolation."""
        section = _stage_a_section()
        a2_start = section.find('A2')
        assert a2_start != -1, "A2 marker not found"
        a2_section = section[a2_start:]
        assert 'isolation' in a2_section, (
            f"Stage A2 section missing 'isolation':\n{a2_section}"
        )


# ---------------------------------------------------------------------------
# AC4: Reference table has separate Plan and Act rows
# ---------------------------------------------------------------------------

class TestAC4ReferenceTable:
    def test_reference_table_has_plan_row(self):
        """Reference table must have a Plan row."""
        from pactkit.prompts import SPRINT_PROMPT
        table_start = SPRINT_PROMPT.find('Subagent Reference')
        assert table_start != -1, "Subagent Reference table not found"
        table_section = SPRINT_PROMPT[table_start:]
        assert '| Plan' in table_section or '| Plan ' in table_section, (
            "Reference table missing Plan row"
        )

    def test_reference_table_has_act_row(self):
        """Reference table must have an Act row."""
        from pactkit.prompts import SPRINT_PROMPT
        table_start = SPRINT_PROMPT.find('Subagent Reference')
        assert table_start != -1, "Subagent Reference table not found"
        table_section = SPRINT_PROMPT[table_start:]
        assert '| Act' in table_section or '| Act ' in table_section, (
            "Reference table missing Act row"
        )

    def test_reference_table_no_merged_build_row(self):
        """Old 'Build (Plan+Act merged)' row must be replaced."""
        from pactkit.prompts import SPRINT_PROMPT
        table_start = SPRINT_PROMPT.find('Subagent Reference')
        table_section = SPRINT_PROMPT[table_start:]
        assert 'Plan+Act merged' not in table_section, (
            "Old merged Build row still present — should be split into Plan and Act"
        )


# ---------------------------------------------------------------------------
# AC6: Phase 0 reads agent_models from pactkit.yaml
# ---------------------------------------------------------------------------

class TestAC6ConfigAwareModelSelection:
    def test_phase0_reads_agent_models(self):
        """Phase 0 must instruct reading agent_models from pactkit.yaml."""
        section = _phase0_section()
        assert 'agent_models' in section, (
            "Phase 0 must reference 'agent_models' config key"
        )

    def test_phase0_references_pactkit_yaml(self):
        """Phase 0 must reference pactkit.yaml as config source."""
        section = _phase0_section()
        assert 'pactkit.yaml' in section, (
            "Phase 0 must reference 'pactkit.yaml'"
        )

    def test_phase0_uses_system_architect_key(self):
        """Phase 0 must use system-architect key for Plan model lookup."""
        section = _phase0_section()
        assert 'system-architect' in section, (
            "Phase 0 must look up 'system-architect' in agent_models"
        )

    def test_phase0_uses_senior_developer_key(self):
        """Phase 0 must use senior-developer key for Act model lookup."""
        section = _phase0_section()
        assert 'senior-developer' in section, (
            "Phase 0 must look up 'senior-developer' in agent_models"
        )


# ---------------------------------------------------------------------------
# AC7: Fallback to defaults when agent_models not configured
# ---------------------------------------------------------------------------

class TestAC7FallbackDefaults:
    def test_phase0_specifies_opus_as_plan_default(self):
        """Phase 0 must specify opus as default Plan model."""
        section = _phase0_section()
        assert 'opus' in section, (
            "Phase 0 must specify 'opus' as the default Plan model"
        )

    def test_phase0_specifies_sonnet_as_act_default(self):
        """Phase 0 must specify sonnet as default Act model."""
        section = _phase0_section()
        assert 'sonnet' in section, (
            "Phase 0 must specify 'sonnet' as the default Act model"
        )

    def test_phase0_mentions_fallback(self):
        """Phase 0 must describe fallback behavior."""
        section = _phase0_section()
        assert 'fallback' in section.lower() or 'default' in section.lower(), (
            "Phase 0 must describe fallback/default behavior for missing config"
        )
