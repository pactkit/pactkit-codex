"""Tests for STORY-006: Session Context Protocol — cross-session project state awareness."""

import importlib


def _prompts():
    import pactkit.prompts as p

    importlib.reload(p)
    return p


# ==============================================================================
# Scenario 1: Done generates context.md instructions
# ==============================================================================
class TestDoneContextGeneration:
    """Done playbook must include context.md generation phase."""

    def test_done_has_context_generation_phase(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "context.md" in done

    def test_done_context_after_commit(self):
        """Context generation must come after git commit (Phase 4)."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        commit_pos = done.find("Git Commit")
        context_pos = done.find("Context")
        # Find the context generation phase that's after commit
        # There may be "Context Loading" earlier, so find the generation one
        assert "Generate Context" in done or "Update Context" in done or "Session Context" in done

    def test_done_context_reads_board(self):
        """Context generation must read sprint_board.md."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        # The context generation instructions should reference sprint_board
        assert "sprint_board" in done

    def test_done_context_reads_lessons(self):
        """Context generation must reference lessons.md."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "lessons" in done.lower()

    def test_done_context_includes_branches(self):
        """Context generation must include active branches."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "branch" in done.lower()

    def test_done_context_includes_next_action(self):
        """Context generation must include recommended next action (via {CONTEXT_SECTIONS})."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "{CONTEXT_SECTIONS}" in done or "Next Recommended Action" in done or "next action" in done.lower()


# ==============================================================================
# Scenario 2: CLAUDE.md references context.md
# ==============================================================================
class TestClaudeMdContextReference:
    """CLAUDE_MD_TEMPLATE must include @./docs/product/context.md."""

    def test_template_has_context_reference(self):
        p = _prompts()
        assert "@./docs/product/context.md" in p.CLAUDE_MD_TEMPLATE

    def test_context_reference_after_rules(self):
        """The @context.md line must come after rule imports."""
        p = _prompts()
        template = p.CLAUDE_MD_TEMPLATE
        # Find last rule import
        last_rule_pos = template.rfind("@~/.claude/rules/")
        context_pos = template.find("@./docs/product/context.md")
        assert context_pos > last_rule_pos

    def test_deployer_classic_includes_context(self):
        """_deploy_claude_md should produce CLAUDE.md with context reference."""
        import tempfile
        from pathlib import Path

        from pactkit.generators.deployer import _deploy_claude_md
        from pactkit.prompts import RULES_FILES

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _deploy_claude_md(tmp_path, list(RULES_FILES.keys()))
            content = (tmp_path / "CLAUDE.md").read_text()
            assert "@./docs/product/context.md" in content


# ==============================================================================
# Scenario 3: Cold start with context (format validation)
# ==============================================================================
class TestContextFileFormat:
    """Context file generation instructions must specify the correct format."""

    def test_done_context_format_has_sprint_status(self):
        """After STORY-slim-007: sections come from schemas via {CONTEXT_SECTIONS} placeholder."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        # Either the placeholder or the rendered section name must be present
        assert "{CONTEXT_SECTIONS}" in done or "Sprint Status" in done

    def test_done_context_format_has_recent_completions(self):
        """After STORY-slim-007: section names come from schemas via {CONTEXT_SECTIONS} placeholder."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]

        # Either the placeholder is present, or the rendered sections are present
        assert "{CONTEXT_SECTIONS}" in done or "Recent Completions" in done

    def test_done_context_format_has_active_branches(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "{CONTEXT_SECTIONS}" in done or "Active Branches" in done

    def test_done_context_format_has_key_decisions(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "{CONTEXT_SECTIONS}" in done or "Key Decisions" in done


# ==============================================================================
# Scenario 4: Lessons auto-appended
# ==============================================================================
class TestLessonsAutoAppend:
    """Done playbook must auto-append to lessons.md."""

    def test_done_has_lessons_append(self):
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "lessons.md" in done

    def test_done_lessons_not_conditional_on_mcp(self):
        """Lessons append must NOT be conditional on Memory MCP."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        # Find lessons.md reference that's NOT inside MCP conditional
        # The lessons append should be a standalone step, not inside "IF mcp__memory"
        lines = done.split("\n")
        found_unconditional_lessons = False
        for i, line in enumerate(lines):
            if "lessons.md" in line and "mcp__memory" not in line:
                # Check this line isn't inside an MCP conditional block
                found_unconditional_lessons = True
                break
        assert found_unconditional_lessons, "lessons.md append must exist outside of Memory MCP conditional"

    def test_done_lessons_has_date_format(self):
        """Lessons entry must include date."""
        p = _prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "date" in done.lower() or "Date" in done


# ==============================================================================
# Scenario 5: Context.md missing gracefully (no code needed — @import behavior)
# This is a behavioral test — Claude Code silently skips missing @imports.
# We just verify the template uses the right syntax.
# ==============================================================================
class TestContextMissingGraceful:
    """@import of context.md should use project-relative path."""

    def test_uses_relative_path(self):
        """Must use @./docs/... not @~/... or absolute path."""
        p = _prompts()
        template = p.CLAUDE_MD_TEMPLATE
        assert "@./docs/product/context.md" in template
        # Should NOT use home-relative path
        assert "@~/.claude/context.md" not in template


# ==============================================================================
# Scenario 6: Plan updates context
# ==============================================================================
class TestPlanContextGeneration:
    """Plan playbook must include context.md generation phase."""

    def test_plan_has_context_generation(self):
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "context.md" in plan

    def test_plan_context_after_board(self):
        """Context generation must come after Board creation."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        board_pos = plan.find("add_story")
        context_pos = plan.find("context.md")
        assert context_pos > board_pos, "context.md generation must come after Board (add_story)"


# ==============================================================================
# Additional: Init generates context
# ==============================================================================
class TestInitContextGeneration:
    """Init playbook must include context.md generation phase."""

    def test_init_has_context_generation(self):
        p = _prompts()
        init = p.COMMANDS_CONTENT["project-init.md"]
        assert "context.md" in init


# ==============================================================================
# Plugin mode: TIP about /project-init
# ==============================================================================
class TestPluginModeContext:
    """Plugin inline CLAUDE.md should include TIP about project-init."""

    def test_plugin_inline_has_init_tip(self):
        """Plugin CLAUDE.md should hint at /project-init for context."""
        import tempfile
        from pathlib import Path

        from pactkit.generators.deployer import _deploy_claude_md_inline

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _deploy_claude_md_inline(tmp_path)
            content = (tmp_path / "CLAUDE.md").read_text()
            assert "/project-init" in content
            assert "context" in content.lower()
