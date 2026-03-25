"""Tests for STORY-018: Enrich Rules Modules."""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


class TestCoreProtocolEnriched:
    """Scenario 1: Core Protocol 有可执行定义"""

    def test_has_visual_first_definition(self):
        p = _prompts()
        core = p.RULES_MODULES['core']
        assert 'visualize' in core.lower() or 'architecture' in core.lower()

    def test_has_tdd_definition(self):
        p = _prompts()
        core = p.RULES_MODULES['core']
        assert 'test' in core.lower() or 'TDD' in core

    def test_has_session_context(self):
        """STORY-008: Core protocol now has Session Context instead of pseudo-advantages."""
        p = _prompts()
        core = p.RULES_MODULES['core']
        assert 'Session Context' in core or 'context.md' in core


class TestHierarchyOfTruthEnriched:
    """Scenario 2: Hierarchy of Truth 有冲突解决"""

    def test_has_conflict_resolution(self):
        p = _prompts()
        hierarchy = p.RULES_MODULES['hierarchy']
        assert '冲突' in hierarchy or 'conflict' in hierarchy.lower() or '矛盾' in hierarchy

    def test_has_spec_priority(self):
        """When Spec conflicts with code, Spec wins."""
        p = _prompts()
        hierarchy = p.RULES_MODULES['hierarchy']
        assert 'Spec' in hierarchy

    def test_has_read_spec_first_rule(self):
        p = _prompts()
        hierarchy = p.RULES_MODULES['hierarchy']
        # Must instruct to read Spec before modifying code
        text = hierarchy.lower()
        assert '先读' in text or 'before' in text or '必须' in text

    def test_still_has_three_tiers(self):
        p = _prompts()
        hierarchy = p.RULES_MODULES['hierarchy']
        assert 'Tier 1' in hierarchy
        assert 'Tier 2' in hierarchy
        assert 'Tier 3' in hierarchy


class TestFileAtlasEnriched:
    """Scenario 3: File Atlas 路径完整"""

    def test_has_specs(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'docs/specs/' in atlas

    def test_has_commands(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'commands/' in atlas

    def test_has_sprint_board(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'sprint_board' in atlas

    def test_has_test_cases(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'test_cases' in atlas

    def test_has_architecture_graphs(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'architecture' in atlas or 'graphs' in atlas

    def test_has_unit_tests(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'tests/unit' in atlas

    def test_has_e2e_tests(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'tests/e2e' in atlas

    def test_has_archive(self):
        p = _prompts()
        atlas = p.RULES_MODULES['atlas']
        assert 'archive' in atlas


class TestWorkflowConventionsRegistered:
    """Scenario 4: Workflow Conventions 已注册"""

    def test_rules_modules_has_workflow(self):
        p = _prompts()
        assert 'workflow' in p.RULES_MODULES

    def test_rules_files_has_workflow(self):
        p = _prompts()
        assert 'workflow' in p.RULES_FILES
        assert p.RULES_FILES['workflow'] == '05-workflow-conventions.md'

    def test_managed_prefixes_has_05(self):
        p = _prompts()
        assert '05-' in p.RULES_MANAGED_PREFIXES

    def test_claude_md_template_imports_05(self):
        p = _prompts()
        assert '05-workflow-conventions.md' in p.CLAUDE_MD_TEMPLATE


class TestWorkflowConventionsContent:
    """Scenario 5: Workflow 包含核心规范"""

    def test_has_conventional_commit(self):
        p = _prompts()
        workflow = p.RULES_MODULES['workflow']
        assert 'Conventional Commit' in workflow or 'conventional commit' in workflow.lower()

    def test_has_feat_type(self):
        p = _prompts()
        workflow = p.RULES_MODULES['workflow']
        assert 'feat(' in workflow or 'feat:' in workflow or '`feat`' in workflow

    def test_has_fix_type(self):
        p = _prompts()
        workflow = p.RULES_MODULES['workflow']
        assert 'fix(' in workflow or 'fix:' in workflow or '`fix`' in workflow

    def test_has_branch_naming(self):
        p = _prompts()
        workflow = p.RULES_MODULES['workflow']
        text = workflow.lower()
        assert 'branch' in text or '分支' in text


class TestRoutingTableUnchanged:
    """Scenario 6: Routing Table 未变"""

    def test_routing_has_all_commands(self):
        p = _prompts()
        routing = p.RULES_MODULES['routing']
        expected = [
            'project-init', 'project-plan', 'project-act',
            'project-check', 'project-done',
            'project-sprint', 'project-hotfix', 'project-design',
        ]
        for cmd in expected:
            assert cmd in routing, f"Missing {cmd} in routing"

    def test_routing_not_in_managed_05(self):
        """Routing is 04, not 05."""
        p = _prompts()
        assert p.RULES_FILES['routing'] == '04-routing-table.md'


class TestBackwardCompatibility:
    """Scenario 7: 向后兼容"""

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

    def test_managed_prefixes_no_10(self):
        """User's 10-safety.md must not be managed."""
        p = _prompts()
        assert '10-' not in p.RULES_MANAGED_PREFIXES
