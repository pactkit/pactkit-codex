"""Tests for STORY-slim-007: Document Schema Registry.

Covers:
- AC1: schemas.py contains all document type constants
- AC2: spec_linter references schemas (no hardcoded strings)
- AC3: scaffold SPEC_TEMPLATE passes spec-lint with 0 errors
- AC4: context.md section list defined once in schemas, referenced via {CONTEXT_SECTIONS}
- AC5: pactkit schema spec CLI output is correct
"""

import re
import subprocess
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# AC1: schemas.py exists and contains all document type constants
# ---------------------------------------------------------------------------


class TestSchemasModule:
    def test_importable(self):
        from pactkit import schemas  # noqa: F401

    def test_spec_constants_exist(self):
        from pactkit.schemas import (
            SPEC_AC_PATTERN,
            SPEC_GIVEN_WHEN_THEN,
            SPEC_REQUIRED_METADATA_FIELDS,
            SPEC_REQUIRED_SECTIONS,
            SPEC_REQUIREMENT_PATTERN,
            SPEC_RFC_KEYWORDS,
        )

        assert len(SPEC_REQUIRED_METADATA_FIELDS) >= 4
        assert "## Requirements" in SPEC_REQUIRED_SECTIONS
        assert "## Acceptance Criteria" in SPEC_REQUIRED_SECTIONS
        assert re.compile(SPEC_REQUIREMENT_PATTERN)
        assert re.compile(SPEC_AC_PATTERN)
        assert "Given" in SPEC_GIVEN_WHEN_THEN
        assert "MUST" in SPEC_RFC_KEYWORDS

    def test_board_constants_exist(self):
        from pactkit.schemas import (
            BOARD_SECTION_BACKLOG,
            BOARD_SECTION_DONE,
            BOARD_SECTION_IN_PROGRESS,
            BOARD_SECTIONS,
            BOARD_TASK_CHECKED,
            BOARD_TASK_UNCHECKED,
        )

        assert "Backlog" in BOARD_SECTION_BACKLOG
        assert "In Progress" in BOARD_SECTION_IN_PROGRESS
        assert "Done" in BOARD_SECTION_DONE
        assert len(BOARD_SECTIONS) == 3
        assert "[ ]" in BOARD_TASK_UNCHECKED
        assert "[x]" in BOARD_TASK_CHECKED

    def test_context_constants_exist(self):
        from pactkit.schemas import CONTEXT_HEADER, CONTEXT_SECTIONS

        assert "Project Context" in CONTEXT_HEADER
        assert len(CONTEXT_SECTIONS) >= 6
        required_sections = (
            "## Sprint Status",
            "## Current Stories",
            "## Recent Completions",
            "## Active Branches",
            "## Key Decisions",
            "## Next Recommended Action",
        )
        for section in required_sections:
            assert section in CONTEXT_SECTIONS, f"Missing: {section}"

    def test_lessons_constants_exist(self):
        from pactkit.schemas import (
            LESSONS_ROW_FORMAT,
            LESSONS_TABLE_HEADER,
        )

        assert "Date" in LESSONS_TABLE_HEADER
        assert "Lesson" in LESSONS_TABLE_HEADER
        assert "Context" in LESSONS_TABLE_HEADER
        assert "{date}" in LESSONS_ROW_FORMAT
        assert "{lesson}" in LESSONS_ROW_FORMAT
        assert "{context}" in LESSONS_ROW_FORMAT

    def test_test_case_constants_exist(self):
        from pactkit.schemas import (
            TEST_CASE_KEYWORDS,
            TEST_CASE_SCENARIO_PATTERN,
            TEST_CASE_TITLE_FORMAT,
        )

        assert "{id}" in TEST_CASE_TITLE_FORMAT
        assert re.compile(TEST_CASE_SCENARIO_PATTERN)
        assert "**Given**" in TEST_CASE_KEYWORDS

    def test_spec_template_exists(self):
        from pactkit.schemas import SPEC_TEMPLATE

        assert "## Requirements" in SPEC_TEMPLATE
        assert "## Acceptance Criteria" in SPEC_TEMPLATE
        assert "## Background" in SPEC_TEMPLATE
        assert "{id}" in SPEC_TEMPLATE
        assert "{title}" in SPEC_TEMPLATE


# ---------------------------------------------------------------------------
# AC2: spec_linter references schemas (no hardcoded strings)
# ---------------------------------------------------------------------------


class TestSpecLinterReferencesSchemas:
    def _get_linter_source(self):
        return (_PROJECT_ROOT / "src/pactkit/skills/spec_linter.py").read_text()

    def test_no_hardcoded_requirements_string(self):
        src = self._get_linter_source()
        # After R2: "## Requirements" must come from schemas, not inline literal
        # Check that it imports from schemas
        assert "from pactkit.schemas import" in src or "pactkit.schemas" in src, (
            "spec_linter.py must import from pactkit.schemas"
        )

    def test_required_fields_from_schemas(self):
        """Required field list ['ID', 'Status', ...] must come from schemas, not hardcoded."""
        src = self._get_linter_source()
        # Should NOT have the old hardcoded list
        assert '["ID", "Status", "Priority", "Release"]' not in src, (
            "Hardcoded required fields list must be replaced with SPEC_REQUIRED_METADATA_FIELDS"
        )

    def test_given_when_then_from_schemas(self):
        """('given', 'when', 'then') check must use SPEC_GIVEN_WHEN_THEN from schemas."""
        src = self._get_linter_source()
        # Should not hardcode the tuple inline in the check
        assert '("given", "when", "then")' not in src, (
            "Inline Given/When/Then tuple must be replaced with SPEC_GIVEN_WHEN_THEN from schemas"
        )

    def test_rfc2119_pattern_from_schemas(self):
        """RFC2119 regex pattern must come from schemas or reference SPEC_RFC_KEYWORDS."""
        src = self._get_linter_source()
        # The RFC pattern is compiled — it should reference SPEC_RFC_KEYWORDS or SPEC_RFC_PATTERN
        assert "SPEC_RFC" in src or "schemas" in src, "RFC2119 pattern must reference pactkit.schemas"


