"""Tests for STORY-025: Language-Agnostic Framework via Language Profile."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: LANG_PROFILES Exists
# ==============================================================================
class TestLangProfilesExists:
    """STORY-025 Scenario 1: LANG_PROFILES exists with required keys."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'LANG_PROFILES')

    def test_is_dict(self):
        p = _prompts()
        assert isinstance(p.LANG_PROFILES, dict)

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_has_required_language(self, lang):
        p = _prompts()
        assert lang in p.LANG_PROFILES, f"Missing language profile: {lang}"


# ==============================================================================
# Scenario 2: Each Profile Has Required Fields
# ==============================================================================
class TestProfileFields:
    """STORY-025 Scenario 2: Each profile has all required fields."""

    from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
    REQUIRED_FIELDS = list(LANG_PROFILE_REQUIRED_KEYS)

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_has_all_fields(self, lang):
        p = _prompts()
        profile = p.LANG_PROFILES[lang]
        for field in self.REQUIRED_FIELDS:
            assert field in profile, f"{lang} profile missing field: {field}"

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_test_runner_non_empty(self, lang):
        p = _prompts()
        assert len(p.LANG_PROFILES[lang]['test_runner']) > 0

    @pytest.mark.parametrize("lang", ["python", "node", "go", "java"])
    def test_source_dirs_is_list(self, lang):
        p = _prompts()
        assert isinstance(p.LANG_PROFILES[lang]['source_dirs'], list)


# ==============================================================================
# Scenario 3: Python Profile Matches Current Behavior
# ==============================================================================
class TestPythonProfile:
    """STORY-025 Scenario 3: Python profile matches current behavior."""

    def test_test_runner(self):
        p = _prompts()
        assert p.LANG_PROFILES['python']['test_runner'] == 'pytest'

    def test_file_ext(self):
        p = _prompts()
        assert p.LANG_PROFILES['python']['file_ext'] == '.py'

    def test_source_dirs_has_src(self):
        p = _prompts()
        assert 'src/' in p.LANG_PROFILES['python']['source_dirs']



# ==============================================================================
# Scenario 4: Node Profile Is Correct
# ==============================================================================
class TestNodeProfile:
    """STORY-025 Scenario 4: Node profile is correct."""

    def test_test_runner(self):
        p = _prompts()
        runner = p.LANG_PROFILES['node']['test_runner']
        assert 'jest' in runner or 'vitest' in runner or 'npm test' in runner

    def test_file_ext(self):
        p = _prompts()
        assert p.LANG_PROFILES['node']['file_ext'] in ['.ts', '.tsx', '.js']

    def test_source_dirs_has_src(self):
        p = _prompts()
        dirs = p.LANG_PROFILES['node']['source_dirs']
        assert 'src/' in dirs or 'app/' in dirs


# ==============================================================================
# Scenario 5: Init Prompt Contains Detection Logic
# ==============================================================================
class TestInitDetection:
    """STORY-025 Scenario 5: Init prompt contains detection logic."""

    def test_has_pyproject(self):
        p = _prompts()
        init = p.COMMANDS_CONTENT['project-init.md']
        assert 'pyproject.toml' in init

    def test_has_package_json(self):
        p = _prompts()
        init = p.COMMANDS_CONTENT['project-init.md']
        assert 'package.json' in init

    def test_has_go_mod(self):
        p = _prompts()
        init = p.COMMANDS_CONTENT['project-init.md']
        assert 'go.mod' in init

    def test_has_pactkit_yaml(self):
        p = _prompts()
        init = p.COMMANDS_CONTENT['project-init.md']
        assert 'pactkit.yaml' in init


# ==============================================================================
# Scenario 6: ACT Prompt Aware of Language Profile
# ==============================================================================
class TestActLanguageAware:
    """STORY-025 Scenario 6: ACT prompt references language profile."""

    def test_act_mentions_lang_profile(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        lower = act.lower()
        assert 'lang_profiles' in lower or 'language profile' in lower or 'test suite' in lower or 'pactkit.yaml' in lower


# ==============================================================================
# Scenario 7: Agents Use Language-Neutral Phrasing
# ==============================================================================
class TestAgentsLanguageNeutral:
    """STORY-025 Scenario 5/6: Agent prompts use language-neutral test phrasing."""

    def test_senior_dev_neutral(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['senior-developer']['prompt']
        # Should mention "test suite" instead of only "pytest"
        assert 'test suite' in prompt.lower() or 'test runner' in prompt.lower() or 'LANG_PROFILES' in prompt

    def test_qa_engineer_neutral(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['qa-engineer']['prompt']
        assert 'test suite' in prompt.lower() or 'test runner' in prompt.lower() or 'LANG_PROFILES' in prompt


# ==============================================================================
# Scenario 7: Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """STORY-025 Scenario 7: All existing commands and agents still present."""

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


# ==============================================================================
# Scenario 8: References Unchanged
# ==============================================================================
class TestReferencesUnchanged:
    """STORY-025 Scenario 8: Existing reference constants unchanged."""

    def test_review_ref_solid(self):
        p = _prompts()
        assert 'SRP' in p.REVIEW_REF_SOLID
        assert 'OCP' in p.REVIEW_REF_SOLID

    def test_review_ref_security(self):
        p = _prompts()
        assert 'XSS' in p.REVIEW_REF_SECURITY

    def test_review_ref_quality(self):
        p = _prompts()
        assert 'N+1' in p.REVIEW_REF_QUALITY

    def test_draw_ref_styles(self):
        p = _prompts()
        assert 'html=1' in p.DRAW_REF_STYLES

    def test_dev_ref_frontend(self):
        p = _prompts()
        assert hasattr(p, 'DEV_REF_FRONTEND')

    def test_dev_ref_backend(self):
        p = _prompts()
        assert hasattr(p, 'DEV_REF_BACKEND')
