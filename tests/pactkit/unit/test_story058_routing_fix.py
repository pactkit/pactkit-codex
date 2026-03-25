"""STORY-058: Fix Routing Table Embedded Skills — Match Reality.

AC1: Routing table has two skill sections (Embedded Skills + Agent Skills).
AC2: Command-embedded skills table contains only pactkit-trace and pactkit-release.
AC3: Agent skills table lists all 5 agent-only skills.
"""

import pytest

from pactkit.prompts.rules import RULES_MODULES


@pytest.fixture
def routing():
    return RULES_MODULES['routing']


# ===========================================================================
# AC1: Routing table has two skill sections
# ===========================================================================
class TestTwoSkillSections:
    """AC1: RULES_MODULES['routing'] has both Embedded Skills and Agent Skills headings."""

    def test_has_embedded_skills_heading(self, routing):
        assert '## Embedded Skills' in routing

    def test_has_agent_skills_heading(self, routing):
        assert '## Agent Skills' in routing

    def test_embedded_before_agent(self, routing):
        """Embedded Skills section appears before Agent Skills section."""
        embedded_pos = routing.index('## Embedded Skills')
        agent_pos = routing.index('## Agent Skills')
        assert embedded_pos < agent_pos


# ===========================================================================
# AC2: Command-embedded skills are accurate
# ===========================================================================
class TestEmbeddedSkillsAccuracy:
    """AC2: Embedded Skills table contains ONLY pactkit-trace and pactkit-release."""

    @pytest.fixture
    def embedded_section(self, routing):
        """Extract text between '## Embedded Skills' and '## Agent Skills'."""
        start = routing.index('## Embedded Skills')
        end = routing.index('## Agent Skills')
        return routing[start:end]

    def test_trace_in_embedded(self, embedded_section):
        assert 'pactkit-trace' in embedded_section

    def test_release_in_embedded(self, embedded_section):
        assert 'pactkit-release' in embedded_section

    def test_draw_not_in_embedded(self, embedded_section):
        assert 'pactkit-draw' not in embedded_section

    def test_status_not_in_embedded(self, embedded_section):
        assert 'pactkit-status' not in embedded_section

    def test_doctor_not_in_embedded(self, embedded_section):
        assert 'pactkit-doctor' not in embedded_section

    def test_review_not_in_embedded(self, embedded_section):
        assert 'pactkit-review' not in embedded_section

    def test_analyze_not_in_embedded(self, embedded_section):
        assert 'pactkit-analyze' not in embedded_section


# ===========================================================================
# AC3: Agent skills table lists all 5 agent-only skills
# ===========================================================================
class TestAgentSkillsAccuracy:
    """AC3: Agent Skills table contains draw, status, doctor, review, analyze."""

    @pytest.fixture
    def agent_section(self, routing):
        """Extract text from '## Agent Skills' to end of routing string."""
        start = routing.index('## Agent Skills')
        return routing[start:]

    def test_draw_in_agent(self, agent_section):
        assert 'pactkit-draw' in agent_section

    def test_status_in_agent(self, agent_section):
        assert 'pactkit-status' in agent_section

    def test_doctor_in_agent(self, agent_section):
        assert 'pactkit-doctor' in agent_section

    def test_review_in_agent(self, agent_section):
        assert 'pactkit-review' in agent_section

    def test_analyze_in_agent(self, agent_section):
        assert 'pactkit-analyze' in agent_section

    def test_trace_not_in_agent(self, agent_section):
        """pactkit-trace is command-embedded, not agent-only."""
        assert 'pactkit-trace' not in agent_section

    def test_release_not_in_agent(self, agent_section):
        """pactkit-release is command-embedded, not agent-only."""
        assert 'pactkit-release' not in agent_section