# ---------------------------------------------------------------------------
# AC3: scaffold SPEC_TEMPLATE passes spec-lint with 0 ERRORs
# ---------------------------------------------------------------------------


class TestSpecTemplateConsistency:
    def test_spec_template_passes_lint(self, tmp_path):
        """SPEC_TEMPLATE must produce a spec that passes spec-lint (no ERRORs)."""
        from pactkit.schemas import SPEC_TEMPLATE

        # Generate a spec from the template with a concrete release version
        spec_content = SPEC_TEMPLATE.format(id="STORY-test-001", title="Test Story")
        spec_content = spec_content.replace("| Release | TBD |", "| Release | 2.0.0 |")
        spec_file = tmp_path / "STORY-test-001.md"
        spec_file.write_text(spec_content)

        from pactkit.skills.spec_linter import validate_spec

        result = validate_spec(str(spec_file))
        assert result.passed, f"SPEC_TEMPLATE produces lint errors: {[str(e) for e in result.errors]}"

    def test_scaffold_create_spec_uses_template(self, tmp_path):
        """create_spec() output must include all fields from SPEC_TEMPLATE."""
        from unittest.mock import patch

        from pactkit.schemas import SPEC_REQUIRED_METADATA_FIELDS, SPEC_REQUIRED_SECTIONS
        from pactkit.skills.scaffold import create_spec

        with patch("pactkit.skills.scaffold.Path") as MockPath:
            MockPath.cwd.return_value = tmp_path
            MockPath.side_effect = Path
            create_spec("STORY-test-002", "Test Title")

        spec_file = tmp_path / "docs/specs/STORY-test-002.md"
        assert spec_file.exists()
        content = spec_file.read_text()

        for field in SPEC_REQUIRED_METADATA_FIELDS:
            assert f"| {field} |" in content, f"Missing field: {field}"
        for section in SPEC_REQUIRED_SECTIONS:
            assert section in content, f"Missing section: {section}"


# ---------------------------------------------------------------------------
# AC4: context.md sections defined once in schemas
# ---------------------------------------------------------------------------


class TestContextSectionsUnified:
    def test_context_sections_used_in_render_prompt(self):
        """_render_prompt must include CONTEXT_SECTIONS variable."""
        from pactkit.generators.deployer import _render_prompt
        from pactkit.profiles import get_profile
        from pactkit.schemas import CONTEXT_SECTIONS

        profile = get_profile("classic")
        template = "{CONTEXT_SECTIONS}"
        result = _render_prompt(template, profile)
        # Should have been replaced with actual section list
        assert "{CONTEXT_SECTIONS}" not in result
        for section in CONTEXT_SECTIONS:
            assert section in result

    def test_commands_playbooks_use_context_sections_var(self):
        """commands.py playbooks should use {CONTEXT_SECTIONS} not inline section lists."""
        content = (_PROJECT_ROOT / "src/pactkit/prompts/commands.py").read_text()
        # Check that the variable is used
        assert "{CONTEXT_SECTIONS}" in content, "commands.py must use {CONTEXT_SECTIONS} template variable"
        # Should NOT have the old inline section list pattern repeated 3 times
        occurrences = content.count("## Sprint Status")
        assert occurrences <= 1, (
            f"'## Sprint Status' appears {occurrences} times in commands.py — "
            "should be defined once in schemas.py and referenced via {{CONTEXT_SECTIONS}}"
        )


# ---------------------------------------------------------------------------
# AC5: pactkit schema CLI output
# ---------------------------------------------------------------------------


class TestSchemaCommand:
    def _run(self, *args):
        return subprocess.run(["pactkit", "schema", *args], capture_output=True, text=True, cwd=_PROJECT_ROOT)

    def test_schema_spec_output(self):
        result = self._run("spec")
        assert result.returncode == 0, f"pactkit schema spec failed: {result.stderr}"
        assert "## Requirements" in result.stdout
        assert "AC" in result.stdout or "Given" in result.stdout

    def test_schema_board_output(self):
        result = self._run("board")
        assert result.returncode == 0
        assert "Backlog" in result.stdout
        assert "In Progress" in result.stdout

    def test_schema_all_output(self):
        result = self._run("--all")
        assert result.returncode == 0
        assert "spec" in result.stdout.lower()
        assert "board" in result.stdout.lower()

    def test_schema_context_output(self):
        result = self._run("context")
        assert result.returncode == 0
        assert "Sprint Status" in result.stdout
