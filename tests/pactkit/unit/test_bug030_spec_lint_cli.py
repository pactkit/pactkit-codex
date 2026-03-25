"""Tests for BUG-030: pactkit spec-lint CLI subcommand.

Verifies that:
1. `pactkit spec-lint <file>` works correctly (AC1)
2. `pactkit spec-lint --all` works correctly (AC2)
3. Prompt templates no longer reference hardcoded path (AC3)
"""
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_VALID_SPEC = """\
# BUG-030: Test Spec

| Field     | Value |
|-----------|-------|
| ID        | BUG-030 |
| Status    | Draft |
| Priority  | High |
| Release   | 1.6.6 |

## Background

Some background.

## Target Call Chain

Some chain.

## Requirements

### R1: Some Requirement

This MUST work.

## Acceptance Criteria

### AC1: Happy Path (R1)
**Given** a valid spec
**When** R1 is linted
**Then** passes

## Security Scope

| Check | Applicable | Reason |
|-------|------------|--------|
| SEC-1 | N/A | Test only |

## Out of Scope

N/A
"""

INVALID_SPEC = """\
# BUG-030: Incomplete Spec

| Field     | Value |
|-----------|-------|
| ID        | BUG-030 |
| Status    | Draft |
| Priority  | High |
| Release   | 1.6.6 |

## Requirements

### R1: A Requirement

This MUST work.
"""


def run_cli(*args):
    """Invoke pactkit CLI via python -m pactkit.cli and return (stdout, stderr, exit_code)."""
    cmd = [sys.executable, "-m", "pactkit.cli"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


# ---------------------------------------------------------------------------
# AC1: pactkit spec-lint <file> (single file mode)
# ---------------------------------------------------------------------------

class TestSpecLintSingleFile:
    def test_valid_spec_exits_zero(self, tmp_path):
        spec = tmp_path / "BUG-030.md"
        spec.write_text(MINIMAL_VALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", str(spec))
        assert code == 0, f"Expected exit 0, got {code}. stdout={stdout}"

    def test_valid_spec_shows_pass(self, tmp_path):
        spec = tmp_path / "BUG-030.md"
        spec.write_text(MINIMAL_VALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", str(spec))
        assert "PASS" in stdout

    def test_invalid_spec_exits_nonzero(self, tmp_path):
        spec = tmp_path / "BAD.md"
        spec.write_text(INVALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", str(spec))
        assert code != 0, f"Expected non-zero exit, got {code}"

    def test_invalid_spec_shows_error(self, tmp_path):
        spec = tmp_path / "BAD.md"
        spec.write_text(INVALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", str(spec))
        assert "ERROR" in stdout or "FAIL" in stdout

    def test_no_args_shows_usage(self):
        stdout, stderr, code = run_cli("spec-lint")
        assert code != 0


# ---------------------------------------------------------------------------
# AC2: pactkit spec-lint --all (batch mode)
# ---------------------------------------------------------------------------

class TestSpecLintAll:
    def test_all_pass_exits_zero(self, tmp_path):
        (tmp_path / "A.md").write_text(MINIMAL_VALID_SPEC)
        (tmp_path / "B.md").write_text(MINIMAL_VALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", "--all", "--specs-dir", str(tmp_path))
        assert code == 0, f"Expected exit 0, got {code}. stdout={stdout}"

    def test_any_fail_exits_nonzero(self, tmp_path):
        (tmp_path / "valid.md").write_text(MINIMAL_VALID_SPEC)
        (tmp_path / "invalid.md").write_text(INVALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", "--all", "--specs-dir", str(tmp_path))
        assert code != 0

    def test_empty_dir_exits_zero(self, tmp_path):
        stdout, stderr, code = run_cli("spec-lint", "--all", "--specs-dir", str(tmp_path))
        assert code == 0

    def test_missing_dir_exits_nonzero(self, tmp_path):
        stdout, stderr, code = run_cli("spec-lint", "--all", "--specs-dir", str(tmp_path / "nonexistent"))
        assert code != 0

    def test_default_specs_dir(self, tmp_path, monkeypatch):
        """--all without --specs-dir uses docs/specs as default."""
        monkeypatch.chdir(tmp_path)
        specs_dir = tmp_path / "docs" / "specs"
        specs_dir.mkdir(parents=True)
        (specs_dir / "A.md").write_text(MINIMAL_VALID_SPEC)
        stdout, stderr, code = run_cli("spec-lint", "--all")
        assert code == 0


# ---------------------------------------------------------------------------
# AC3: Prompt templates no longer reference hardcoded path
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parents[2]
_COMMANDS_PY = _PROJECT_ROOT / "src" / "pactkit" / "prompts" / "commands.py"
_WORKFLOWS_PY = _PROJECT_ROOT / "src" / "pactkit" / "prompts" / "workflows.py"
_HARDCODED = "python3 src/pactkit/skills/spec_linter.py"


class TestPromptsUpdated:
    def test_commands_py_no_hardcoded_path(self):
        content = _COMMANDS_PY.read_text()
        assert _HARDCODED not in content, (
            f"commands.py still contains hardcoded path: '{_HARDCODED}'. "
            "Replace with 'pactkit spec-lint'."
        )

    def test_workflows_py_no_hardcoded_path(self):
        content = _WORKFLOWS_PY.read_text()
        assert _HARDCODED not in content, (
            f"workflows.py still contains hardcoded path: '{_HARDCODED}'. "
            "Replace with 'pactkit spec-lint'."
        )

    def test_commands_py_uses_pactkit_spec_lint(self):
        content = _COMMANDS_PY.read_text()
        assert "pactkit spec-lint" in content

    def test_workflows_py_uses_pactkit_spec_lint(self):
        content = _WORKFLOWS_PY.read_text()
        assert "pactkit spec-lint" in content
