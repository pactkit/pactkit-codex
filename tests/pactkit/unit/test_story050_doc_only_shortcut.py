"""STORY-050: Doc-Only Regression Shortcut — skip full test suite for non-source changes."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# =============================================================================
# AC1 / R1: Done command has Doc-Only Shortcut (Step 1.3)
# =============================================================================
class TestDoneDocOnlyShortcut:
    """R1: Done Phase 2.5 MUST have Step 1.3 Doc-Only Shortcut before Step 1.5."""

    def test_done_has_doc_only_keyword(self):
        """Done prompt must contain doc-only shortcut language."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'doc-only' in lower or 'doc only' in lower, \
            'Done prompt missing doc-only shortcut language'

    def test_doc_only_before_release_gate(self):
        """Doc-Only Shortcut (Step 1.3) must appear before Release Gate (Step 1.6)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        doc_only_idx = done.lower().find('doc-only')
        if doc_only_idx < 0:
            doc_only_idx = done.lower().find('doc only')
        release_gate_idx = done.find('Release Gate')
        assert doc_only_idx > 0, 'Doc-Only shortcut not found'
        assert release_gate_idx > 0, 'Release Gate not found'
        assert doc_only_idx < release_gate_idx, \
            'Doc-Only shortcut must appear before Release Gate'

    def test_done_references_source_dirs(self):
        """Done prompt should reference source_dirs or LANG_PROFILES for source detection."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'source_dirs' in done or 'LANG_PROFILES' in done, \
            'Done prompt missing source_dirs / LANG_PROFILES reference'

    def test_done_has_skip_decision_log(self):
        """Done prompt should include SKIP decision log format."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'SKIP' in done, \
            'Done prompt missing SKIP decision log type'

    def test_done_has_story_only_decision_log(self):
        """Done prompt should include STORY-ONLY decision log format."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'STORY-ONLY' in done, \
            'Done prompt missing STORY-ONLY decision log type'


# =============================================================================
# AC4 / R2: Act command has Doc-Only detection
# =============================================================================
class TestActDocOnlyDetection:
    """R2: Act Phase 3 Step 3 MUST have Doc-Only detection."""

    def test_act_has_doc_only_keyword(self):
        """Act prompt must contain doc-only detection language."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'doc-only' in lower or 'doc only' in lower, \
            'Act prompt missing doc-only detection language'

    def test_act_doc_only_in_regression_section(self):
        """Doc-Only detection must be in the Regression Check section."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        # Find Regression Check section
        regression_idx = act.find('Regression Check')
        assert regression_idx > 0, 'Regression Check section not found in Act'
        # Doc-only must appear after Regression Check heading
        after_regression = act[regression_idx:]
        lower = after_regression.lower()
        assert 'doc-only' in lower or 'doc only' in lower, \
            'Doc-Only detection must be inside Regression Check section'


# =============================================================================
# AC5 / R3: LANG_PROFILES has source_dirs
# =============================================================================
class TestSourceDirsInLangProfiles:
    """R3: LANG_PROFILES SHOULD have source_dirs field for each language."""

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_has_source_dirs(self, lang):
        p = _prompts()
        profile = p.LANG_PROFILES[lang]
        assert 'source_dirs' in profile, \
            f'{lang} profile missing source_dirs field'

    def test_python_source_dirs_has_src(self):
        p = _prompts()
        dirs = p.LANG_PROFILES['python']['source_dirs']
        assert isinstance(dirs, list)
        assert 'src/' in dirs

    def test_node_source_dirs_has_src(self):
        p = _prompts()
        dirs = p.LANG_PROFILES['node']['source_dirs']
        assert isinstance(dirs, list)
        assert 'src/' in dirs

    def test_java_source_dirs_has_src_main(self):
        p = _prompts()
        dirs = p.LANG_PROFILES['java']['source_dirs']
        assert isinstance(dirs, list)
        assert 'src/main/java/' in dirs


# =============================================================================
# AC3: Existing behavior preserved when source files change
# =============================================================================
class TestBackwardCompatibility:
    """AC3: When source files are changed, behavior must remain unchanged."""

    def test_done_still_has_full_regression(self):
        """Done must still have full regression as default."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'full regression' in lower or 'full suite' in lower

    def test_done_still_has_release_gate(self):
        """Release Gate (Step 1.6) must still exist (STORY-057 removed Step 1.5)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'Release Gate' in done

    def test_done_still_has_decision_tree(self):
        """Decision Tree must still exist."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'Decision Tree' in done

    def test_done_still_has_gate(self):
        """Done must still stop on test failure."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        lower = done.lower()
        assert 'stop' in lower and 'fail' in lower

    def test_act_still_has_regression_check(self):
        """Act must still have Regression Check section."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'Regression Check' in act

    def test_act_still_has_fallback(self):
        """Act must still have fallback to full suite."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'fallback' in lower or 'fall back' in lower

    def test_existing_lang_profile_fields_preserved(self):
        """All existing LANG_PROFILES fields must still be present."""
        p = _prompts()
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        required = list(LANG_PROFILE_REQUIRED_KEYS)
        for lang in ['python', 'node', 'go', 'java']:
            for field in required:
                assert field in p.LANG_PROFILES[lang], \
                    f'{lang} missing existing field: {field}'


# =============================================================================
# AC2 / R4: Decision Logging format updated
# =============================================================================
class TestDecisionLogging:
    """R4: Decision Logging SHOULD support SKIP and STORY-ONLY formats."""

    def test_done_decision_logging_has_skip_format(self):
        """Step 2.3 should document the SKIP format."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        # Find Decision Logging section
        logging_idx = done.find('Decision Logging')
        assert logging_idx > 0, 'Decision Logging section not found'
        after_logging = done[logging_idx:]
        assert 'SKIP' in after_logging, \
            'Decision Logging section missing SKIP format'

    def test_done_decision_logging_has_story_only_format(self):
        """Step 2.3 should document the STORY-ONLY format."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        logging_idx = done.find('Decision Logging')
        assert logging_idx > 0, 'Decision Logging section not found'
        after_logging = done[logging_idx:]
        assert 'STORY-ONLY' in after_logging, \
            'Decision Logging section missing STORY-ONLY format'
