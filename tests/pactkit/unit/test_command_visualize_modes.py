"""Tests for STORY-010: Commands must reference visualize multi-mode."""
from pactkit.prompts import COMMANDS_CONTENT
from pactkit.prompts.agents import AGENTS_EXPERT


# ==============================================================================
# Scenario 1: pactkit-trace skill uses call graph
# ==============================================================================
class TestProjectTrace:
    def test_trace_skill_has_call_mode(self):
        from pactkit.prompts import SKILL_TRACE_MD
        assert '--mode call' in SKILL_TRACE_MD

    def test_trace_skill_has_entry_param(self):
        from pactkit.prompts import SKILL_TRACE_MD
        assert '--entry' in SKILL_TRACE_MD

    def test_trace_skill_references_call_graph_mmd(self):
        from pactkit.prompts import SKILL_TRACE_MD
        assert 'call_graph.mmd' in SKILL_TRACE_MD


# ==============================================================================
# Scenario 2: project-plan mode selection guidance
# ==============================================================================
class TestProjectPlan:
    def test_plan_has_mode_class(self):
        content = COMMANDS_CONTENT['project-plan.md']
        assert '--mode class' in content

    def test_plan_has_mode_call(self):
        content = COMMANDS_CONTENT['project-plan.md']
        assert '--mode call' in content

    def test_plan_has_mode_selection_guidance(self):
        content = COMMANDS_CONTENT['project-plan.md']
        # Should mention at least two modes to guide selection
        assert 'class' in content
        assert 'call' in content


# ==============================================================================
# Scenario 3: project-act full graph update
# ==============================================================================
class TestProjectAct:
    def test_act_has_call_entry(self):
        content = COMMANDS_CONTENT['project-act.md']
        assert '--mode call' in content or '--entry' in content

    def test_act_phase4_updates_class_graph(self):
        content = COMMANDS_CONTENT['project-act.md']
        assert '--mode class' in content


# ==============================================================================
# Scenario 4: pactkit-doctor skill class health check
# ==============================================================================
class TestProjectDoctor:
    def test_doctor_skill_has_class_mode(self):
        from pactkit.prompts import SKILL_DOCTOR_MD
        assert '--mode class' in SKILL_DOCTOR_MD


# ==============================================================================
# Scenario 5: project-init full mode discovery
# ==============================================================================
class TestProjectInit:
    def test_init_has_class_mode(self):
        content = COMMANDS_CONTENT['project-init.md']
        assert '--mode class' in content


# ==============================================================================
# Scenario 6: Agents know about new modes
# ==============================================================================
class TestAgents:
    def test_system_architect_knows_class_mode(self):
        content = AGENTS_EXPERT['system-architect']['prompt']
        assert '--mode class' in content or 'class' in content.lower()

    def test_senior_developer_knows_call_mode(self):
        content = AGENTS_EXPERT['senior-developer']['prompt']
        assert '--mode call' in content or '--entry' in content
