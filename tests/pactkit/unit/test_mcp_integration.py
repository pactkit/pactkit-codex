"""Tests for STORY-036 + STORY-037 + STORY-038: MCP-Aware PDCA Commands & Safe Regression."""


def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ---------------------------------------------------------------------------
# Scenario 1: Rule File Content
# ---------------------------------------------------------------------------
class TestMcpRuleModule:
    """R1+R5: MCP integration rule exists in RULES_MODULES."""

    def test_mcp_key_in_rules_modules(self):
        p = _prompts()
        assert 'mcp' in p.RULES_MODULES

    def test_mcp_key_in_rules_files(self):
        p = _prompts()
        assert 'mcp' in p.RULES_FILES
        assert p.RULES_FILES['mcp'] == '06-mcp-integration.md'

    def test_managed_prefix_includes_06(self):
        p = _prompts()
        assert '06-' in p.RULES_MANAGED_PREFIXES

    def test_claude_md_references_06(self):
        p = _prompts()
        assert '06-mcp-integration.md' in p.CLAUDE_MD_TEMPLATE

    def test_rule_mentions_context7(self):
        p = _prompts()
        assert 'context7' in p.RULES_MODULES['mcp'].lower() or 'Context7' in p.RULES_MODULES['mcp']

    def test_rule_mentions_shadcn(self):
        p = _prompts()
        assert 'shadcn' in p.RULES_MODULES['mcp'].lower()

    def test_rule_mentions_playwright(self):
        p = _prompts()
        assert 'playwright' in p.RULES_MODULES['mcp'].lower() or 'Playwright' in p.RULES_MODULES['mcp']

    def test_rule_mentions_chrome_devtools(self):
        p = _prompts()
        mcp_rule = p.RULES_MODULES['mcp']
        assert 'chrome' in mcp_rule.lower() or 'devtools' in mcp_rule.lower() or 'Chrome DevTools' in mcp_rule

    def test_rule_is_conditional(self):
        p = _prompts()
        mcp_rule = p.RULES_MODULES['mcp'].lower()
        assert 'if ' in mcp_rule or 'conditional' in mcp_rule


# ---------------------------------------------------------------------------
# Scenario 2: Design Uses shadcn
# ---------------------------------------------------------------------------
class TestDesignMcpEnhancement:
    """R2: DESIGN_PROMPT contains shadcn instructions."""

    def test_design_prompt_mentions_shadcn(self):
        p = _prompts()
        assert 'shadcn' in p.DESIGN_PROMPT

    def test_design_prompt_mentions_components_json(self):
        p = _prompts()
        assert 'components.json' in p.DESIGN_PROMPT


# ---------------------------------------------------------------------------
# Scenario 3: Act Uses Context7
# ---------------------------------------------------------------------------
class TestActMcpEnhancement:
    """R3: ACT_PROMPT contains Context7 instructions."""

    def test_act_prompt_mentions_context7(self):
        p = _prompts()
        assert 'context7' in p.COMMANDS_CONTENT['project-act.md'].lower() or \
               'Context7' in p.COMMANDS_CONTENT['project-act.md']


# ---------------------------------------------------------------------------
# Scenario 4: Check Uses Playwright MCP + Chrome DevTools
# ---------------------------------------------------------------------------
class TestCheckMcpEnhancement:
    """R4: CHECK_PROMPT contains Playwright MCP and Chrome DevTools instructions."""

    def test_check_prompt_mentions_playwright_mcp(self):
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        assert 'playwright' in check.lower() or 'Playwright MCP' in check

    def test_check_prompt_mentions_chrome_devtools(self):
        p = _prompts()
        check = p.COMMANDS_CONTENT['project-check.md']
        assert 'chrome' in check.lower() or 'devtools' in check.lower() or 'Chrome DevTools' in check


