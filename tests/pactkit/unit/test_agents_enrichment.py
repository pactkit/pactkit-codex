"""Tests for STORY-019: Enrich Agent Definitions."""
import pytest


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


ALL_AGENTS = [
    'system-architect', 'senior-developer', 'qa-engineer',
    'repo-maintainer', 'system-medic', 'security-auditor',
    'visual-architect', 'code-explorer',
]


class TestFourSectionStructure:
    """Scenario 1: 所有 Agent 有四段结构"""

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_has_goal(self, agent):
        p = _prompts()
        prompt = p.AGENTS_EXPERT[agent]['prompt']
        assert 'Goal' in prompt or '目标' in prompt

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_has_boundaries(self, agent):
        p = _prompts()
        prompt = p.AGENTS_EXPERT[agent]['prompt']
        assert 'Boundaries' in prompt or 'Boundary' in prompt or '边界' in prompt

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_has_output(self, agent):
        p = _prompts()
        prompt = p.AGENTS_EXPERT[agent]['prompt']
        assert 'Output' in prompt or '输出' in prompt or '交付' in prompt

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_has_protocol(self, agent):
        p = _prompts()
        prompt = p.AGENTS_EXPERT[agent]['prompt']
        assert 'Protocol' in prompt or '协议' in prompt


class TestMultiCommandAwareness:
    """Scenario 2: 多命令感知"""

    def test_senior_dev_has_act_and_hotfix(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['senior-developer']['prompt']
        assert 'project-act' in prompt
        assert 'project-hotfix' in prompt

    def test_repo_maintainer_has_done_and_release(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['repo-maintainer']['prompt']
        assert 'project-done' in prompt
        assert 'pactkit-release' in prompt

    def test_qa_engineer_has_check_and_review(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['qa-engineer']['prompt']
        assert 'project-check' in prompt
        assert 'pactkit-review' in prompt


class TestSkillsCompletion:
    """Scenario 3: Skills 补全"""

    def test_repo_maintainer_has_board_skill(self):
        p = _prompts()
        skills = p.AGENTS_EXPERT['repo-maintainer'].get('skills', '')
        assert 'pactkit-board' in skills

    def test_system_medic_has_visualize_skill(self):
        p = _prompts()
        skills = p.AGENTS_EXPERT['system-medic'].get('skills', '')
        assert 'pactkit-visualize' in skills

    def test_system_architect_skills_unchanged(self):
        p = _prompts()
        skills = p.AGENTS_EXPERT['system-architect']['skills']
        assert 'pactkit-visualize' in skills
        assert 'pactkit-scaffold' in skills

    def test_senior_developer_skills_unchanged(self):
        p = _prompts()
        skills = p.AGENTS_EXPERT['senior-developer']['skills']
        assert 'pactkit-visualize' in skills
        assert 'pactkit-scaffold' in skills


class TestSecurityAuditorEnhanced:
    """Scenario 4: security-auditor 增强"""

    def test_has_severity_levels(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['security-auditor']['prompt']
        for level in ['Critical', 'High', 'Medium', 'Low']:
            assert level in prompt, f"Missing severity: {level}"

    def test_has_owasp_categories(self):
        p = _prompts()
        prompt = p.AGENTS_EXPERT['security-auditor']['prompt']
        # At least 5 OWASP categories mentioned
        owasp_keywords = [
            'Injection', 'XSS', 'Auth', 'SSRF', 'Crypto',
            'Access Control', 'Misconfiguration', 'Deserialization',
            'Logging', 'Secrets', 'Hardcoded',
        ]
        count = sum(1 for kw in owasp_keywords if kw in prompt)
        assert count >= 5, f"Only {count} OWASP categories found"

    def test_has_playbook_reference(self):
        """security-auditor should reference its usage context."""
        p = _prompts()
        prompt = p.AGENTS_EXPERT['security-auditor']['prompt']
        assert 'OWASP' in prompt


class TestFrontmatterUnchanged:
    """Scenario 5: Frontmatter 字段不变"""

    EXPECTED_TOOLS = {
        'system-architect': 'Read, Write, Edit, Bash, Glob',
        'senior-developer': 'Read, Write, Edit, Bash, Glob, Grep',
        'qa-engineer': 'Read, Bash, Grep',
        'repo-maintainer': 'Read, Write, Edit, Bash, Glob',
        'system-medic': 'Read, Bash, Glob',
        'security-auditor': 'Read, Bash, Grep',
        'visual-architect': 'Read, Write',
        'code-explorer': 'Read, Bash, Grep, Glob, Find',
    }

    @pytest.mark.parametrize("agent", ALL_AGENTS)
    def test_tools_unchanged(self, agent):
        p = _prompts()
        assert p.AGENTS_EXPERT[agent]['tools'] == self.EXPECTED_TOOLS[agent]

    def test_qa_permission_mode(self):
        p = _prompts()
        assert p.AGENTS_EXPERT['qa-engineer']['permissionMode'] == 'plan'

    def test_security_disallowed_tools(self):
        p = _prompts()
        assert p.AGENTS_EXPERT['security-auditor']['disallowedTools'] == '[Write, Edit]'

    def test_code_explorer_max_turns(self):
        p = _prompts()
        assert p.AGENTS_EXPERT['code-explorer']['maxTurns'] == 15  # STORY-slim-020

    def test_visual_architect_max_turns(self):
        p = _prompts()
        assert p.AGENTS_EXPERT['visual-architect']['maxTurns'] == 30

    def test_code_explorer_memory(self):
        p = _prompts()
        assert p.AGENTS_EXPERT['code-explorer']['memory'] == 'user'


class TestBackwardCompatibility:
    """Scenario 6: 向后兼容"""

    def test_all_agents_present(self):
        p = _prompts()
        for agent in ALL_AGENTS:
            assert agent in p.AGENTS_EXPERT, f"Missing agent {agent}"

    def test_all_commands_present(self):
        p = _prompts()
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"
