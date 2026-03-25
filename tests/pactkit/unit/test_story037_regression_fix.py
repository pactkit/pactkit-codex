"""Tests for STORY-037: Fix regression decision tree — replace unverifiable conditions.

AC1: Condition 1 uses git-diff check instead of unverifiable session freshness
AC2: Condition 3 uses fallback-tolerant check (test mapping OR test count threshold)
AC3: Decision logging present in Done regression output
AC4: Act regression uses explicit fan-in criteria instead of "if unsure"
"""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# AC1: Condition 1 is verifiable (git diff based)
# ==============================================================================
class TestAC1VerifiableCondition1:
    """Done decision tree Condition 1 must use git-diff, not session freshness."""

    def test_no_session_freshness_language(self):
        """The old 'updated in the current session' phrasing must be gone."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'updated in the current session' not in done

    def test_uses_git_diff_for_graph_check(self):
        """Condition 1 should reference git diff to verify graph freshness."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        # Must mention git diff in the context of code_graph.mmd
        assert 'git diff' in lower
        assert 'code_graph' in lower

    def test_condition_1_is_verifiable(self):
        """Condition 1 must contain a concrete verification command."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Should reference checking recent commit or staged changes
        assert 'HEAD~1' in done or 'HEAD' in done


# ==============================================================================
# AC2: Condition 3 tolerates non-standard test naming
# ==============================================================================
class TestAC2FallbackTolerantCondition3:
    """Done decision tree Condition 3 must have a fallback for non-standard naming."""

    def test_no_strict_all_mapping_requirement(self):
        """The old 'ALL changed source files have direct test mappings' must be relaxed."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Should NOT require ALL files to have mappings
        assert 'ALL changed source files have direct test mappings' not in done

    def test_has_threshold_fallback(self):
        """Should have a test count or time threshold as fallback."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        # Must mention some kind of threshold (count or time)
        assert '500' in done or 'threshold' in lower or 'fast enough' in lower

    def test_still_mentions_test_map_pattern(self):
        """test_map_pattern should still be referenced (but not as strict gate)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'test_map_pattern' in done


# ==============================================================================
# AC3: Decision logging present
# ==============================================================================
class TestAC3DecisionLogging:
    """Done regression gate should log which path was chosen and why."""

    def test_has_logging_instruction(self):
        """Done should instruct the agent to log the regression decision."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        # Must mention logging/reporting the decision
        assert ('log' in lower or 'report' in lower or 'output' in lower)
        assert ('which' in lower or 'reason' in lower or 'condition' in lower)

    def test_shows_example_format(self):
        """Should include an example of the decision log format."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Must have a concrete example like "Regression: FULL" or "Regression: INCREMENTAL"
        assert 'Regression:' in done or 'regression:' in done


# ==============================================================================
# AC4: Act regression uses explicit criteria
# ==============================================================================
class TestAC4ActExplicitCriteria:
    """Act regression should use fan-in criteria instead of 'if unsure'."""

    def test_no_if_unsure_language(self):
        """The vague 'if unsure about change scope' phrasing must be gone."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'if unsure about change scope' not in act

    def test_has_explicit_full_suite_criteria(self):
        """Act should have explicit criteria for when to run full suite."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        # Must mention fan-in, import count, or dependency-based criteria
        assert ('import' in lower or 'fan-in' in lower or
                '3+' in act or 'dependents' in lower or 'imported by' in lower)

    def test_preserves_pre_existing_test_protocol(self):
        """The pre-existing test failure STOP protocol must be preserved."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'DO NOT modify' in act
        assert 'STOP' in act


# ==============================================================================
# AC5: Fast-suite threshold (SHOULD)
# ==============================================================================
class TestAC5FastSuiteThreshold:
    """Done should have a fast-suite threshold to skip decision tree."""

    def test_has_fast_suite_skip(self):
        """If total test time is small, skip the decision tree entirely."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        # Must mention time-based threshold or "fast" suite
        assert ('30 second' in lower or 'fast' in lower or
                'small suite' in lower or 'skip the decision tree' in lower)


# ==============================================================================
# Backward compatibility: existing tests must still pass
# ==============================================================================
class TestBackwardCompat:
    """Changes must not break existing regression keywords."""

    def test_done_still_has_full_regression(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'full regression' in done.lower() or 'full suite' in done.lower()

    def test_done_still_has_incremental(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'incremental' in done.lower()

    def test_done_still_has_fallback(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_done_still_has_decision_tree(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'Decision Tree' in done

    def test_act_still_has_fallback(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_act_still_has_git_diff(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'git diff' in act.lower()
