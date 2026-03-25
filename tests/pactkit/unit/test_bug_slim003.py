"""Tests for BUG-slim-003: CLI Migration Gaps.

Verifies prompt inconsistencies are fixed and implementation mismatches corrected.
"""
def _prompts():
    import importlib

    import pactkit.prompts as p
    importlib.reload(p)
    return p


# ---------------------------------------------------------------------------
# R1: pactkit next-id called in sprint/hotfix/design
# ---------------------------------------------------------------------------

class TestR1NextIdConsistency:
    """Sprint, Hotfix, and Design prompts must call pactkit next-id."""

    def test_sprint_calls_pactkit_next_id(self):
        """SPRINT_PROMPT must reference pactkit next-id."""
        p = _prompts()
        assert "pactkit next-id" in p.SPRINT_PROMPT

    def test_sprint_no_manual_scan(self):
        """SPRINT_PROMPT must not instruct manual docs/specs/ scanning."""
        p = _prompts()
        assert "Determine next STORY-ID via Glob" not in p.SPRINT_PROMPT

    def test_hotfix_calls_pactkit_next_id(self):
        """HOTFIX_PROMPT must reference pactkit next-id."""
        p = _prompts()
        assert "pactkit next-id" in p.HOTFIX_PROMPT

    def test_hotfix_no_manual_scan(self):
        """HOTFIX_PROMPT must not instruct manual docs/specs/ scanning for IDs."""
        p = _prompts()
        assert "determine the next available number" not in p.HOTFIX_PROMPT

    def test_design_calls_pactkit_next_id(self):
        """DESIGN_PROMPT must reference pactkit next-id."""
        p = _prompts()
        assert "pactkit next-id" in p.DESIGN_PROMPT

    def test_design_no_manual_scan(self):
        """DESIGN_PROMPT must not instruct manual docs/specs/ scanning."""
        p = _prompts()
        assert "Scan `docs/specs/` to find the next available" not in p.DESIGN_PROMPT


# ---------------------------------------------------------------------------
# R2: pactkit sec-scope called in Plan Phase 3.2
# ---------------------------------------------------------------------------

class TestR2SecScopeConsistency:
    """Plan Phase 3.2 must delegate to pactkit sec-scope."""

    def test_plan_calls_pactkit_sec_scope(self):
        """Plan prompt must reference pactkit sec-scope for security scope."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "pactkit sec-scope" in plan

    def test_plan_sec_table_is_reference_only(self):
        """The SEC detection table may remain as reference but must not be the primary instruction."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        # pactkit sec-scope should appear BEFORE the SEC table (if table still exists)
        sec_scope_pos = plan.find("pactkit sec-scope")
        sec1_pos = plan.find("SEC-1")
        assert sec_scope_pos > 0
        if sec1_pos > 0:
            assert sec_scope_pos < sec1_pos, "pactkit sec-scope must appear before SEC table"


# ---------------------------------------------------------------------------
# R3: pactkit context called in Plan Phase 3.3 and Init Phase 6
# ---------------------------------------------------------------------------

class TestR3ContextConsistency:
    """Plan Phase 3.3 and Init Phase 6 must delegate to pactkit context."""

    def test_plan_calls_pactkit_context(self):
        """Plan Phase 3.3 must reference pactkit context."""
        p = _prompts()
        plan = p.COMMANDS_CONTENT["project-plan.md"]
        assert "pactkit context" in plan

    def test_init_calls_pactkit_context(self):
        """Init Phase 6 must reference pactkit context."""
        p = _prompts()
        init = p.COMMANDS_CONTENT["project-init.md"]
        assert "pactkit context" in init


# ---------------------------------------------------------------------------
# R4: cleaners.py Java cleanup matches LANG_PROFILES
# ---------------------------------------------------------------------------

class TestR4CleanersJavaAlignment:
    """cleaners.py Java cleanup patterns are correct (canonical source since BUG-slim-006)."""

    def test_java_cleanup_has_all_languages(self):
        """_CLEANUP_PATTERNS must cover all 4 languages."""
        from pactkit.cleaners import _CLEANUP_PATTERNS

        for lang in ["python", "node", "go", "java"]:
            assert lang in _CLEANUP_PATTERNS, f"Missing {lang} in _CLEANUP_PATTERNS"

    def test_java_cleanup_has_gradle(self):
        """Java cleanup must include .gradle/ directory."""
        from pactkit.cleaners import _CLEANUP_PATTERNS

        assert ".gradle/" in _CLEANUP_PATTERNS["java"] or ".gradle" in _CLEANUP_PATTERNS["java"]

    def test_java_cleanup_no_star_class(self):
        """Java cleanup must NOT include *.class (not in canonical LANG_PROFILES)."""
        from pactkit.cleaners import _CLEANUP_PATTERNS

        assert "*.class" not in _CLEANUP_PATTERNS["java"]


