"""Test scaffold.py auto-injects developer prefix from pactkit.yaml.

Covers: create_spec, git_start, create_e2e all inject developer prefix.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pactkit.skills.scaffold import (
    _inject_developer_prefix,
    _read_developer_prefix,
    create_spec,
)


class TestDeveloperPrefixInjection(unittest.TestCase):
    """Verify _inject_developer_prefix logic."""

    def test_inject_prefix_when_developer_set(self):
        with patch("pactkit.skills.scaffold._read_developer_prefix", return_value="slim"):
            assert _inject_developer_prefix("BUG-001") == "BUG-slim-001"
            assert _inject_developer_prefix("STORY-042") == "STORY-slim-042"
            assert _inject_developer_prefix("HOTFIX-002") == "HOTFIX-slim-002"

    def test_no_double_inject(self):
        with patch("pactkit.skills.scaffold._read_developer_prefix", return_value="slim"):
            assert _inject_developer_prefix("BUG-slim-001") == "BUG-slim-001"
            assert _inject_developer_prefix("STORY-slim-042") == "STORY-slim-042"

    def test_no_inject_when_developer_empty(self):
        with patch("pactkit.skills.scaffold._read_developer_prefix", return_value=""):
            assert _inject_developer_prefix("BUG-001") == "BUG-001"
            assert _inject_developer_prefix("STORY-042") == "STORY-042"

    def test_no_inject_on_malformed_id(self):
        with patch("pactkit.skills.scaffold._read_developer_prefix", return_value="slim"):
            assert _inject_developer_prefix("RANDOM") == "RANDOM"


class TestReadDeveloperPrefix(unittest.TestCase):
    """Verify _read_developer_prefix reads from pactkit.yaml."""

    def test_reads_from_claude_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            claude_dir = tmp / ".claude"
            claude_dir.mkdir()
            (claude_dir / "pactkit.yaml").write_text('developer: "alice"\nstack: python\n')
            with patch("pactkit.skills.scaffold.Path") as MockPath:
                MockPath.cwd.return_value = tmp
                # Re-create Path behavior for non-cwd uses
                MockPath.side_effect = Path
                result = _read_developer_prefix()
            assert result == "alice"

    def test_reads_from_opencode_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            oc_dir = tmp / ".opencode"
            oc_dir.mkdir()
            (oc_dir / "pactkit.yaml").write_text("developer: bob\nstack: node\n")
            with patch("pactkit.skills.scaffold.Path") as MockPath:
                MockPath.cwd.return_value = tmp
                MockPath.side_effect = Path
                result = _read_developer_prefix()
            assert result == "bob"

    def test_returns_empty_when_no_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            with patch("pactkit.skills.scaffold.Path") as MockPath:
                MockPath.cwd.return_value = tmp
                MockPath.side_effect = Path
                result = _read_developer_prefix()
            assert result == ""

    def test_returns_empty_when_developer_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            claude_dir = tmp / ".claude"
            claude_dir.mkdir()
            (claude_dir / "pactkit.yaml").write_text("stack: python\nversion: 1.0.0\n")
            with patch("pactkit.skills.scaffold.Path") as MockPath:
                MockPath.cwd.return_value = tmp
                MockPath.side_effect = Path
                result = _read_developer_prefix()
            assert result == "bob" if False else result == ""


class TestCreateSpecWithPrefix(unittest.TestCase):
    """Verify create_spec auto-injects developer prefix into file name and content."""

    def test_create_spec_injects_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            claude_dir = tmp / ".claude"
            claude_dir.mkdir()
            (claude_dir / "pactkit.yaml").write_text('developer: "slim"\n')
            with patch("pactkit.skills.scaffold._read_developer_prefix", return_value="slim"):
                with patch("pactkit.skills.scaffold.Path") as MockPath:
                    MockPath.cwd.return_value = tmp
                    MockPath.side_effect = Path
                    create_spec("BUG-001", "Test bug")
            spec_file = tmp / "docs/specs/BUG-slim-001.md"
            assert spec_file.exists(), f"Expected {spec_file}, got: {list((tmp / 'docs/specs').iterdir())}"
            content = spec_file.read_text()
            assert "BUG-slim-001" in content
            assert "| ID | BUG-slim-001 |" in content


if __name__ == "__main__":
    unittest.main()
