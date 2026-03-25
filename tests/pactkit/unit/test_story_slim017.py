"""Tests for STORY-slim-017: Done Phase Deterministic Gate Migration.

R1: lesson-append with dedup
R2: invariants-refresh test count
R3: coverage-gate verification
R4: CLI wiring (3 new subcommands)
R5: Prompt delegation to new CLI commands
"""

from __future__ import annotations

import inspect
import textwrap
from datetime import date
from unittest.mock import patch


# ---------------------------------------------------------------------------
# R1: lessons.py — append_lesson()
# ---------------------------------------------------------------------------
class TestR1LessonAppend:
    """Scenario 1+2: append when specific & non-dup, skip when dup."""

    def _make_lessons_md(self, tmp_path, entries=5):
        content = "# Lessons Learned\n\n| Date | Lesson | Context |\n|------|--------|--------|\n"
        for i in range(entries):
            content += f"| 2026-03-{10+i:02d} | lesson {i} about foo_{i}.py:bar() | STORY-{i:03d} |\n"
        p = tmp_path / "docs" / "architecture" / "governance" / "lessons.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def test_append_specific_non_duplicate(self, tmp_path):
        from pactkit.lessons import append_lesson

        self._make_lessons_md(tmp_path)
        result = append_lesson(
            project_root=tmp_path,
            story_id="STORY-017",
            text="cleaners.py _CLEANUP_PATTERNS diverged from LANG_PROFILES",
            context="cleaners.py:detect_stack",
        )
        assert result["action"] == "appended"
        lessons = (tmp_path / "docs/architecture/governance/lessons.md").read_text()
        assert "cleaners.py _CLEANUP_PATTERNS" in lessons
        assert str(date.today()) in lessons

    def test_skip_duplicate(self, tmp_path):
        from pactkit.lessons import append_lesson

        self._make_lessons_md(tmp_path)
        # First append
        append_lesson(
            tmp_path, "STORY-017",
            "cleaners.py _CLEANUP_PATTERNS diverged from LANG_PROFILES",
        )
        # Near-identical second append
        result = append_lesson(
            tmp_path, "STORY-017",
            "cleaners.py _CLEANUP_PATTERNS diverged from LANG_PROFILES source",
        )
        assert result["action"] == "skipped"
        assert "duplicate" in result["reason"].lower()

    def test_skip_non_specific(self, tmp_path):
        from pactkit.lessons import append_lesson

        self._make_lessons_md(tmp_path)
        result = append_lesson(
            tmp_path, "STORY-017",
            "always write good tests",
        )
        assert result["action"] == "skipped"
        assert "specific" in result["reason"].lower()

    def test_no_lessons_file(self, tmp_path):
        from pactkit.lessons import append_lesson

        result = append_lesson(tmp_path, "STORY-017", "foo.py:bar pattern")
        assert result["action"] == "skipped"


# ---------------------------------------------------------------------------
# R2: invariants.py — refresh_test_count()
# ---------------------------------------------------------------------------
class TestR2InvariantsRefresh:
    """Scenario 3: update test count in rules.md."""

    def _make_rules_md(self, tmp_path, count=2572):
        content = textwrap.dedent(f"""\
            # Governance Rules

            ## Invariants

            1. All {count}+ tests must pass before any commit to `main`.
            2. Specs are the source of truth.
        """)
        p = tmp_path / "docs" / "architecture" / "governance" / "rules.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def test_update_test_count(self, tmp_path):
        from pactkit.invariants import refresh_test_count

        self._make_rules_md(tmp_path, count=2572)
        result = refresh_test_count(tmp_path, test_count=2587)
        assert result["action"] == "updated"
        assert result["old_count"] == 2572
        assert result["new_count"] == 2587
        text = (tmp_path / "docs/architecture/governance/rules.md").read_text()
        assert "All 2587+ tests" in text
        assert "2572" not in text

    def test_skip_same_count(self, tmp_path):
        from pactkit.invariants import refresh_test_count

        self._make_rules_md(tmp_path, count=2587)
        result = refresh_test_count(tmp_path, test_count=2587)
        assert result["action"] == "skipped"

    def test_not_found_no_file(self, tmp_path):
        from pactkit.invariants import refresh_test_count

        result = refresh_test_count(tmp_path, test_count=100)
        assert result["action"] == "not_found"

    def test_not_found_no_pattern(self, tmp_path):
        from pactkit.invariants import refresh_test_count

        p = tmp_path / "docs" / "architecture" / "governance" / "rules.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# Rules\n\nNo invariants here.\n")
        result = refresh_test_count(tmp_path, test_count=100)
        assert result["action"] == "not_found"


