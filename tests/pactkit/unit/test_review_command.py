"""Tests for /project-review command (STORY-016 + STORY-022)."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


class TestReviewPromptExists:
    """Scenario 1: REVIEW_PROMPT 可导入"""

    def test_importable(self):
        p = _prompts()
        assert hasattr(p, 'REVIEW_PROMPT')

    def test_non_empty(self):
        p = _prompts()
        assert isinstance(p.REVIEW_PROMPT, str)
        assert len(p.REVIEW_PROMPT) > 100

    def test_has_frontmatter(self):
        p = _prompts()
        assert p.REVIEW_PROMPT.strip().startswith('---')

    def test_has_arguments_placeholder(self):
        p = _prompts()
        assert '$ARGUMENTS' in p.REVIEW_PROMPT


class TestReviewIsSkill:
    """Scenario 2: Review is now a skill (STORY-011), not a command."""

    def test_not_in_commands_content(self):
        """project-review.md should no longer be in COMMANDS_CONTENT."""
        p = _prompts()
        assert 'project-review.md' not in p.COMMANDS_CONTENT

    def test_skill_md_exists(self):
        """SKILL_REVIEW_MD should exist as a skill template."""
        p = _prompts()
        assert hasattr(p, 'SKILL_REVIEW_MD')
        assert isinstance(p.SKILL_REVIEW_MD, str)
        assert len(p.SKILL_REVIEW_MD) > 50


class TestRoutingTableIncludesReview:
    """Scenario 3: 路由表包含 Review as embedded skill"""

    def test_review_in_routing(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        assert 'pactkit-review' in routing or 'Review' in routing

    def test_has_role(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        assert 'QA Engineer' in routing

    def test_has_skill_reference(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        assert 'pactkit-review' in routing


class TestPlaybookContent:
    """Scenario 4: Playbook 包含核心关键词"""

    def test_has_gh_pr_diff(self):
        p = _prompts()
        assert 'gh pr diff' in p.REVIEW_PROMPT

    def test_has_gh_pr_view(self):
        p = _prompts()
        assert 'gh pr view' in p.REVIEW_PROMPT

    def test_has_owasp(self):
        p = _prompts()
        assert 'OWASP' in p.REVIEW_PROMPT

    def test_has_approve_verdict(self):
        p = _prompts()
        assert 'APPROVE' in p.REVIEW_PROMPT

    def test_has_request_changes_verdict(self):
        p = _prompts()
        assert 'REQUEST_CHANGES' in p.REVIEW_PROMPT

    def test_has_phases(self):
        p = _prompts()
        for phase in ['Phase 0', 'Phase 1', 'Phase 2', 'Phase 3',
                       'Phase 4', 'Phase 5', 'Phase 6', 'Phase 7']:
            assert phase in p.REVIEW_PROMPT, f"Missing {phase}"

    def test_has_spec_alignment(self):
        p = _prompts()
        assert 'Spec' in p.REVIEW_PROMPT or 'spec' in p.REVIEW_PROMPT


class TestPlaybookReadOnly:
    """Scenario 5: Playbook 为只读"""

    def test_allowed_tools_no_write(self):
        p = _prompts()
        # Check frontmatter allowed-tools line
        lines = p.REVIEW_PROMPT.split('\n')
        for line in lines:
            if 'allowed-tools' in line:
                assert 'Write' not in line, "Review should not have Write tool"
                assert 'Edit' not in line, "Review should not have Edit tool"
                break

    def test_allowed_tools_has_read(self):
        p = _prompts()
        lines = p.REVIEW_PROMPT.split('\n')
        for line in lines:
            if 'allowed-tools' in line:
                assert 'Read' in line
                assert 'Bash' in line
                break


class TestBackwardCompatibility:
    """Scenario 6: 现有命令不受影响"""

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


class TestDeployment:
    """Scenario 7: 部署后文件存在"""

    def test_file_deployed(self):
        from pathlib import Path
        deployed = Path.home() / '.claude' / 'commands' / 'project-review.md'
        # This test only passes after deployment; skip if not deployed
        if not deployed.exists():
            pytest.skip("Not deployed yet")
        content = deployed.read_text()
        assert '---' in content
        assert 'description' in content


# === STORY-022: Enhanced Code Review Checklists ===


class TestReferenceConstants:
    """STORY-022 Scenario 1: Reference checklist constants exist."""

    @pytest.mark.parametrize("attr", [
        "REVIEW_REF_SOLID",
        "REVIEW_REF_SECURITY",
        "REVIEW_REF_QUALITY",
        "REVIEW_REF_REMOVAL",
    ])
    def test_exists_and_non_empty(self, attr):
        p = _prompts()
        assert hasattr(p, attr), f"Missing constant {attr}"
        val = getattr(p, attr)
        assert isinstance(val, str)
        assert len(val) > 50, f"{attr} too short ({len(val)} chars)"


class TestSeveritySystem:
    """STORY-022 Scenario 2: P0-P3 severity in REVIEW_PROMPT."""

    @pytest.mark.parametrize("marker", ["P0", "P1", "P2", "P3"])
    def test_has_severity_level(self, marker):
        p = _prompts()
        assert marker in p.REVIEW_PROMPT, f"Missing severity {marker}"

    @pytest.mark.parametrize("name", ["Critical", "High", "Medium", "Low"])
    def test_has_severity_name(self, name):
        p = _prompts()
        assert name in p.REVIEW_PROMPT, f"Missing severity name {name}"


class TestSOLIDKeywords:
    """STORY-022 Scenario 4: SOLID keywords present."""

    @pytest.mark.parametrize("principle", ["SRP", "OCP", "LSP", "ISP", "DIP"])
    def test_solid_principle(self, principle):
        p = _prompts()
        assert principle in p.REVIEW_PROMPT, f"Missing SOLID principle {principle}"


class TestNextStepsConfirmation:
    """STORY-022 Scenario 5: Next Steps confirmation flow."""

    @pytest.mark.parametrize("option", ["Fix all", "Fix P0/P1 only", "No changes"])
    def test_has_option(self, option):
        p = _prompts()
        assert option in p.REVIEW_PROMPT, f"Missing next-step option: {option}"


class TestSpecAlignmentPreserved:
    """STORY-022 Scenario 7: Spec alignment preserved."""

    def test_has_spec_keyword(self):
        p = _prompts()
        assert 'Spec' in p.REVIEW_PROMPT

    def test_has_story_pattern(self):
        p = _prompts()
        assert 'STORY-' in p.REVIEW_PROMPT

    def test_has_docs_specs_path(self):
        p = _prompts()
        assert 'docs/specs/' in p.REVIEW_PROMPT


class TestGhCLIPreserved:
    """STORY-022 Scenario 9: gh CLI integration preserved."""

    def test_has_gh_pr_diff(self):
        p = _prompts()
        assert 'gh pr diff' in p.REVIEW_PROMPT

    def test_has_gh_pr_view(self):
        p = _prompts()
        assert 'gh pr view' in p.REVIEW_PROMPT
