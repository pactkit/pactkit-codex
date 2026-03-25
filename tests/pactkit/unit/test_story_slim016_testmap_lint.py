"""Tests for STORY-slim-016: Test Mapping & Stack-Aware Lint CLI.

Covers R1-R4: test-map, lint runner, CLI wiring, prompt delegation.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# R1: map_to_tests
# ---------------------------------------------------------------------------

class TestR1TestMapper:
    """test-map must map source files to test files."""

    def test_python_source_to_test(self, tmp_path):
        """Python src/pactkit/cli.py → tests/unit/test_cli.py."""
        from pactkit.test_mapper import map_to_tests

        # Create marker + test file
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)
        (test_dir / "test_cli.py").write_text("# test\n")

        result = map_to_tests(["src/pactkit/cli.py"], tmp_path)
        assert any("test_cli.py" in str(p) for p in result["mapped"])

    def test_nonexistent_test_not_returned(self, tmp_path):
        """If test file doesn't exist on disk → not in mapped list."""
        from pactkit.test_mapper import map_to_tests

        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = map_to_tests(["src/pactkit/brand_new.py"], tmp_path)
        assert result["mapped"] == []

    def test_multiple_files_mapped(self, tmp_path):
        """Multiple source files → multiple test files."""
        from pactkit.test_mapper import map_to_tests

        (tmp_path / "pyproject.toml").write_text("[project]\n")
        test_dir = tmp_path / "tests" / "unit"
        test_dir.mkdir(parents=True)
        (test_dir / "test_cli.py").write_text("# test\n")
        (test_dir / "test_config.py").write_text("# test\n")

        result = map_to_tests(
            ["src/pactkit/cli.py", "src/pactkit/config.py"], tmp_path
        )
        assert len(result["mapped"]) == 2

    def test_non_source_file_ignored(self, tmp_path):
        """Non-source files (docs, configs) → no mapping."""
        from pactkit.test_mapper import map_to_tests

        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = map_to_tests(["README.md", "docs/specs/STORY-001.md"], tmp_path)
        assert result["mapped"] == []

    def test_unknown_stack_returns_empty(self, tmp_path):
        """Unknown stack with no LANG_PROFILES entry → empty with reason."""
        from pactkit.test_mapper import map_to_tests

        # No marker files → defaults to python, but test with explicit override
        result = map_to_tests(["src/app.rs"], tmp_path)
        # Python default still applies, but test file won't exist
        assert result["mapped"] == []


# ---------------------------------------------------------------------------
# R2: run_lint
# ---------------------------------------------------------------------------

class TestR2LintRunner:
    """lint must run correct command for stack."""

    @patch("pactkit.lint_runner.subprocess.run")
    def test_python_lint_command(self, mock_run, tmp_path):
        """Python project → runs ruff check."""
        from pactkit.lint_runner import run_lint

        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = run_lint(tmp_path)
        assert result["exit_code"] == 0
        # Should have called ruff
        cmd_str = str(mock_run.call_args)
        assert "ruff" in cmd_str

    @patch("pactkit.lint_runner.subprocess.run")
    def test_lint_fix_runs_fix_first(self, mock_run, tmp_path):
        """--fix flag → runs with fix flag first."""
        from pactkit.lint_runner import run_lint

        mock_run.return_value = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        run_lint(tmp_path, fix=True)
        # Should have been called at least twice (fix + check)
        assert mock_run.call_count >= 2

    @patch("pactkit.lint_runner.subprocess.run")
    def test_lint_blocking_from_config(self, mock_run, tmp_path):
        """lint_blocking: true in config → blocking=True in result."""
        from pactkit.lint_runner import run_lint

        mock_run.return_value = type("R", (), {"returncode": 1, "stdout": "error", "stderr": ""})()
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        config_dir = tmp_path / ".claude"
        config_dir.mkdir()
        (config_dir / "pactkit.yaml").write_text(
            "stack: python\nlint_blocking: true\n"
        )

        result = run_lint(tmp_path)
        assert result["blocking"] is True

    def test_no_lint_command_skips(self, tmp_path):
        """Unknown stack with no lint command → skip."""
        from pactkit.lint_runner import run_lint

        # Force unknown stack by patching
        with patch("pactkit.lint_runner.detect_stack", return_value="rust"):
            result = run_lint(tmp_path)
        assert result["exit_code"] == 0
        assert "skip" in result["message"].lower() or "no lint" in result["message"].lower()


# ---------------------------------------------------------------------------
# R3: CLI wiring
# ---------------------------------------------------------------------------

class TestR3CLIWiring:
    """CLI must expose test-map and lint subcommands."""

    _PACTKIT = shutil.which("pactkit") or str(Path(__file__).parents[2] / ".venv" / "bin" / "pactkit")

    def test_test_map_subcommand_exists(self):
        """pactkit test-map should be a recognized subcommand."""
        import subprocess
        result = subprocess.run(
            [self._PACTKIT, "test-map", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_lint_subcommand_exists(self):
        """pactkit lint should be a recognized subcommand."""
        import subprocess
        result = subprocess.run(
            [self._PACTKIT, "lint", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# R4: Prompt delegation
# ---------------------------------------------------------------------------

class TestR4PromptDelegation:
    """Prompts must delegate to pactkit test-map and pactkit lint."""

    def _reload_prompts(self):
        import importlib

        import pactkit.prompts as p
        importlib.reload(p)
        return p

    def test_act_references_pactkit_test_map(self):
        """Act Phase 3 must reference pactkit test-map."""
        p = self._reload_prompts()
        act = p.COMMANDS_CONTENT["project-act.md"]
        assert "pactkit test-map" in act

    def test_done_references_pactkit_lint(self):
        """Done Phase 2.5 Step 2.7 must reference pactkit lint."""
        p = self._reload_prompts()
        done = p.COMMANDS_CONTENT["project-done.md"]
        assert "pactkit lint" in done

    def test_hotfix_references_pactkit_test_map(self):
        """Hotfix must reference pactkit test-map."""
        from pactkit.prompts.workflows import HOTFIX_PROMPT
        assert "pactkit test-map" in HOTFIX_PROMPT

    def test_check_references_pactkit_test_map(self):
        """Check must reference pactkit test-map."""
        p = self._reload_prompts()
        check = p.COMMANDS_CONTENT["project-check.md"]
        assert "pactkit test-map" in check
