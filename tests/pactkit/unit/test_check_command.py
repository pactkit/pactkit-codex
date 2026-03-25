"""Tests for /project-check command (STORY-023: Enhanced Security & Quality Checklists)."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


def _check_prompt():
    return _prompts().COMMANDS_CONTENT['project-check.md']


class TestSecurityChecklistKeywords:
    """STORY-023 Scenario 1: Security checklist keywords present."""

    @pytest.mark.parametrize("keyword", [
        "XSS", "Injection", "SSRF", "Race Condition", "TOCTOU",
    ])
    def test_has_security_keyword(self, keyword):
        prompt = _check_prompt()
        assert keyword in prompt, f"Missing security keyword: {keyword}"


class TestQualityChecklistKeywords:
    """STORY-023 Scenario 2: Quality checklist keywords present."""

    def test_has_n_plus_1(self):
        prompt = _check_prompt()
        assert 'N+1' in prompt

    def test_has_boundary(self):
        prompt = _check_prompt()
        assert 'boundary' in prompt.lower() or 'Boundary' in prompt

    def test_has_error_handling(self):
        prompt = _check_prompt()
        assert 'error handling' in prompt.lower() or 'swallowed exception' in prompt.lower()


class TestSeveritySystem:
    """STORY-023 Scenario 3: P0-P3 severity present."""

    @pytest.mark.parametrize("marker", ["P0", "P1", "P2", "P3"])
    def test_has_severity_level(self, marker):
        prompt = _check_prompt()
        assert marker in prompt, f"Missing severity {marker}"


class TestAllPhases:
    """STORY-023 Scenario 4: All phases present (Phase 0-5)."""

    @pytest.mark.parametrize("phase", [
        "Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5",
    ])
    def test_has_phase(self, phase):
        prompt = _check_prompt()
        assert phase in prompt, f"Missing {phase}"


class TestReadOnlyConstraint:
    """STORY-023 Scenario 5: Read-only constraint preserved."""

    def test_no_write_tool(self):
        prompt = _check_prompt()
        lines = prompt.split('\n')
        for line in lines:
            if 'allowed-tools' in line:
                assert 'Write' not in line
                assert 'Edit' not in line
                break

    def test_has_read_tool(self):
        prompt = _check_prompt()
        lines = prompt.split('\n')
        for line in lines:
            if 'allowed-tools' in line:
                assert 'Read' in line
                assert 'Bash' in line
                break


class TestSpecVerificationPreserved:
    """STORY-023 Scenario 6: Spec verification preserved."""

    def test_has_spec_keyword(self):
        prompt = _check_prompt()
        assert 'Spec' in prompt

    def test_has_acceptance_criteria(self):
        prompt = _check_prompt()
        assert 'Acceptance Criteria' in prompt

    def test_has_gherkin(self):
        prompt = _check_prompt()
        assert 'Gherkin' in prompt


class TestBackwardCompatibility:
    """STORY-023 Scenario 7: Backward compatibility."""

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