# ---------------------------------------------------------------------------
# Scenario 5+6: Backward Compatibility
# ---------------------------------------------------------------------------
class TestBackwardCompatibility:
    """R6: All existing exports still work."""

    def test_existing_rules_modules_intact(self):
        p = _prompts()
        for key in ['core', 'hierarchy', 'atlas', 'routing', 'workflow']:
            assert key in p.RULES_MODULES

    def test_existing_rules_files_intact(self):
        p = _prompts()
        expected = {
            'core': '01-core-protocol.md',
            'hierarchy': '02-hierarchy-of-truth.md',
            'atlas': '03-file-atlas.md',
            'routing': '04-routing-table.md',
            'workflow': '05-workflow-conventions.md',
        }
        for key, val in expected.items():
            assert p.RULES_FILES[key] == val


# ===========================================================================
# STORY-037: Memory MCP Integration
# ===========================================================================

# ---------------------------------------------------------------------------
# Scenario 1: MCP Rule Updated with Memory MCP
# ---------------------------------------------------------------------------
class TestMemoryMcpRule:
    """R1: RULES_MODULES['mcp'] contains Memory MCP section."""

    def test_rule_mentions_memory(self):
        p = _prompts()
        mcp_rule = p.RULES_MODULES['mcp']
        assert 'memory' in mcp_rule.lower() or 'Memory' in mcp_rule

    def test_rule_mentions_create_entities(self):
        p = _prompts()
        assert 'create_entities' in p.RULES_MODULES['mcp']

    def test_rule_mentions_search_nodes(self):
        p = _prompts()
        assert 'search_nodes' in p.RULES_MODULES['mcp']

    def test_rule_memory_is_conditional(self):
        p = _prompts()
        mcp_rule = p.RULES_MODULES['mcp']
        # Memory section should have conditional language
        memory_idx = mcp_rule.lower().find('memory')
        assert memory_idx != -1
        memory_section = mcp_rule[memory_idx:memory_idx + 500].lower()
        assert 'if ' in memory_section or 'conditional' in memory_section

    def test_phase_table_includes_memory(self):
        p = _prompts()
        mcp_rule = p.RULES_MODULES['mcp']
        # The PDCA phase table should mention Memory
        assert 'Memory' in mcp_rule or 'memory' in mcp_rule.lower()
        # Should appear in Plan, Act, and Done rows
        assert 'Plan' in mcp_rule
        assert 'Done' in mcp_rule


# ---------------------------------------------------------------------------
# Scenario 2: Plan Stores Knowledge
# ---------------------------------------------------------------------------
class TestPlanMemoryMcp:
    """R2: PLAN_PROMPT contains Memory MCP instructions."""

    def test_plan_prompt_mentions_memory_mcp(self):
        p = _prompts()
        plan = p.COMMANDS_CONTENT['project-plan.md']
        assert 'memory' in plan.lower() or 'Memory' in plan

    def test_plan_prompt_mentions_create_entities(self):
        p = _prompts()
        plan = p.COMMANDS_CONTENT['project-plan.md']
        assert 'create_entities' in plan or 'create_entity' in plan


