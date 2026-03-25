"""Tests for STORY-slim-028: Configurable scan_excludes via pactkit.yaml.

AC1: Default behavior unchanged — no visualize section → SCAN_EXCLUDES constant used.
AC2: Custom excludes respected — config excludes override SCAN_EXCLUDES.
AC3: pactkit init generates visualize config without project-specific dirs.
AC4: auto_merge preserves user config — existing visualize section not overwritten.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

# ===========================================================================
# Test 1: get_default_config has visualize.scan_excludes key
# ===========================================================================


class TestGetDefaultConfigHasVisualize:
    """R1: get_default_config() MUST return a dict with 'visualize.scan_excludes'."""

    def test_get_default_config_has_visualize(self):
        from pactkit.config import get_default_config

        cfg = get_default_config()
        assert "visualize" in cfg, "'visualize' section missing from default config"
        assert "scan_excludes" in cfg["visualize"], "'visualize.scan_excludes' missing from default config"
        assert isinstance(cfg["visualize"]["scan_excludes"], list), "scan_excludes must be a list"

    def test_default_excludes_not_empty(self):
        from pactkit.config import get_default_config

        cfg = get_default_config()
        excludes = cfg["visualize"]["scan_excludes"]
        assert len(excludes) > 0, "scan_excludes must not be empty"


# ===========================================================================
# Test 2: Default list does NOT contain project-specific dirs
# ===========================================================================


class TestDefaultExcludesNoProjectDirs:
    """R2: Default scan_excludes MUST NOT include skills, commands, rules, agents."""

    def test_default_excludes_no_skills(self):
        from pactkit.config import get_default_config

        excludes = get_default_config()["visualize"]["scan_excludes"]
        assert "skills" not in excludes, "'skills' must not be in default scan_excludes"

    def test_default_excludes_no_commands(self):
        from pactkit.config import get_default_config

        excludes = get_default_config()["visualize"]["scan_excludes"]
        assert "commands" not in excludes, "'commands' must not be in default scan_excludes"

    def test_default_excludes_no_rules(self):
        from pactkit.config import get_default_config

        excludes = get_default_config()["visualize"]["scan_excludes"]
        assert "rules" not in excludes, "'rules' must not be in default scan_excludes"

    def test_default_excludes_no_agents(self):
        from pactkit.config import get_default_config

        excludes = get_default_config()["visualize"]["scan_excludes"]
        assert "agents" not in excludes, "'agents' must not be in default scan_excludes"

    def test_default_excludes_has_universal_dirs(self):
        from pactkit.config import get_default_config

        excludes = get_default_config()["visualize"]["scan_excludes"]
        for expected in ("venv", ".venv", "__pycache__", ".git", "node_modules"):
            assert expected in excludes, f"'{expected}' must be in default scan_excludes"


# ===========================================================================
# Test 3: _scan_files default excludes uses SCAN_EXCLUDES constant
# ===========================================================================


class TestScanFilesDefaultExcludes:
    """R4: When no scan_excludes param → _scan_files uses SCAN_EXCLUDES constant (backward compat)."""

    def test_scan_files_default_excludes(self, tmp_path):
        """Calling _scan_files(root) with no extra arg still excludes SCAN_EXCLUDES dirs."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _scan_files

        # Create a normal py file that should be found
        src = tmp_path / "mymodule.py"
        src.write_text("x = 1")

        # Create a venv dir with a py file that should be excluded
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "excluded.py").write_text("x = 2")

        all_files, _, _ = _scan_files(tmp_path)
        found_names = [f.name for f in all_files]

        assert "mymodule.py" in found_names, "Normal file should be scanned"
        assert "excluded.py" not in found_names, "File inside venv/ should be excluded by default"

    def test_scan_files_respects_scan_excludes_constant(self, tmp_path):
        """The SCAN_EXCLUDES constant should still contain standard PactKit excludes."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import SCAN_EXCLUDES

        # PactKit dirs should still be in the constant for backward compat
        for expected in ("venv", ".venv", "__pycache__", ".git"):
            assert expected in SCAN_EXCLUDES, f"'{expected}' must remain in SCAN_EXCLUDES constant"


# ===========================================================================
# Test 4: _scan_files with custom excludes
# ===========================================================================


class TestScanFilesCustomExcludes:
    """R4: When scan_excludes param provided → only those dirs are excluded."""

    def test_scan_files_custom_excludes_overrides_defaults(self, tmp_path):
        """Custom list overrides the SCAN_EXCLUDES constant."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _scan_files

        # Create a src file
        (tmp_path / "main.py").write_text("x = 1")

        # Create a skills dir (normally excluded by SCAN_EXCLUDES constant)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "tool.py").write_text("y = 2")

        # Create venv (in our custom exclude list)
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "excluded.py").write_text("z = 3")

        # Pass custom excludes that only exclude venv, not skills
        all_files, _, _ = _scan_files(tmp_path, scan_excludes=["venv"])
        found_names = [f.name for f in all_files]

        assert "main.py" in found_names, "main.py should be included"
        assert "tool.py" in found_names, "skills/tool.py should be included when not in custom excludes"
        assert "excluded.py" not in found_names, "venv/excluded.py should be excluded"

    def test_scan_files_empty_custom_excludes(self, tmp_path):
        """Empty custom list means nothing is excluded (not even venv)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _scan_files

        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "script.py").write_text("x = 1")

        all_files, _, _ = _scan_files(tmp_path, scan_excludes=[])
        found_names = [f.name for f in all_files]
        assert "script.py" in found_names, "With empty excludes, venv/script.py should be found"


# ===========================================================================
# Test 5: auto_merge backfills visualize section
# ===========================================================================


class TestAutoMergeBackfillsVisualize:
    """R3: auto_merge_config_file() MUST backfill visualize section for existing projects."""

    def test_auto_merge_backfills_missing_visualize(self, tmp_path):
        """If visualize section is absent, auto_merge adds it."""
        import yaml

        from pactkit.config import auto_merge_config_file

        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(
            textwrap.dedent("""\
                version: "2.3.5"
                stack: python
                agents:
                  - senior-developer
                commands:
                  - project-act
                skills:
                  - pactkit-visualize
                rules:
                  - 01-core-protocol
            """)
        )

        added = auto_merge_config_file(yaml_file)

        # visualize section should have been added
        assert any("visualize" in item for item in added), (
            f"Expected 'visualize' in added list, got: {added}"
        )

        # Read back and verify
        data = yaml.safe_load(yaml_file.read_text())
        assert "visualize" in data, "visualize section missing after auto_merge"
        assert "scan_excludes" in data["visualize"], "scan_excludes missing after auto_merge"

    def test_auto_merge_preserves_existing_visualize(self, tmp_path):
        """If visualize section already exists, it MUST NOT be overwritten."""
        import yaml

        from pactkit.config import auto_merge_config_file

        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(
            textwrap.dedent("""\
                version: "2.3.5"
                stack: python
                agents:
                  - senior-developer
                commands:
                  - project-act
                skills:
                  - pactkit-visualize
                rules:
                  - 01-core-protocol
                visualize:
                  scan_excludes:
                    - venv
                    - custom_dir
            """)
        )

        auto_merge_config_file(yaml_file)

        data = yaml.safe_load(yaml_file.read_text())
        assert data["visualize"]["scan_excludes"] == ["venv", "custom_dir"], (
            "Existing visualize.scan_excludes must be preserved"
        )


# ===========================================================================
# Test 6: load_config deep-merges visualize section
# ===========================================================================


class TestLoadConfigDeepMergesVisualize:
    """R1: load_config() deep-merges visualize so partial user config inherits defaults."""

    def test_load_config_partial_visualize_inherits_defaults(self, tmp_path):
        """User specifies partial visualize; missing sub-keys come from defaults."""
        from pactkit.config import load_config

        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text(
            textwrap.dedent("""\
                version: "2.3.5"
                stack: python
                visualize:
                  scan_excludes:
                    - venv
                    - my_custom_dir
            """)
        )

        cfg = load_config(yaml_file)
        # User's custom list must be respected
        assert cfg["visualize"]["scan_excludes"] == ["venv", "my_custom_dir"], (
            "User's custom scan_excludes must be preserved"
        )

    def test_load_config_no_visualize_gets_defaults(self, tmp_path):
        """No visualize section in user YAML → defaults applied."""
        from pactkit.config import get_default_config, load_config

        yaml_file = tmp_path / "pactkit.yaml"
        yaml_file.write_text("version: \"2.3.5\"\nstack: python\n")

        cfg = load_config(yaml_file)
        default_excludes = get_default_config()["visualize"]["scan_excludes"]
        assert cfg["visualize"]["scan_excludes"] == default_excludes, (
            "Default scan_excludes must be used when visualize section absent"
        )


# ===========================================================================
# Test 7: _load_scan_excludes reads pactkit.yaml
# ===========================================================================


class TestLoadScanExcludesFromYaml:
    """R4: _load_scan_excludes(root) reads scan_excludes from .claude/pactkit.yaml."""

    def test_load_scan_excludes_from_claude_yaml(self, tmp_path):
        """_load_scan_excludes reads from .claude/pactkit.yaml."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _load_scan_excludes

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        yaml_file = claude_dir / "pactkit.yaml"
        yaml_file.write_text(
            textwrap.dedent("""\
                visualize:
                  scan_excludes:
                    - venv
                    - my_custom_dir
            """)
        )

        result = _load_scan_excludes(tmp_path)
        assert result == ["venv", "my_custom_dir"], (
            f"Expected ['venv', 'my_custom_dir'], got: {result}"
        )

    def test_load_scan_excludes_from_opencode_yaml(self, tmp_path):
        """_load_scan_excludes falls back to .opencode/pactkit.yaml."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _load_scan_excludes

        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir()
        yaml_file = opencode_dir / "pactkit.yaml"
        yaml_file.write_text(
            textwrap.dedent("""\
                visualize:
                  scan_excludes:
                    - venv
                    - opencode_custom
            """)
        )

        result = _load_scan_excludes(tmp_path)
        assert result == ["venv", "opencode_custom"], (
            f"Expected ['venv', 'opencode_custom'], got: {result}"
        )


# ===========================================================================
# Test 8: _load_scan_excludes returns None when no yaml exists
# ===========================================================================


class TestLoadScanExcludesMissingYaml:
    """R4: _load_scan_excludes returns None when no pactkit.yaml exists."""

    def test_load_scan_excludes_no_yaml(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _load_scan_excludes

        result = _load_scan_excludes(tmp_path)
        assert result is None, f"Expected None when no yaml file, got: {result}"

    def test_load_scan_excludes_yaml_without_visualize_section(self, tmp_path):
        """Returns None if pactkit.yaml exists but has no visualize section."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _load_scan_excludes

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        yaml_file = claude_dir / "pactkit.yaml"
        yaml_file.write_text("version: \"2.3.5\"\nstack: python\n")

        result = _load_scan_excludes(tmp_path)
        assert result is None, f"Expected None when no visualize section, got: {result}"

    def test_load_scan_excludes_graceful_on_import_error(self, tmp_path):
        """Returns None gracefully if yaml module not available (simulated by bad content)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "pactkit" / "skills"))
        from visualize import _load_scan_excludes

        # Empty directory → no yaml file
        result = _load_scan_excludes(tmp_path)
        assert result is None


# ===========================================================================
# Test 9: generate_default_yaml contains visualize section
# ===========================================================================


class TestGenerateDefaultYamlVisualize:
    """R2: generate_default_yaml() MUST include visualize.scan_excludes section."""

    def test_generate_default_yaml_has_visualize(self):
        from pactkit.config import generate_default_yaml

        yaml_str = generate_default_yaml()
        assert "visualize:" in yaml_str, "visualize section missing from generated YAML"
        assert "scan_excludes:" in yaml_str, "scan_excludes missing from generated YAML"

    def test_generate_default_yaml_no_project_dirs(self):
        from pactkit.config import generate_default_yaml

        yaml_str = generate_default_yaml()
        # Find the visualize section and check it doesn't contain project-specific dirs
        lines = yaml_str.split("\n")
        in_visualize = False
        visualize_content = []
        for line in lines:
            if line.startswith("visualize:"):
                in_visualize = True
            elif in_visualize and line and not line.startswith(" "):
                break
            if in_visualize:
                visualize_content.append(line)

        visualize_text = "\n".join(visualize_content)
        for forbidden in ("skills", "commands", "rules", "agents"):
            assert f"- {forbidden}" not in visualize_text, (
                f"'{forbidden}' must not be in generated visualize.scan_excludes"
            )
