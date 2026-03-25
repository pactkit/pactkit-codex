"""Tests for STORY-026: Stack-Aware Reference Profiles for Multi-Role Development."""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Frontend Reference Exists
# ==============================================================================
class TestDevRefFrontend:
    """STORY-026 Scenario 1: DEV_REF_FRONTEND exists with required content."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'DEV_REF_FRONTEND')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.DEV_REF_FRONTEND, str)
        assert len(p.DEV_REF_FRONTEND) > 100

    def test_has_component(self):
        p = _prompts()
        assert 'component' in p.DEV_REF_FRONTEND.lower() or 'Component' in p.DEV_REF_FRONTEND

    def test_has_accessibility(self):
        p = _prompts()
        ref = p.DEV_REF_FRONTEND
        assert 'accessibility' in ref.lower() or 'a11y' in ref.lower() or 'ARIA' in ref

    def test_has_rerender_or_memoization(self):
        p = _prompts()
        ref = p.DEV_REF_FRONTEND.lower()
        assert 're-render' in ref or 'rerender' in ref or 'memoization' in ref or 'memo' in ref

    def test_has_client_side_security(self):
        p = _prompts()
        ref = p.DEV_REF_FRONTEND.lower()
        assert 'localstorage' in ref or 'client-side' in ref or 'client side' in ref

    def test_has_bundle_or_loading(self):
        p = _prompts()
        ref = p.DEV_REF_FRONTEND.lower()
        assert 'bundle' in ref or 'lazy' in ref or 'code splitting' in ref or 'tree shaking' in ref


# ==============================================================================
# Scenario 2: Backend Reference Exists
# ==============================================================================
class TestDevRefBackend:
    """STORY-026 Scenario 2: DEV_REF_BACKEND exists with required content."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'DEV_REF_BACKEND')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.DEV_REF_BACKEND, str)
        assert len(p.DEV_REF_BACKEND) > 100

    def test_has_api(self):
        p = _prompts()
        assert 'API' in p.DEV_REF_BACKEND

    def test_has_database_or_orm(self):
        p = _prompts()
        ref = p.DEV_REF_BACKEND
        assert 'ORM' in ref or 'database' in ref.lower() or 'Database' in ref

    def test_has_migration(self):
        p = _prompts()
        assert 'migration' in p.DEV_REF_BACKEND.lower() or 'Migration' in p.DEV_REF_BACKEND

    def test_has_observability_or_logging(self):
        p = _prompts()
        ref = p.DEV_REF_BACKEND.lower()
        assert 'logging' in ref or 'observability' in ref or 'tracing' in ref


# ==============================================================================
# Scenario 3: Python Test Reference
# ==============================================================================
class TestTestRefPython:
    """STORY-026 Scenario 3: TEST_REF_PYTHON exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'TEST_REF_PYTHON')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.TEST_REF_PYTHON, str)
        assert len(p.TEST_REF_PYTHON) > 50

    def test_has_pytest(self):
        p = _prompts()
        assert 'pytest' in p.TEST_REF_PYTHON

    def test_has_fixture(self):
        p = _prompts()
        assert 'fixture' in p.TEST_REF_PYTHON.lower() or 'Fixture' in p.TEST_REF_PYTHON

    def test_has_parametrize(self):
        p = _prompts()
        assert 'parametrize' in p.TEST_REF_PYTHON.lower()


# ==============================================================================
# Scenario 4: Node Test Reference
# ==============================================================================
class TestTestRefNode:
    """STORY-026 Scenario 4: TEST_REF_NODE exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'TEST_REF_NODE')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.TEST_REF_NODE, str)
        assert len(p.TEST_REF_NODE) > 50

    def test_has_jest_or_vitest(self):
        p = _prompts()
        ref = p.TEST_REF_NODE.lower()
        assert 'jest' in ref or 'vitest' in ref

    def test_has_describe(self):
        p = _prompts()
        assert 'describe' in p.TEST_REF_NODE

    def test_has_testing_library_or_snapshot(self):
        p = _prompts()
        ref = p.TEST_REF_NODE
        assert 'Testing Library' in ref or 'snapshot' in ref.lower()


# ==============================================================================
# Scenario 5: Go Test Reference
# ==============================================================================
class TestTestRefGo:
    """STORY-026 Scenario 5: TEST_REF_GO exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'TEST_REF_GO')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.TEST_REF_GO, str)
        assert len(p.TEST_REF_GO) > 50

    def test_has_table_driven(self):
        p = _prompts()
        assert 'table-driven' in p.TEST_REF_GO.lower() or 'table driven' in p.TEST_REF_GO.lower()

    def test_has_t_run(self):
        p = _prompts()
        assert 't.Run' in p.TEST_REF_GO

    def test_has_race(self):
        p = _prompts()
        assert 'race' in p.TEST_REF_GO.lower()


# ==============================================================================
# Scenario 6: Java Test Reference
# ==============================================================================
class TestTestRefJava:
    """STORY-026 Scenario 6: TEST_REF_JAVA exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'TEST_REF_JAVA')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.TEST_REF_JAVA, str)
        assert len(p.TEST_REF_JAVA) > 50

    def test_has_junit(self):
        p = _prompts()
        assert 'JUnit' in p.TEST_REF_JAVA

    def test_has_mockito_or_mock(self):
        p = _prompts()
        ref = p.TEST_REF_JAVA
        assert 'Mockito' in ref or 'mock' in ref.lower()

    def test_has_spring_test(self):
        p = _prompts()
        ref = p.TEST_REF_JAVA
        assert '@SpringBootTest' in ref or 'test slicing' in ref.lower() or 'Spring' in ref


# ==============================================================================
# Scenario 7: ACT Prompt Has Stack Detection
# ==============================================================================
class TestActPromptStackDetection:
    """STORY-026 Scenario 7: project-act.md references stack detection."""

    def test_act_has_stack_detection(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        # Should mention detecting project type
        lower = act.lower()
        assert ('detect' in lower or 'identify' in lower)
        assert ('stack' in lower or 'language' in lower or 'project type' in lower)

    def test_act_references_dev_ref(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'DEV_REF' in act or 'TEST_REF' in act or 'Stack Reference' in act or 'stack reference' in act


# ==============================================================================
# Scenario 8: Existing References Unchanged
# ==============================================================================
class TestExistingReferencesUnchanged:
    """STORY-026 Scenario 8: Existing references still present and valid."""

    def test_review_ref_solid(self):
        p = _prompts()
        assert hasattr(p, 'REVIEW_REF_SOLID')
        assert 'SRP' in p.REVIEW_REF_SOLID
        assert 'OCP' in p.REVIEW_REF_SOLID

    def test_review_ref_security(self):
        p = _prompts()
        assert hasattr(p, 'REVIEW_REF_SECURITY')
        assert 'XSS' in p.REVIEW_REF_SECURITY

    def test_review_ref_quality(self):
        p = _prompts()
        assert hasattr(p, 'REVIEW_REF_QUALITY')
        assert 'N+1' in p.REVIEW_REF_QUALITY

    def test_draw_ref_styles(self):
        p = _prompts()
        assert hasattr(p, 'DRAW_REF_STYLES')
        assert 'html=1' in p.DRAW_REF_STYLES


# ==============================================================================
# Scenario 9: Backward Compatibility
# ==============================================================================
class TestBackwardCompatibility:
    """STORY-026 Scenario 9: All existing commands and agents still present."""

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
