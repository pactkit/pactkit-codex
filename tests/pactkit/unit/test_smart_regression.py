"""Tests for STORY-033: Smart Regression — Incremental Testing for Act/Check, Impact-Based Done Gate."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Act Runs Incremental Tests
# ==============================================================================
class TestActIncremental:
    """STORY-033 Scenario 1: Act Phase 3 instructs incremental testing."""

    def test_act_has_git_diff(self):
        """Act should instruct using git diff to identify changed modules."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'git diff' in act.lower()

    def test_act_has_incremental_keyword(self):
        """Act should mention incremental or related-test mapping."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'incremental' in lower or 'related test' in lower or 'changed module' in lower

    def test_act_has_fallback(self):
        """Act must have a fallback to full test suite."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_act_still_has_lang_profiles(self):
        """Act must still reference LANG_PROFILES for the test runner."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'LANG_PROFILES' in act or 'pactkit.yaml' in act


# ==============================================================================
# Scenario 2: Check Runs Incremental Unit Tests
# ==============================================================================
class TestCheckIncremental:
    """STORY-033 Scenario 2: Check Phase 5 uses incremental unit tests."""

    def test_check_has_incremental_keyword(self):
        """Check should mention incremental or related-test mapping."""
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        lower = check.lower()
        assert 'incremental' in lower or 'related test' in lower or 'changed module' in lower

    def test_check_still_runs_story_e2e(self):
        """Check must still run the story-specific E2E test."""
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        assert 'test_{STORY_ID}' in check or 'specific test file' in check.lower()

    def test_check_has_fallback(self):
        """Check must have a fallback to full unit test suite."""
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        lower = check.lower()
        assert 'fallback' in lower or 'fall back' in lower


# ==============================================================================
# Scenario 3: Done Triggers Full Regression on Core Module Change
# ==============================================================================
class TestDoneFullOnCoreModule:
    """STORY-033 Scenario 3: Done triggers full regression on core module change."""

    def test_done_has_impact_analysis(self):
        """Done should mention impact analysis or fan-out or dependency."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert ('impact' in lower or 'fan-out' in lower or
                'core module' in lower or 'dependents' in lower)

    def test_done_mentions_code_graph(self):
        """Done should reference code_graph.mmd for dependency analysis."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'code_graph' in done.lower() or 'dependency' in done.lower()


# ==============================================================================
# Scenario 4: Done Runs Incremental on Leaf Module Change
# ==============================================================================
class TestDoneIncrementalOnLeaf:
    """STORY-033 Scenario 4: Done runs incremental on leaf module change."""

    def test_done_has_incremental_path(self):
        """Done should have an incremental testing path."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'incremental' in lower or 'related test' in lower

    def test_done_has_decision_tree(self):
        """Done should have a decision tree (full vs incremental)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert ('full regression' in lower or 'full suite' in lower)
        assert (
            'incremental' in lower or 'related test' in lower
        )


# ==============================================================================
# Scenario 5: Done Triggers Full Regression on Version Change
# ==============================================================================
class TestDoneFullOnVersionChange:
    """STORY-033 Scenario 5: Done triggers full regression on version change."""

    def test_done_mentions_version_trigger(self):
        """Done should mention version change as a full-regression trigger."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'version' in lower
        assert ('full' in lower or 'regression' in lower)

    def test_done_mentions_pactkit_yaml(self):
        """Done should reference pactkit.yaml for version detection."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'pactkit.yaml' in done


# ==============================================================================
# Scenario 6: LANG_PROFILES Has Test Map Pattern
# ==============================================================================
class TestLangProfilesTestMap:
    """STORY-033 Scenario 6: LANG_PROFILES has test_map_pattern field."""

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_has_test_map_pattern(self, lang):
        p = _prompts()
        profile = p.LANG_PROFILES[lang]
        assert 'test_map_pattern' in profile, f"{lang} missing test_map_pattern"

    def test_python_pattern_correct(self):
        p = _prompts()
        pattern = p.LANG_PROFILES['python']['test_map_pattern']
        assert 'test_' in pattern
        assert '{module}' in pattern


# ==============================================================================
# Scenario 7: Fallback to Full Suite
# ==============================================================================
class TestFallbackToFull:
    """STORY-033 Scenario 7: All commands have fallback to full suite."""

    def test_act_fallback(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_check_fallback(self):
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        lower = check.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_done_fallback(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'fallback' in lower or 'fall back' in lower


# ==============================================================================
# Scenario 8: Hotfix Uses Incremental Testing
# ==============================================================================
class TestHotfixIncremental:
    """STORY-033 Scenario 8: Hotfix uses incremental testing."""

    def test_hotfix_has_incremental_keyword(self):
        p = _prompts()
        hotfix = p.COMMANDS_CONTENT['project-hotfix.md']
        lower = hotfix.lower()
        assert 'incremental' in lower or 'related test' in lower or 'changed module' in lower

    def test_hotfix_has_fallback(self):
        p = _prompts()
        hotfix = p.COMMANDS_CONTENT['project-hotfix.md']
        lower = hotfix.lower()
        assert 'fallback' in lower or 'fall back' in lower


# ==============================================================================
# Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """STORY-033: All existing commands and agents still present."""

    def test_existing_commands_present(self):
        p = _prompts()
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_agents_unchanged(self):
        p = _prompts()
        expected_agents = [
            'system-architect', 'senior-developer', 'qa-engineer',
            'repo-maintainer', 'system-medic', 'security-auditor',
            'visual-architect', 'code-explorer',
        ]
        for agent in expected_agents:
            assert agent in p.AGENTS_EXPERT, f"Missing agent {agent}"

    def test_lang_profiles_existing_fields_preserved(self):
        """Existing LANG_PROFILES fields must still be present."""
        p = _prompts()
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        required = list(LANG_PROFILE_REQUIRED_KEYS)
        for lang in ['python', 'node', 'go', 'java']:
            for field in required:
                assert field in p.LANG_PROFILES[lang], f"{lang} missing {field}"

    def test_done_still_has_gate(self):
        """Done regression gate must still stop on failure."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'stop' in lower or 'do not proceed' in lower
