"""Tests for STORY-024: Externalized Draw.io reference constants."""
import re

import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


class TestDrawRefStyles:
    """STORY-024 Scenario 1: Style reference exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'DRAW_REF_STYLES')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.DRAW_REF_STYLES, str)
        assert len(p.DRAW_REF_STYLES) > 100

    def test_has_html_rule(self):
        p = _prompts()
        assert 'html=1' in p.DRAW_REF_STYLES

    def test_has_whitespace_wrap(self):
        p = _prompts()
        assert 'whiteSpace=wrap' in p.DRAW_REF_STYLES


class TestDrawRefAntiBugs:
    """STORY-024 Scenario 2: Anti-Bug reference exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'DRAW_REF_ANTI_BUGS')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.DRAW_REF_ANTI_BUGS, str)
        assert len(p.DRAW_REF_ANTI_BUGS) > 50

    def test_at_least_5_anti_bug_rules(self):
        p = _prompts()
        count = len(re.findall(r'Anti-Bug', p.DRAW_REF_ANTI_BUGS))
        assert count >= 5, f"Only {count} Anti-Bug mentions, need >= 5"


class TestDrawRefLayouts:
    """STORY-024 Scenario 3: Layout reference exists."""

    def test_exists(self):
        p = _prompts()
        assert hasattr(p, 'DRAW_REF_LAYOUTS')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.DRAW_REF_LAYOUTS, str)
        assert len(p.DRAW_REF_LAYOUTS) > 50

    @pytest.mark.parametrize("keyword", ["Architecture", "Dataflow", "Deployment"])
    def test_has_layout_type(self, keyword):
        p = _prompts()
        assert keyword in p.DRAW_REF_LAYOUTS, f"Missing layout type: {keyword}"


class TestBackwardCompatibility:
    """STORY-024 Scenario 5: All existing commands and agents still present."""

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
