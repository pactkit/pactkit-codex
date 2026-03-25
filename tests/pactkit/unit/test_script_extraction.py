"""Tests for STORY-013 R2/R3: script extraction to real files."""

import ast
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


SCRIPTS_DIR = project_root / "src" / "pactkit" / "skills"
SCRIPT_NAMES = ["visualize.py", "board.py", "scaffold.py"]


class TestScriptFilesExist:
    """R2: Script files exist as real Python files."""

    @pytest.mark.parametrize("name", SCRIPT_NAMES)
    def test_script_file_exists(self, name):
        assert (SCRIPTS_DIR / name).is_file(), f"{name} not found in {SCRIPTS_DIR}"

    @pytest.mark.parametrize("name", SCRIPT_NAMES)
    def test_script_is_valid_python(self, name):
        content = (SCRIPTS_DIR / name).read_text(encoding="utf-8")
        ast.parse(content)  # raises SyntaxError if invalid

    @pytest.mark.parametrize("name", SCRIPT_NAMES)
    def test_script_has_body_marker(self, name):
        content = (SCRIPTS_DIR / name).read_text(encoding="utf-8")
        assert "# === SCRIPT BODY ===" in content


class TestLoadScript:
    """R3: load_script prepends _SHARED_HEADER correctly."""

    def test_load_script_returns_string(self):
        from pactkit.skills import load_script

        result = load_script("visualize.py")
        assert isinstance(result, str)
        assert len(result) > 100

    def test_load_script_starts_with_shared_header(self):
        from pactkit.skills import _SHARED_HEADER, load_script

        for name in SCRIPT_NAMES:
            result = load_script(name)
            assert result.startswith(_SHARED_HEADER), f"{name} missing shared header"

    def test_load_script_strips_standalone_header(self):
        from pactkit.skills import _SHARED_HEADER, load_script

        for name in SCRIPT_NAMES:
            result = load_script(name)
            body = result[len(_SHARED_HEADER) :]
            # Body should NOT contain the standalone shebang or docstring
            assert "#!/usr/bin/env python3" not in body
            assert "Standalone version" not in body


class TestPromptsBackwardCompat:
    """R4: prompts.py SOURCE variables still work via load_script."""

    def test_visualize_source_importable(self):
        from pactkit.prompts import VISUALIZE_SOURCE

        assert "def visualize" in VISUALIZE_SOURCE
        assert "def init_architecture" in VISUALIZE_SOURCE

    def test_board_source_importable(self):
        from pactkit.prompts import BOARD_SOURCE

        assert "def add_story" in BOARD_SOURCE

    def test_scaffold_source_importable(self):
        from pactkit.prompts import SCAFFOLD_SOURCE

        assert "def create_spec" in SCAFFOLD_SOURCE

    def test_tools_source_importable(self):
        from pactkit.prompts import TOOLS_SOURCE

        assert "def visualize" in TOOLS_SOURCE
        assert "def add_story" in TOOLS_SOURCE
        assert "def create_spec" in TOOLS_SOURCE


class TestPromptsCleaned:
    """R2 scenario 5: prompts.py no longer contains inline source."""

    def test_no_inline_source_in_prompts(self):
        # After STORY-034, prompts is a package; skills.py holds script loading
        content = (project_root / "src" / "pactkit" / "prompts" / "skills.py").read_text()
        # The file should use load_script, not inline r"""..."""
        assert "load_script(" in content and "visualize.py" in content
        assert "load_script(" in content and "board.py" in content
        assert "load_script(" in content and "scaffold.py" in content
        # Should NOT have the old inline function definitions
        assert "def init_architecture" not in content
        assert "def _scan_files" not in content