# ---------------------------------------------------------------------------
# R3: coverage_gate.py — check_coverage()
# ---------------------------------------------------------------------------
class TestR3CoverageGate:
    """Scenario 4+5: coverage thresholds and pytest-cov unavailable."""

    def test_skip_when_pytest_cov_unavailable(self, tmp_path):
        from pactkit.coverage_gate import check_coverage

        with patch("pactkit.coverage_gate._run_pytest_cov") as mock_run:
            mock_run.side_effect = FileNotFoundError("pytest-cov not installed")
            result = check_coverage(["src/pactkit/foo.py"], project_root=tmp_path)
        assert result["overall"] == "skip"
        assert "reason" in result

    def test_pass_threshold(self):
        from pactkit.coverage_gate import _classify_coverage

        assert _classify_coverage(85) == "pass"

    def test_warn_threshold(self):
        from pactkit.coverage_gate import _classify_coverage

        assert _classify_coverage(65) == "warn"

    def test_block_threshold(self):
        from pactkit.coverage_gate import _classify_coverage

        assert _classify_coverage(40) == "block"

    def test_parse_coverage_output(self):
        from pactkit.coverage_gate import _parse_coverage_output

        output = textwrap.dedent("""\
            Name                    Stmts   Miss  Cover   Missing
            -------------------------------------------------------
            src/pactkit/foo.py         50     10    80%   11-15,20
            src/pactkit/bar.py         30     18    40%   1-18
            -------------------------------------------------------
            TOTAL                      80     28    65%
        """)
        files = _parse_coverage_output(output)
        assert len(files) == 2
        assert files[0]["file"] == "src/pactkit/foo.py"
        assert files[0]["coverage"] == 80
        assert files[1]["coverage"] == 40

    def test_module_path_extraction(self):
        from pactkit.coverage_gate import _extract_module_path

        assert _extract_module_path("src/pactkit/foo.py") == "pactkit.foo"
        assert _extract_module_path("src/pactkit/prompts/commands.py") == "pactkit.prompts.commands"


# ---------------------------------------------------------------------------
# R4: CLI wiring — 3 new subcommands
# ---------------------------------------------------------------------------
class TestR4CLIWiring:
    def test_lesson_append_subparser_exists(self):
        from pactkit.cli import main

        source = inspect.getsource(main)
        assert "lesson-append" in source

    def test_invariants_refresh_subparser_exists(self):
        from pactkit.cli import main

        source = inspect.getsource(main)
        assert "invariants-refresh" in source

    def test_coverage_gate_subparser_exists(self):
        from pactkit.cli import main

        source = inspect.getsource(main)
        assert "coverage-gate" in source


# ---------------------------------------------------------------------------
# R5: Prompt delegation — Done prompt references new CLI commands
# ---------------------------------------------------------------------------
class TestR5PromptDelegation:
    def _get_done_prompt(self):
        from pactkit.prompts.commands import COMMANDS_CONTENT
        return COMMANDS_CONTENT["project-done.md"]

    def test_done_references_lesson_append(self):
        done = self._get_done_prompt()
        assert "pactkit lesson-append" in done

    def test_done_references_invariants_refresh(self):
        done = self._get_done_prompt()
        assert "pactkit invariants-refresh" in done

    def test_done_references_coverage_gate(self):
        done = self._get_done_prompt()
        assert "pactkit coverage-gate" in done
