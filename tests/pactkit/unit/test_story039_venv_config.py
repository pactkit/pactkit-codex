"""Tests for STORY-039: Virtual Environment Configuration Support.

AC1: Config Schema Validation
AC2: Auto-Detection
AC3: Project CLAUDE.md Generation (prompt-based, tested via prompt content)
AC4: Fallback When Venv Not Found
AC5: Silent Fallback for Auto-Detect
AC6: Backward Compatibility
"""
import tempfile
import warnings
from pathlib import Path

from pactkit.config import (
    detect_venv,
    generate_default_yaml,
    get_default_config,
    validate_config,
)


class TestAC1ConfigSchemaValidation:
    """AC1: Config with venv.path should be accepted without errors."""

    def test_venv_config_in_default(self):
        """Default config should have venv section."""
        cfg = get_default_config()
        assert 'venv' in cfg
        assert 'auto_detect' in cfg['venv']
        assert cfg['venv']['auto_detect'] is True

    def test_validate_accepts_valid_venv_path(self):
        """validate_config should accept valid venv.path."""
        cfg = get_default_config()
        cfg['venv'] = {'path': '.venv', 'auto_detect': True}
        # Should not raise or warn
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            venv_warnings = [x for x in w if 'venv' in str(x.message).lower()]
            assert venv_warnings == [], f"Unexpected venv warnings: {venv_warnings}"

    def test_validate_warns_on_invalid_venv_path_type(self):
        """validate_config should warn if venv.path is not a string."""
        cfg = get_default_config()
        cfg['venv'] = {'path': 123}  # invalid type
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            venv_warnings = [x for x in w if 'venv' in str(x.message).lower()]
            assert len(venv_warnings) == 1


class TestAC2AutoDetection:
    """AC2: Auto-detection should find .venv when present.

    Note: BUG-021 changed detect_venv to return (name, layout) tuple.
    """

    def test_detect_venv_finds_dotenv(self):
        """detect_venv should find .venv directory and return layout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            venv_dir = project_root / ".venv" / "bin"
            venv_dir.mkdir(parents=True)
            (venv_dir / "python3").touch()

            result = detect_venv(project_root)
            # BUG-021: Now returns tuple (name, layout)
            assert result == (".venv", "unix")

    def test_detect_venv_finds_venv(self):
        """detect_venv should find venv directory and return layout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            venv_dir = project_root / "venv" / "bin"
            venv_dir.mkdir(parents=True)
            (venv_dir / "python3").touch()

            result = detect_venv(project_root)
            # BUG-021: Now returns tuple (name, layout)
            assert result == ("venv", "unix")

    def test_detect_venv_priority_order(self):
        """detect_venv should prefer .venv over venv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create both
            for name in [".venv", "venv"]:
                venv_dir = project_root / name / "bin"
                venv_dir.mkdir(parents=True)
                (venv_dir / "python3").touch()

            result = detect_venv(project_root)
            # BUG-021: Now returns tuple (name, layout)
            assert result == (".venv", "unix")  # .venv takes priority


class TestAC4FallbackWhenNotFound:
    """AC4: When venv.path is set but doesn't exist, warn and fallback."""

    def test_detect_venv_returns_none_when_not_found(self):
        """detect_venv should return None when no venv exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            result = detect_venv(project_root)
            assert result is None


class TestAC5SilentFallbackForAutoDetect:
    """AC5: When auto_detect=true but no venv, silently fallback."""

    def test_detect_venv_returns_none_silently(self):
        """detect_venv should return None without warning when no venv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                result = detect_venv(project_root)
                assert result is None
                # Should not emit any warnings (silent fallback)
                assert len(w) == 0


class TestAC6BackwardCompatibility:
    """AC6: Config without venv section should work unchanged."""

    def test_config_without_venv_works(self):
        """Config without venv should validate without errors."""
        cfg = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': [],
            'commands': [],
            'skills': [],
            'rules': [],
        }
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_config(cfg)
            venv_warnings = [x for x in w if 'venv' in str(x.message).lower()]
            assert venv_warnings == []


class TestGenerateDefaultYaml:
    """Test that generate_default_yaml includes venv section."""

    def test_yaml_contains_venv_section(self):
        """Generated YAML should include venv configuration."""
        yaml_content = generate_default_yaml()
        assert 'venv:' in yaml_content
        assert 'auto_detect:' in yaml_content


class TestProjectInitPromptVenvSection:
    """Test that project-init prompt includes venv section instructions."""

    def test_project_init_has_venv_instructions(self):
        """project-init prompt should mention venv section generation."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        init_prompt = COMMANDS_CONTENT.get('project-init.md', '')
        # Should mention virtual environment
        assert 'venv' in init_prompt.lower() or 'virtual' in init_prompt.lower()
