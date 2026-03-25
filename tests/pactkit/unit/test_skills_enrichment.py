"""Tests for STORY-020: Enrich Skill SKILL.md Documentation."""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


class TestMissingCommandsCovered:
    """Scenario 1: 遗漏命令已补全"""

    def test_board_has_snapshot(self):
        p = _prompts()
        assert 'snapshot' in p.SKILL_BOARD_MD

    def test_visualize_has_list_rules(self):
        p = _prompts()
        assert 'list_rules' in p.SKILL_VISUALIZE_MD


class TestParameterDocs:
    """Scenario 2: 有参数说明"""

    def test_board_add_story_pipe_separator(self):
        p = _prompts()
        # Must explain that | is the task separator
        assert '|' in p.SKILL_BOARD_MD
        text = p.SKILL_BOARD_MD.lower()
        assert '分隔' in text or 'separator' in text or 'split' in text

    def test_board_update_task_match_hint(self):
        p = _prompts()
        text = p.SKILL_BOARD_MD.lower()
        assert '匹配' in text or 'match' in text or '精确' in text or 'exact' in text


class TestPrerequisites:
    """Scenario 3: 有前置条件"""

    def test_board_has_prerequisites(self):
        p = _prompts()
        text = p.SKILL_BOARD_MD.lower()
        assert '前置' in text or 'prerequisite' in text or '条件' in text

    def test_scaffold_has_prerequisites(self):
        p = _prompts()
        text = p.SKILL_SCAFFOLD_MD.lower()
        assert '前置' in text or 'prerequisite' in text or '条件' in text

    def test_visualize_has_prerequisites(self):
        p = _prompts()
        text = p.SKILL_VISUALIZE_MD.lower()
        assert '前置' in text or 'prerequisite' in text or '条件' in text

    def test_board_mentions_sprint_board_file(self):
        p = _prompts()
        assert 'sprint_board.md' in p.SKILL_BOARD_MD


class TestUsageContext:
    """Scenario 4: 有使用场景"""

    def test_board_has_usage_context(self):
        p = _prompts()
        text = p.SKILL_BOARD_MD.lower()
        assert 'scenario' in text or 'context' in text or 'usage' in text

    def test_board_mentions_plan_and_done(self):
        p = _prompts()
        assert 'project-plan' in p.SKILL_BOARD_MD
        assert 'project-done' in p.SKILL_BOARD_MD

    def test_visualize_mentions_plan_and_act(self):
        p = _prompts()
        assert 'project-plan' in p.SKILL_VISUALIZE_MD
        assert 'project-act' in p.SKILL_VISUALIZE_MD

    def test_scaffold_mentions_plan_and_act(self):
        p = _prompts()
        assert 'project-plan' in p.SKILL_SCAFFOLD_MD
        assert 'project-act' in p.SKILL_SCAFFOLD_MD


class TestFrontmatterUnchanged:
    """Scenario 5: Frontmatter 不变"""

    def test_board_name(self):
        p = _prompts()
        assert 'name: pactkit-board' in p.SKILL_BOARD_MD

    def test_board_description(self):
        p = _prompts()
        assert 'Sprint Board atomic operations' in p.SKILL_BOARD_MD

    def test_scaffold_name(self):
        p = _prompts()
        assert 'name: pactkit-scaffold' in p.SKILL_SCAFFOLD_MD

    def test_scaffold_description(self):
        p = _prompts()
        assert 'File scaffolding' in p.SKILL_SCAFFOLD_MD

    def test_visualize_name(self):
        p = _prompts()
        assert 'name: pactkit-visualize' in p.SKILL_VISUALIZE_MD

    def test_visualize_description(self):
        p = _prompts()
        assert 'Generate project code dependency graph' in p.SKILL_VISUALIZE_MD


class TestBackwardCompatibility:
    """Scenario 6: 向后兼容"""

    def test_all_commands_present(self):
        p = _prompts()
        expected = [
            'project-plan.md', 'project-act.md', 'project-check.md',
            'project-done.md', 'project-init.md',
            'project-sprint.md', 'project-hotfix.md', 'project-design.md',
        ]
        for cmd in expected:
            assert cmd in p.COMMANDS_CONTENT, f"Missing {cmd}"

    def test_all_agents_present(self):
        p = _prompts()
        expected = [
            'system-architect', 'senior-developer', 'qa-engineer',
            'repo-maintainer', 'system-medic', 'security-auditor',
            'visual-architect', 'code-explorer',
        ]
        for agent in expected:
            assert agent in p.AGENTS_EXPERT, f"Missing {agent}"
