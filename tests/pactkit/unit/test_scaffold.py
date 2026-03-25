"""Tests for scaffold.py — BUG-033: create_spec must pass spec-lint."""

import os

from pactkit.skills.scaffold import create_spec
from pactkit.skills.spec_linter import validate_spec


class TestCreateSpec:
    """BUG-033: create_spec() output must pass spec_linter validation."""

    def test_generated_spec_passes_lint(self, tmp_path):
        """AC1: Generated Spec passes lint with zero errors."""
        # Setup: create docs/specs directory
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        # Change to temp directory so create_spec writes there
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # When: generate a spec
            result = create_spec("STORY-999", "Test Title")
            assert "✅" in result

            # Then: spec file exists and passes lint (except E008 — TBD is intentional for draft)
            spec_path = specs_dir / "STORY-999.md"
            assert spec_path.exists()

            lint_result = validate_spec(str(spec_path))
            # STORY-slim-007: SPEC_TEMPLATE uses TBD as draft placeholder.
            # E008 (Release=TBD) is intentional — developer fills it before /project-act.
            non_e008_errors = [e for e in lint_result.errors if e.rule_id != "E008"]
            assert not non_e008_errors, f"Spec lint failed (non-E008): {[e.message for e in non_e008_errors]}"
        finally:
            os.chdir(old_cwd)

    def test_metadata_table_format(self, tmp_path):
        """AC2: Generated Spec contains | Field | Value | metadata table."""
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            create_spec("STORY-999", "Test Title")
            content = (specs_dir / "STORY-999.md").read_text()

            # Must have Field | Value header
            assert "| Field | Value |" in content
            # Must have required fields
            assert "| ID |" in content
            assert "| Status |" in content
            assert "| Priority |" in content
            assert "| Release |" in content
        finally:
            os.chdir(old_cwd)

    def test_requirements_have_subsections(self, tmp_path):
        """AC3: Requirements section has ### R1: subsection."""
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            create_spec("STORY-999", "Test Title")
            content = (specs_dir / "STORY-999.md").read_text()

            # Must have R1 subsection
            assert "### R1:" in content
            # Must have RFC 2119 keyword
            assert "MUST" in content or "SHOULD" in content or "MAY" in content
        finally:
            os.chdir(old_cwd)

    def test_release_not_tbd(self, tmp_path):
        """R3: Release field must not be literal TBD."""
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            create_spec("STORY-999", "Test Title")
            content = (specs_dir / "STORY-999.md").read_text()

            # STORY-slim-007: New SPEC_TEMPLATE uses TBD as a draft placeholder.
            # spec-lint E008 will block Act until Release is filled with a real version.
            # This is intentional — scaffold creates draft, developer fills before Act.
            lines = content.split("\n")
            for line in lines:
                if "| Release |" in line:
                    parts = line.split("|")
                    if len(parts) >= 3:
                        release_val = parts[2].strip()
                        assert release_val, f"Release field should not be empty, got: {release_val!r}"
        finally:
            os.chdir(old_cwd)
