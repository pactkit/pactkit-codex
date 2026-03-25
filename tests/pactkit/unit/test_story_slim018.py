"""STORY-slim-018: Systemic Cross-Flow Guards — tests for R2, R3.

R2: LANG_PROFILE_REQUIRED_KEYS canonical in schemas.py
R3: Spec Status lifecycle (spec-status CLI, W006 lint rule, Done prompt)
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# =========================================================================
# R2: LANG_PROFILE_REQUIRED_KEYS is canonical (AC3, AC4)
# =========================================================================
class TestR2LangProfileCanonicalKeys:
    """AC3: All test files import from schemas.py, not hardcode."""

    def test_schemas_defines_lang_profile_required_keys(self):
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        assert isinstance(LANG_PROFILE_REQUIRED_KEYS, frozenset)
        assert len(LANG_PROFILE_REQUIRED_KEYS) >= 5

    def test_all_profiles_match_canonical_keys(self):
        """AC4: Every LANG_PROFILES entry has exactly the canonical keys."""
        from pactkit.prompts.workflows import LANG_PROFILES
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        for lang, profile in LANG_PROFILES.items():
            assert set(profile.keys()) == LANG_PROFILE_REQUIRED_KEYS, (
                f"LANG_PROFILES[{lang}] keys {set(profile.keys())} != canonical {LANG_PROFILE_REQUIRED_KEYS}"
            )

    def test_canonical_keys_contain_expected_fields(self):
        from pactkit.schemas import LANG_PROFILE_REQUIRED_KEYS
        for key in ("test_runner", "file_ext", "source_dirs", "test_map_pattern", "lint_command"):
            assert key in LANG_PROFILE_REQUIRED_KEYS


# =========================================================================
# R3: Spec Status lifecycle (AC5, AC6)
# =========================================================================
class TestR3SpecValidStatuses:
    """SPEC_VALID_STATUSES defined in schemas.py."""

    def test_spec_valid_statuses_defined(self):
        from pactkit.schemas import SPEC_VALID_STATUSES
        assert "Draft" in SPEC_VALID_STATUSES
        assert "In Progress" in SPEC_VALID_STATUSES
        assert "Done" in SPEC_VALID_STATUSES

    def test_spec_valid_statuses_is_tuple(self):
        from pactkit.schemas import SPEC_VALID_STATUSES
        assert isinstance(SPEC_VALID_STATUSES, tuple)


class TestR3W006SpecLintStatusValidation:
    """AC6: spec-lint W006 flags invalid Status values."""

    def test_valid_status_no_w006(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec
        spec = tmp_path / "test.md"
        spec.write_text(
            "# TEST-001: Test\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| ID | TEST-001 |\n| Status | Draft |\n| Priority | High |\n| Release | 1.0.0 |\n\n"
            "## Requirements\n\n### R1: Something (MUST)\n\nDo it.\n\n"
            "## Acceptance Criteria\n\n### AC1: Check\n\n- **Given** X\n- **When** Y\n- **Then** Z\n"
        )
        result = validate_spec(str(spec))
        w006_warnings = [w for w in result.warnings if w.rule_id == "W006"]
        assert len(w006_warnings) == 0

    def test_invalid_status_triggers_w006(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec
        spec = tmp_path / "test.md"
        spec.write_text(
            "# TEST-001: Test\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| ID | TEST-001 |\n| Status | Foobar |\n| Priority | High |\n| Release | 1.0.0 |\n\n"
            "## Requirements\n\n### R1: Something (MUST)\n\nDo it.\n\n"
            "## Acceptance Criteria\n\n### AC1: Check\n\n- **Given** X\n- **When** Y\n- **Then** Z\n"
        )
        result = validate_spec(str(spec))
        w006_warnings = [w for w in result.warnings if w.rule_id == "W006"]
        assert len(w006_warnings) == 1
        assert "Foobar" in w006_warnings[0].message

    def test_done_status_no_w006(self, tmp_path):
        from pactkit.skills.spec_linter import validate_spec
        spec = tmp_path / "test.md"
        spec.write_text(
            "# TEST-001: Test\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| ID | TEST-001 |\n| Status | Done |\n| Priority | High |\n| Release | 1.0.0 |\n\n"
            "## Requirements\n\n### R1: Something (MUST)\n\nDo it.\n\n"
            "## Acceptance Criteria\n\n### AC1: Check\n\n- **Given** X\n- **When** Y\n- **Then** Z\n"
        )
        result = validate_spec(str(spec))
        w006_warnings = [w for w in result.warnings if w.rule_id == "W006"]
        assert len(w006_warnings) == 0


class TestR3DonePromptSpecStatus:
    """AC5: Done prompt contains instruction to update Spec Status."""

    def test_done_prompt_contains_spec_status_instruction(self):
        from pactkit.prompts import COMMANDS_CONTENT
        done = COMMANDS_CONTENT["project-done.md"]
        assert "Status" in done
        assert "Done" in done
        # Must mention updating the spec status field
        assert "spec-status" in done or "Status | Draft" in done or "Status | Done" in done


class TestR3SpecStatusCli:
    """R3.2: pactkit spec-status CLI subcommand exists."""

    def test_spec_status_registered_as_subcommand(self):
        import inspect

        from pactkit.cli import main

        source = inspect.getsource(main)
        assert "spec-status" in source

    def test_spec_status_updates_status_field(self, tmp_path):
        """spec-status updates | Status | Draft | to | Status | Done |."""
        from pactkit.spec_status import update_spec_status
        spec = tmp_path / "TEST-001.md"
        spec.write_text(
            "# TEST-001: Test\n\n"
            "| Field | Value |\n|-------|-------|\n"
            "| ID | TEST-001 |\n| Status | Draft |\n| Priority | High |\n| Release | 1.0.0 |\n"
        )
        update_spec_status(spec, "Done")
        content = spec.read_text()
        assert "| Status | Done |" in content
        assert "| Status | Draft |" not in content