# ---------------------------------------------------------------------------
# R5: guards.py config completeness check
# ---------------------------------------------------------------------------

class TestR5GuardsConfigCompleteness:
    """check_init_markers should optionally report config completeness."""

    def test_missing_developer_reported(self, tmp_path):
        """A pactkit.yaml missing 'developer' should produce a config warning."""
        from pactkit.guards import check_init_markers

        # Create all 3 markers
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pactkit.yaml").write_text("stack: python\n")
        (tmp_path / "docs" / "product").mkdir(parents=True)
        (tmp_path / "docs" / "product" / "sprint_board.md").write_text("# Board\n")
        (tmp_path / "docs" / "architecture" / "graphs").mkdir(parents=True)

        ok, missing = check_init_markers(tmp_path)
        # Markers are all present, so ok should be True
        assert ok is True
        # But there should be config warnings (returned separately or in missing)
        # The function returns (ok, missing) — config issues are warnings, not blockers
        # We check via the new check_config_completeness function
        from pactkit.guards import check_config_completeness

        warnings = check_config_completeness(tmp_path)
        assert any("developer" in w for w in warnings)

    def test_complete_config_no_warnings(self, tmp_path):
        """A pactkit.yaml with all expected sections produces no warnings."""
        from pactkit.guards import check_config_completeness

        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "pactkit.yaml").write_text(
            "developer: slim\nstack: python\nagents: []\ncommands: []\nskills: []\nrules: []\n"
        )

        warnings = check_config_completeness(tmp_path)
        assert warnings == []

    def test_no_yaml_returns_skip(self, tmp_path):
        """If pactkit.yaml doesn't exist, config completeness returns skip message."""
        from pactkit.guards import check_config_completeness

        warnings = check_config_completeness(tmp_path)
        assert any("not found" in w.lower() or "skip" in w.lower() for w in warnings) or warnings == []


# ---------------------------------------------------------------------------
# R6: lint_lessons row format validation
# ---------------------------------------------------------------------------

class TestR6LintLessonsRowFormat:
    """lint_lessons should validate row column count."""

    def test_valid_3_column_row(self, tmp_path):
        """A lessons.md with valid 3-column rows passes."""
        from pactkit.validators import lint_lessons

        content = (
            "# Lessons Learned\n\n"
            "| Date | Lesson | Context |\n"
            "|------|--------|---------|\n"
            "| 2026-01 | Some lesson | STORY-001 |\n"
        )
        path = tmp_path / "lessons.md"
        path.write_text(content)
        errors = lint_lessons(path)
        assert errors == []

    def test_2_column_row_fails(self, tmp_path):
        """A lessons.md with a 2-column row (missing Context) fails."""
        from pactkit.validators import lint_lessons

        content = (
            "# Lessons Learned\n\n"
            "| Date | Lesson | Context |\n"
            "|------|--------|---------|\n"
            "| 2026-01 | lesson only |\n"
        )
        path = tmp_path / "lessons.md"
        path.write_text(content)
        errors = lint_lessons(path)
        assert len(errors) > 0
        assert any("column" in e.lower() for e in errors)

    def test_4_column_row_fails(self, tmp_path):
        """A lessons.md with a 4-column row fails."""
        from pactkit.validators import lint_lessons

        content = (
            "# Lessons Learned\n\n"
            "| Date | Lesson | Context |\n"
            "|------|--------|---------|\n"
            "| 2026-01 | lesson | STORY | extra |\n"
        )
        path = tmp_path / "lessons.md"
        path.write_text(content)
        errors = lint_lessons(path)
        assert len(errors) > 0
        assert any("column" in e.lower() for e in errors)

    def test_separator_row_not_counted(self, tmp_path):
        """The separator row (|---|---|---|) should not be validated as a data row."""
        from pactkit.validators import lint_lessons

        content = (
            "# Lessons Learned\n\n"
            "| Date | Lesson | Context |\n"
            "|------|--------|---------|\n"
        )
        path = tmp_path / "lessons.md"
        path.write_text(content)
        errors = lint_lessons(path)
        assert errors == []
