"""Tests for STORY-slim-029: Multi-language file discovery via LANG_PROFILES.

AC1: Python project unchanged — pyproject.toml → scans *.py files.
AC2: Go project discovers .go files — go.mod → scans *.go files.
AC3: Java project discovers .java files — pom.xml → scans *.java files.
AC4: Unknown stack falls back to *.py.
AC5: Full tree scanned, not restricted to source_dirs.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

SKILLS_PATH = str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills")


def _add_skills_path():
    if SKILLS_PATH not in sys.path:
        sys.path.insert(0, SKILLS_PATH)


# ===========================================================================
# Test 1: _detect_file_ext — Python project (pyproject.toml)
# ===========================================================================


class TestDetectFileExtPython:
    """AC1: pyproject.toml marker → returns '.py'."""

    def test_detect_file_ext_python(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'foo'\n")

        result = _detect_file_ext(tmp_path)
        assert result == ".py", f"Expected '.py', got: {result!r}"


# ===========================================================================
# Test 2: _detect_file_ext — Go project (go.mod)
# ===========================================================================


class TestDetectFileExtGo:
    """AC2: go.mod marker → returns '.go'."""

    def test_detect_file_ext_go(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        (tmp_path / "go.mod").write_text("module example.com/myapp\n\ngo 1.21\n")

        result = _detect_file_ext(tmp_path)
        assert result == ".go", f"Expected '.go', got: {result!r}"


# ===========================================================================
# Test 3: _detect_file_ext — Java project (pom.xml)
# ===========================================================================


class TestDetectFileExtJava:
    """AC3: pom.xml marker → returns '.java'."""

    def test_detect_file_ext_java(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        (tmp_path / "pom.xml").write_text(
            "<project><modelVersion>4.0.0</modelVersion></project>\n"
        )

        result = _detect_file_ext(tmp_path)
        assert result == ".java", f"Expected '.java', got: {result!r}"


# ===========================================================================
# Test 4: _detect_file_ext — Node project (package.json)
# ===========================================================================


class TestDetectFileExtNode:
    """Node project: package.json marker → returns '.ts'."""

    def test_detect_file_ext_node(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        (tmp_path / "package.json").write_text('{"name": "myapp", "version": "1.0.0"}\n')

        result = _detect_file_ext(tmp_path)
        assert result == ".ts", f"Expected '.ts', got: {result!r}"


# ===========================================================================
# Test 5: _detect_file_ext — unknown stack falls back to .py
# ===========================================================================


class TestDetectFileExtUnknownFallback:
    """AC4: No marker files → falls back to '.py'."""

    def test_detect_file_ext_unknown_fallback(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        # Empty directory — no marker files at all
        result = _detect_file_ext(tmp_path)
        assert result == ".py", f"Expected '.py' fallback, got: {result!r}"


# ===========================================================================
# Test 6: _detect_file_ext — pactkit.yaml stack override
# ===========================================================================


class TestDetectFileExtYamlStackOverride:
    """pactkit.yaml with stack: go → returns '.go' regardless of marker files."""

    def test_detect_file_ext_yaml_stack_override(self, tmp_path):
        _add_skills_path()
        from visualize import _detect_file_ext

        # No go.mod marker — but yaml says stack: go
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(
            textwrap.dedent("""\
                version: "2.3.7"
                stack: go
                visualize:
                  scan_excludes:
                    - vendor
            """)
        )

        result = _detect_file_ext(tmp_path)
        assert result == ".go", f"Expected '.go' from yaml stack override, got: {result!r}"

    def test_detect_file_ext_yaml_stack_auto_falls_through_to_marker(self, tmp_path):
        """stack: auto in yaml → falls through to marker-file detection."""
        _add_skills_path()
        from visualize import _detect_file_ext

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(
            textwrap.dedent("""\
                version: "2.3.7"
                stack: auto
            """)
        )

        # go.mod present → should detect go
        (tmp_path / "go.mod").write_text("module example.com/foo\n\ngo 1.21\n")

        result = _detect_file_ext(tmp_path)
        assert result == ".go", f"Expected '.go' from marker detection, got: {result!r}"


# ===========================================================================
# Test 7: _scan_files uses file_ext param
# ===========================================================================


class TestScanFilesUsesFileExt:
    """_scan_files(root, file_ext='.go') picks up *.go files, not *.py files."""

    def test_scan_files_uses_file_ext(self, tmp_path):
        _add_skills_path()
        from visualize import _scan_files

        # Create a .go file
        (tmp_path / "main.go").write_text("package main\n\nfunc main() {}\n")

        # Create a .py file that should NOT be included
        (tmp_path / "ignored.py").write_text("x = 1\n")

        all_files, _, _ = _scan_files(tmp_path, file_ext=".go")
        found_names = [f.name for f in all_files]

        assert "main.go" in found_names, "main.go must be found when file_ext='.go'"
        assert "ignored.py" not in found_names, "ignored.py must NOT appear when file_ext='.go'"

    def test_scan_files_uses_java_ext(self, tmp_path):
        """file_ext='.java' discovers .java files."""
        _add_skills_path()
        from visualize import _scan_files

        src_dir = tmp_path / "src" / "main" / "java"
        src_dir.mkdir(parents=True)
        (src_dir / "App.java").write_text("public class App {}\n")
        (tmp_path / "build.gradle").write_text("plugins { id 'java' }\n")

        all_files, _, _ = _scan_files(tmp_path, file_ext=".java")
        found_names = [f.name for f in all_files]

        assert "App.java" in found_names, "App.java must be found when file_ext='.java'"


# ===========================================================================
# Test 8: _scan_files default still scans *.py (backward compatibility)
# ===========================================================================


class TestScanFilesDefaultPy:
    """_scan_files(root) with no file_ext arg defaults to *.py — backward compat."""

    def test_scan_files_default_py(self, tmp_path):
        _add_skills_path()
        from visualize import _scan_files

        (tmp_path / "module.py").write_text("def foo(): pass\n")
        (tmp_path / "main.go").write_text("package main\n")

        all_files, _, _ = _scan_files(tmp_path)
        found_names = [f.name for f in all_files]

        assert "module.py" in found_names, "module.py must be found with default (*.py)"
        assert "main.go" not in found_names, "main.go must NOT appear with default *.py"

    def test_scan_files_default_py_explicit(self, tmp_path):
        """Explicit file_ext='.py' behaves same as default."""
        _add_skills_path()
        from visualize import _scan_files

        (tmp_path / "util.py").write_text("def bar(): pass\n")

        all_files_default, _, _ = _scan_files(tmp_path)
        all_files_explicit, _, _ = _scan_files(tmp_path, file_ext=".py")

        assert [f.name for f in all_files_default] == [f.name for f in all_files_explicit]


# ===========================================================================
# Test 9: Full tree scanned (AC5) — not restricted to source_dirs
# ===========================================================================


class TestFullTreeScanned:
    """AC5: Files in both cmd/ and internal/ appear in the scan."""

    def test_scan_files_go_project_full_tree(self, tmp_path):
        """Go project: both cmd/ and internal/ .go files are discovered."""
        _add_skills_path()
        from visualize import _scan_files

        (tmp_path / "go.mod").write_text("module example.com/app\n\ngo 1.21\n")

        cmd_dir = tmp_path / "cmd"
        cmd_dir.mkdir()
        (cmd_dir / "main.go").write_text("package main\nfunc main() {}\n")

        internal_dir = tmp_path / "internal" / "server"
        internal_dir.mkdir(parents=True)
        (internal_dir / "server.go").write_text("package server\ntype Server struct{}\n")

        all_files, _, _ = _scan_files(tmp_path, file_ext=".go")
        found_names = [f.name for f in all_files]

        assert "main.go" in found_names, "cmd/main.go must be found"
        assert "server.go" in found_names, "internal/server/server.go must be found"
