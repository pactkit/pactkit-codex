"""Tests for STORY-004: Project Visibility — metadata and content correctness."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestReadmeContent:
    """STORY-004 R4: README must not reference deleted features."""

    def _readme(self):
        return (PROJECT_ROOT / "README.md").read_text()

    def test_no_mode_common_reference(self):
        """README must not reference --mode common (deleted feature)."""
        content = self._readme()
        assert "--mode common" not in content

    def test_no_mode_common_description(self):
        """README must not describe Common mode."""
        content = self._readme().lower()
        assert "common mode" not in content

    def test_quick_start_no_mode_flag(self):
        """Quick Start code blocks must not use --mode."""
        content = self._readme()
        # Find code blocks and check none contain --mode
        in_code = False
        for line in content.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code and "--mode" in line:
                raise AssertionError(f"Code block contains --mode: {line}")


class TestPyprojectMetadata:
    """STORY-004 R5: PyPI metadata must be up to date."""

    def _pyproject(self):
        return (PROJECT_ROOT / "pyproject.toml").read_text()

    def test_classifier_production_stable(self):
        """Classifier must be Production/Stable, not Beta."""
        content = self._pyproject()
        assert "Development Status :: 5 - Production/Stable" in content
        assert "Development Status :: 4 - Beta" not in content

    def test_keyword_claude(self):
        """Keywords must include 'claude'."""
        content = self._pyproject()
        assert '"claude"' in content

    def test_keyword_anthropic(self):
        """Keywords must include 'anthropic'."""
        content = self._pyproject()
        assert '"anthropic"' in content

    def test_keyword_multi_agent(self):
        """Keywords must include 'multi-agent'."""
        content = self._pyproject()
        assert '"multi-agent"' in content

    def test_keyword_code_assistant(self):
        """Keywords must include 'code-assistant'."""
        content = self._pyproject()
        assert '"code-assistant"' in content

    def test_keyword_developer_tools(self):
        """Keywords must include 'developer-tools'."""
        content = self._pyproject()
        assert '"developer-tools"' in content

    def test_keyword_code_quality(self):
        """Keywords must include 'code-quality'."""
        content = self._pyproject()
        assert '"code-quality"' in content
