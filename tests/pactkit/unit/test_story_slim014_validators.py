"""STORY-slim-014 R2: Document structure validators.

Tests for pactkit.validators module.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


class TestLintContext(unittest.TestCase):
    """Tests for lint_context()."""

    def _make_valid_context(self, tmp_dir: str) -> Path:
        content = """\
# Project Context (Auto-generated)

## Sprint Status
All done.

## Current Stories
None.

## Recent Completions
- STORY-001

## Active Branches
main

## Key Decisions
- Use Python.

## Next Recommended Action
/project-plan
"""
        path = Path(tmp_dir) / "context.md"
        path.write_text(content)
        return path

    def test_valid_context_returns_empty_list(self):
        from pactkit.validators import lint_context

        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_valid_context(tmp)
            errors = lint_context(path)
            self.assertEqual(errors, [])

    def test_missing_header_returns_error(self):
        from pactkit.validators import lint_context

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "context.md"
            # Write content without the canonical header
            path.write_text("## Sprint Status\nSome content.\n## Current Stories\n")
            errors = lint_context(path)
            self.assertTrue(any("Project Context" in e or "Auto-generated" in e for e in errors),
                            f"Expected header error, got: {errors}")

    def test_file_not_found_returns_error(self):
        from pactkit.validators import lint_context

        path = Path("/nonexistent/context.md")
        errors = lint_context(path)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("not found" in e.lower() or "no such" in e.lower() or "exist" in e.lower()
                            for e in errors),
                        f"Expected file-not-found error, got: {errors}")

    def test_missing_section_lists_specific_missing(self):
        from pactkit.validators import lint_context

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "context.md"
            # Include header but omit "## Active Branches" and "## Key Decisions"
            path.write_text(
                "# Project Context (Auto-generated)\n"
                "## Sprint Status\n"
                "## Current Stories\n"
                "## Recent Completions\n"
                "## Next Recommended Action\n"
            )
            errors = lint_context(path)
            error_text = " ".join(errors)
            self.assertIn("Active Branches", error_text)
            self.assertIn("Key Decisions", error_text)

    def test_all_sections_present_but_no_header_returns_error(self):
        from pactkit.validators import lint_context

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "context.md"
            path.write_text(
                "## Sprint Status\n"
                "## Current Stories\n"
                "## Recent Completions\n"
                "## Active Branches\n"
                "## Key Decisions\n"
                "## Next Recommended Action\n"
            )
            errors = lint_context(path)
            self.assertTrue(len(errors) > 0, "Should have error for missing header")


class TestLintLessons(unittest.TestCase):
    """Tests for lint_lessons()."""

    def _make_valid_lessons(self, tmp_dir: str) -> Path:
        content = """\
# Lessons Learned

| Date | Lesson | Context |
|------|--------|---------|
| 2026-01-01 | Always test first | TDD |
"""
        path = Path(tmp_dir) / "lessons.md"
        path.write_text(content)
        return path

    def test_valid_lessons_returns_empty_list(self):
        from pactkit.validators import lint_lessons

        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_valid_lessons(tmp)
            errors = lint_lessons(path)
            self.assertEqual(errors, [])

    def test_missing_table_header_returns_error(self):
        from pactkit.validators import lint_lessons

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lessons.md"
            # Only separator present, no header
            path.write_text("|------|--------|---------|")
            errors = lint_lessons(path)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("Date" in e or "Lesson" in e or "header" in e.lower() for e in errors),
                            f"Expected table header error, got: {errors}")

    def test_missing_separator_returns_error(self):
        from pactkit.validators import lint_lessons

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lessons.md"
            # Only header present, no separator
            path.write_text("| Date | Lesson | Context |")
            errors = lint_lessons(path)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("separator" in e.lower() or "---" in e for e in errors),
                            f"Expected separator error, got: {errors}")

    def test_file_not_found_returns_error(self):
        from pactkit.validators import lint_lessons

        path = Path("/nonexistent/lessons.md")
        errors = lint_lessons(path)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("not found" in e.lower() or "no such" in e.lower() or "exist" in e.lower()
                            for e in errors),
                        f"Expected file-not-found error, got: {errors}")

    def test_partial_content_missing_separator_error(self):
        from pactkit.validators import lint_lessons

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lessons.md"
            # Header present but no separator line
            path.write_text("| Date | Lesson | Context |\n| 2026-01-01 | A | B |\n")
            errors = lint_lessons(path)
            # Separator is missing
            self.assertTrue(len(errors) > 0)


class TestLintTestcase(unittest.TestCase):
    """Tests for lint_testcase()."""

    def _make_valid_testcase(self, tmp_dir: str) -> Path:
        content = """\
# Test Cases: STORY-001 — My Feature

## TC-01: Happy path

- **Given** a valid input
- **When** the function is called
- **Then** it returns success

## TC-02: Error case

- **Given** an invalid input
- **When** the function is called
- **Then** it returns an error
"""
        path = Path(tmp_dir) / "STORY-001_case.md"
        path.write_text(content)
        return path

    def test_valid_testcase_returns_empty_list(self):
        from pactkit.validators import lint_testcase

        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_valid_testcase(tmp)
            errors = lint_testcase(path)
            self.assertEqual(errors, [])

    def test_missing_scenario_pattern_returns_error(self):
        from pactkit.validators import lint_testcase

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.md"
            # Has keywords but no ## TC-NN: pattern
            path.write_text(
                "# Test Cases\n\n"
                "- **Given** something\n"
                "- **When** action\n"
                "- **Then** result\n"
            )
            errors = lint_testcase(path)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("TC-" in e or "scenario" in e.lower() for e in errors),
                            f"Expected scenario pattern error, got: {errors}")

    def test_missing_keywords_returns_error(self):
        from pactkit.validators import lint_testcase

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.md"
            # Has TC pattern but missing **Then**
            path.write_text(
                "## TC-01: Something\n\n"
                "- **Given** something\n"
                "- **When** action\n"
            )
            errors = lint_testcase(path)
            self.assertTrue(len(errors) > 0)
            self.assertTrue(any("Then" in e for e in errors),
                            f"Expected 'Then' keyword error, got: {errors}")

    def test_file_not_found_returns_error(self):
        from pactkit.validators import lint_testcase

        path = Path("/nonexistent/case.md")
        errors = lint_testcase(path)
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any("not found" in e.lower() or "no such" in e.lower() or "exist" in e.lower()
                            for e in errors),
                        f"Expected file-not-found error, got: {errors}")

    def test_all_keywords_listed_when_multiple_missing(self):
        from pactkit.validators import lint_testcase

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "case.md"
            # Has TC pattern but no keywords at all
            path.write_text("## TC-01: Empty scenario\n\nNo content here.\n")
            errors = lint_testcase(path)
            error_text = " ".join(errors)
            # All three keywords should be mentioned
            self.assertIn("Given", error_text)
            self.assertIn("When", error_text)
            self.assertIn("Then", error_text)


if __name__ == "__main__":
    unittest.main()
