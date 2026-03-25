"""STORY-slim-014 R7: Lazy Visualize — skip graph generation when no source changes.

Tests for pactkit.lazy_visualize module.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestShouldVisualize(unittest.TestCase):
    """Tests for should_visualize()."""

    def _make_graph(self, project_root: Path) -> Path:
        """Create the code_graph.mmd file."""
        graph_dir = project_root / "docs" / "architecture" / "graphs"
        graph_dir.mkdir(parents=True, exist_ok=True)
        graph_file = graph_dir / "code_graph.mmd"
        graph_file.write_text("graph TD\n  A --> B\n")
        return graph_file

    def test_no_source_changes_graph_exists_returns_false(self):
        """When no source changes and graph exists, should return (False, skip reason)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Create pyproject.toml so stack=python
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "docs/README.md\n"  # only docs changed

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertFalse(should_run)
        self.assertIn("Graph up-to-date", reason)

    def test_source_file_changed_returns_true(self):
        """When a source .py file changed, should return (True, mention of changed files)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "src/pactkit/validators.py\n"

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)
        self.assertIn("source files changed", reason)

    def test_graph_missing_returns_true(self):
        """When graph file does not exist, should return (True, mention graph missing)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            # Do NOT create the graph file

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""  # No changed files

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)
        self.assertIn("code_graph.mmd", reason)

    def test_git_failure_returns_true(self):
        """When git command fails (not a git repo), should return (True, unable to detect)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            with patch("subprocess.run", side_effect=subprocess.CalledProcessError(128, "git")):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)
        self.assertIn("unable to detect", reason)

    def test_git_exception_returns_true(self):
        """When subprocess.run raises an OSError, should return (True, unable to detect)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            with patch("subprocess.run", side_effect=OSError("not found")):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)
        self.assertIn("unable to detect", reason)

    def test_source_change_takes_priority_over_graph_exists(self):
        """Even when graph exists, source changes should trigger visualization."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "src/pactkit/new_module.py\nother/file.md\n"

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)

    def test_both_source_change_and_graph_missing_returns_true(self):
        """When both source files changed and graph missing, returns True."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            # No graph file

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "src/main.py\n"

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)

    def test_return_type_is_tuple(self):
        """Return value must be a tuple of (bool, str)."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""

            with patch("subprocess.run", return_value=mock_result):
                result = should_visualize(root)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], bool)
        self.assertIsInstance(result[1], str)

    def test_non_source_ext_file_changed_no_trigger(self):
        """Changing a .md file in docs should not trigger when graph exists."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "docs/architecture/graphs/code_graph.mmd\nREADME.md\n"

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        # .mmd and .md files are not .py source files
        self.assertFalse(should_run)

    def test_explicit_stack_python(self):
        """stack='python' explicitly uses .py source_dirs check."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "src/pactkit/module.py\n"

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root, stack="python")

        self.assertTrue(should_run)

    def test_git_returns_nonzero_but_no_exception_treated_as_failure(self):
        """When git returns non-zero exit code without exception, treat as failure."""
        from pactkit.lazy_visualize import should_visualize

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            self._make_graph(root)

            mock_result = MagicMock()
            mock_result.returncode = 128
            mock_result.stdout = ""

            with patch("subprocess.run", return_value=mock_result):
                should_run, reason = should_visualize(root)

        self.assertTrue(should_run)
        self.assertIn("unable to detect", reason)


if __name__ == "__main__":
    unittest.main()
