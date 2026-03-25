"""
STORY-057: Playbook Implicit Instruction Cleanup

Verify:
- AC1: Regression Gate cascade preserved (Step 1.3 → Step 1.6, no Step 1.5)
- AC2: Step 1.5 text fully removed (no "Fast-Suite Shortcut", "Step 1.5", "< 30 seconds")
- AC3: Clarify Gate signals explicitly labeled with [High] or [Medium]
- AC4: Clarify Gate trigger logic unchanged
"""
import importlib


def _commands():
    from pactkit.prompts import commands as cmd
    importlib.reload(cmd)
    return cmd


# ===========================================================================
# AC1: Regression Gate cascade preserved after Step 1.5 removal
# ===========================================================================

class TestRegressionGateCascade:
    """After Step 1.5 removal, Step 1.3 fall-through goes to Step 1.6."""

    def _done(self) -> str:
        return _commands().COMMANDS_CONTENT['project-done.md']

    def test_step_1_3_falls_through_to_step_1_6(self):
        """Step 1.3 Doc-Only fall-through must reference Step 1.6, not Step 1.5."""
        done = self._done()
        # Find the "any source files changed" line in Step 1.3
        assert 'Step 1.6' in done, \
            "Step 1.3 fall-through must reference Step 1.6 (Release Gate)"

    def test_step_1_6_still_exists(self):
        """Step 1.6 Release Gate must still exist."""
        done = self._done()
        assert 'Step 1.6' in done and 'Release Gate' in done

    def test_step_1_7_still_exists(self):
        """Step 1.7 Impact-Based Analysis must still exist."""
        done = self._done()
        assert 'Step 1.7' in done and 'Impact-Based' in done

    def test_step_2_decision_tree_still_exists(self):
        """Step 2 Decision Tree must still exist."""
        done = self._done()
        assert 'Decision Tree' in done

    def test_step_3_gate_still_exists(self):
        """Step 3 Gate must still exist."""
        done = self._done()
        assert 'Step 3' in done
        assert 'STOP' in done


# ===========================================================================
# AC2: Step 1.5 text fully removed
# ===========================================================================

class TestStep15Removed:
    """No trace of Fast-Suite Shortcut in project-done.md."""

    def _done(self) -> str:
        return _commands().COMMANDS_CONTENT['project-done.md']

    def test_no_fast_suite_shortcut(self):
        done = self._done()
        assert 'Fast-Suite Shortcut' not in done, \
            "project-done.md must not contain 'Fast-Suite Shortcut'"

    def test_no_step_1_5_reference(self):
        done = self._done()
        assert 'Step 1.5' not in done, \
            "project-done.md must not contain 'Step 1.5'"

    def test_no_30_seconds_reference(self):
        done = self._done()
        assert '30 second' not in done.lower(), \
            "project-done.md must not contain '< 30 seconds' heuristic"


# ===========================================================================
# AC3: Clarify Gate signals explicitly labeled
# ===========================================================================

class TestClarifyGateSignalLabels:
    """Each of the 6 ambiguity signals must have [High] or [Medium] label."""

    def _plan(self) -> str:
        return _commands().COMMANDS_CONTENT['project-plan.md']

    def test_no_quantitative_metrics_is_high(self):
        plan = self._plan()
        # Find the signal line and check for [High] label
        for line in plan.split('\n'):
            if 'quantitative metrics' in line.lower():
                assert '[High]' in line, \
                    "'No quantitative metrics' signal must be labeled [High]"
                return
        raise AssertionError("Signal 'No quantitative metrics' not found")

    def test_no_boundary_conditions_is_high(self):
        plan = self._plan()
        for line in plan.split('\n'):
            if 'boundary conditions' in line.lower():
                assert '[High]' in line, \
                    "'No boundary conditions' signal must be labeled [High]"
                return
        raise AssertionError("Signal 'No boundary conditions' not found")

    def test_no_technical_constraints_is_medium(self):
        plan = self._plan()
        for line in plan.split('\n'):
            if 'technical constraints' in line.lower():
                assert '[Medium]' in line, \
                    "'No technical constraints' signal must be labeled [Medium]"
                return
        raise AssertionError("Signal 'No technical constraints' not found")

    def test_single_sentence_is_low(self):
        """BUG-slim-002 R4: Single sentence downgraded from Medium to Low."""
        plan = self._plan()
        for line in plan.split('\n'):
            if 'single sentence' in line.lower() or '< 15 words' in line:
                assert '[Low]' in line, \
                    "'Single sentence input' signal must be labeled [Low] (BUG-slim-002 R4)"
                return
        raise AssertionError("Signal 'Single sentence input' not found")

    def test_vague_quantifiers_is_medium(self):
        plan = self._plan()
        for line in plan.split('\n'):
            if 'vague quantifiers' in line.lower():
                assert '[Medium]' in line, \
                    "'Vague quantifiers' signal must be labeled [Medium]"
                return
        raise AssertionError("Signal 'Vague quantifiers' not found")

    def test_no_target_user_is_medium(self):
        plan = self._plan()
        for line in plan.split('\n'):
            if 'target user' in line.lower() and 'no ' in line.lower():
                assert '[Medium]' in line, \
                    "'No target user specified' signal must be labeled [Medium]"
                return
        raise AssertionError("Signal 'No target user specified' not found")


# ===========================================================================
# AC4: Clarify Gate trigger logic unchanged
# ===========================================================================

class TestClarifyGateTriggerLogic:
    """Trigger thresholds must remain unchanged."""

    def _plan(self) -> str:
        return _commands().COMMANDS_CONTENT['project-plan.md']

    def test_auto_trigger_on_2_high(self):
        plan = self._plan()
        assert '2 High' in plan or '≥ 2 High' in plan, \
            "Trigger logic must retain '≥ 2 High signals → Auto-trigger'"

    def test_auto_trigger_on_1_high_2_medium(self):
        plan = self._plan()
        assert '1 High' in plan and '2 Medium' in plan, \
            "Trigger logic must retain '1 High + ≥ 2 Medium → Auto-trigger'"

    def test_suggest_on_2_medium(self):
        plan = self._plan()
        # Find the suggest line
        found = False
        for line in plan.split('\n'):
            if '2 Medium' in line and 'Suggest' in line:
                found = True
                break
        assert found, "Trigger logic must retain '≥ 2 Medium → Suggest'"