# ---------------------------------------------------------------------------
# Scenario 3: Act Loads Context
# ---------------------------------------------------------------------------
class TestActMemoryMcp:
    """R3: ACT_PROMPT contains Memory MCP load instructions."""

    def test_act_prompt_mentions_search_nodes(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'search_nodes' in act

    def test_act_prompt_mentions_memory_mcp(self):
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'memory' in act.lower() or 'Memory' in act


# ---------------------------------------------------------------------------
# Scenario 4: Done Records Lessons
# ---------------------------------------------------------------------------
class TestDoneMemoryMcp:
    """R4: DONE_PROMPT contains Memory MCP record instructions."""

    def test_done_prompt_mentions_memory_mcp(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'memory' in done.lower() or 'Memory' in done

    def test_done_prompt_mentions_add_observations(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert 'add_observations' in done


# ===========================================================================
# STORY-038: Safe Regression — No Blind Fixes
# ===========================================================================

# ---------------------------------------------------------------------------
# Scenario 1: Act TDD Loop Is Isolated
# ---------------------------------------------------------------------------
class TestActTddLoopIsolated:
    """R1: Act Phase 3 TDD loop only runs Phase 2 tests."""

    def test_act_has_tdd_loop_step(self):
        """Phase 3 must have a distinct TDD loop step."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'TDD Loop' in act or 'tdd loop' in act.lower()

    def test_act_tdd_loop_limits_to_phase2_tests(self):
        """TDD loop must reference running only Phase 2 tests."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        act_lower = act.lower()
        assert 'phase 2' in act_lower
        assert ('only' in act_lower or 'loop' in act_lower)


# ---------------------------------------------------------------------------
# Scenario 2+3: Act Regression Is Read-Only Gate
# ---------------------------------------------------------------------------
class TestActRegressionReadOnly:
    """R1: Act regression check is read-only, stops on pre-existing failure."""

    def test_act_has_regression_check_step(self):
        """Phase 3 must have a distinct regression check step."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        assert 'Regression Check' in act or 'regression check' in act.lower()

    def test_act_regression_prohibits_modifying_preexisting(self):
        """Regression check must prohibit modifying pre-existing tests."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        act_lower = act.lower()
        assert 'do not modify' in act_lower or 'do not fix' in act_lower or \
               'DO NOT modify' in act or 'DO NOT fix' in act

    def test_act_regression_stops_on_failure(self):
        """Regression check must STOP on pre-existing test failure."""
        p = _prompts()
        act = p.COMMANDS_CONTENT['project-act.md']
        act_lower = act.lower()
        assert 'stop' in act_lower
        assert ('report' in act_lower or 'user' in act_lower)


# ---------------------------------------------------------------------------
# Scenario 4: Done Regression No-Fix Rule
# ---------------------------------------------------------------------------
class TestDoneRegressionNoFix:
    """R2: Done regression gate prohibits fixing pre-existing failures."""

    def test_done_prohibits_fixing_preexisting(self):
        """Done must prohibit auto-fixing pre-existing test failures."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        done_lower = done.lower()
        assert ('do not' in done_lower and 'fix' in done_lower) or \
               ('do not' in done_lower and 'modify' in done_lower)

    def test_done_mentions_preexisting_intent(self):
        """Done must mention that agent doesn't understand pre-existing test intent."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        done_lower = done.lower()
        assert 'pre-existing' in done_lower or 'pre existing' in done_lower or \
               'preexisting' in done_lower


# ---------------------------------------------------------------------------
# Scenario 5+6: Done Defaults to Full Regression
# ---------------------------------------------------------------------------
class TestDoneDefaultFull:
    """R3: Done defaults to full regression, incremental is opt-in."""

    def test_done_default_is_full(self):
        """Decision tree must state full regression as the default."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        done_lower = done.lower()
        # Must contain "default" near "full" or explicit "otherwise full"
        assert ('default' in done_lower and 'full' in done_lower) or \
               'otherwise' in done_lower and 'full' in done_lower

    def test_done_incremental_requires_all_conditions(self):
        """Incremental must require ALL conditions (not ANY)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        done_lower = done.lower()
        assert 'all' in done_lower
        assert 'incremental' in done_lower

    def test_done_no_hard_code_graph_dependency(self):
        """Decision tree must not fail when code_graph.mmd is missing."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        done_lower = done.lower()
        # Must mention that missing graph → full regression
        assert ('missing' in done_lower or 'does not exist' in done_lower or
                'not exist' in done_lower)
        assert 'full' in done_lower


# ---------------------------------------------------------------------------
# Scenario 7: Coverage Check Present
# ---------------------------------------------------------------------------
class TestDoneCoverageCheck:
    """R4: Done has optional coverage verification."""

    def test_done_mentions_coverage(self):
        """Done must mention coverage verification."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert '--cov' in done or 'coverage' in done.lower()

    def test_done_mentions_coverage_thresholds(self):
        """Done must mention 80% and 50% thresholds."""
        p = _prompts()
        done = p.COMMANDS_CONTENT['project-done.md']
        assert '80%' in done
        assert '50%' in done
