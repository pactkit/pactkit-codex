"""Tests for BUG-019: Venv deployment integration.

AC1: Auto-detect produces CLAUDE.md venv section
AC2: Explicit path override
AC3: No venv when not found
AC4: Warning on missing explicit path
AC5: detect_venv called in deployer
"""
import sys
import warnings
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestAC1AutoDetectProducesVenvSection:
    """AC1: When venv is auto-detected, CLAUDE.md contains venv section."""

    def test_generate_project_claude_md_with_detected_venv(self, tmp_path):
        """Generated CLAUDE.md includes venv section when .venv exists."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        # Create .venv structure
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python3").touch()

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config = get_default_config()
        config['venv'] = {'auto_detect': True}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        claude_md = claude_dir / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "## Virtual Environment" in content
        assert ".venv/bin/python3" in content


class TestAC2ExplicitPathOverride:
    """AC2: Explicit venv.path overrides auto-detect."""

    def test_explicit_path_used_over_autodetect(self, tmp_path):
        """When venv.path is set, it overrides auto-detection."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        # Create both .venv and custom_venv
        (tmp_path / ".venv" / "bin").mkdir(parents=True)
        (tmp_path / ".venv" / "bin" / "python3").touch()
        custom_venv = tmp_path / "custom_venv" / "bin"
        custom_venv.mkdir(parents=True)
        (custom_venv / "python3").touch()

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config = get_default_config()
        config['venv'] = {'auto_detect': True, 'path': 'custom_venv'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        content = (claude_dir / "CLAUDE.md").read_text()
        assert "custom_venv/bin/python3" in content
        assert ".venv/bin" not in content


class TestAC3NoVenvWhenNotFound:
    """AC3: No venv section when no venv directory exists."""

    def test_no_venv_section_when_not_found(self, tmp_path):
        """CLAUDE.md has no venv section when no venv exists."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config = get_default_config()
        config['venv'] = {'auto_detect': True}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        content = (claude_dir / "CLAUDE.md").read_text()
        assert "## Virtual Environment" not in content


class TestAC4WarningOnMissingExplicitPath:
    """AC4: Warning printed when explicit venv.path doesn't exist."""

    def test_warning_on_missing_explicit_venv(self, tmp_path):
        """Warning printed when venv.path doesn't exist."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config = get_default_config()
        config['venv'] = {'path': 'nonexistent_venv'}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                _generate_project_claude_md_if_missing(config)
                # Check warning was issued
                venv_warnings = [x for x in w if 'venv' in str(x.message).lower()]
                assert len(venv_warnings) > 0


class TestAC5DetectVenvCalledInDeployer:
    """AC5: detect_venv is imported and used in deployer."""

    def test_deployer_imports_detect_venv(self):
        """deployer.py imports detect_venv from config."""
        import pactkit.generators.deployer as deployer
        assert hasattr(deployer, 'detect_venv') or 'detect_venv' in dir(deployer)

    def test_detect_venv_function_exists(self):
        """detect_venv function is callable."""
        from pactkit.config import detect_venv
        assert callable(detect_venv)


class TestBackupExistingClaudeMd:
    """STORY-040 supersedes BUG-021: Existing file regenerated, user content migrated."""

    def test_existing_claude_md_not_overwritten(self, tmp_path):
        """STORY-040: Existing user-modified CLAUDE.md is regenerated, content migrated."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        # Create existing user-modified CLAUDE.md
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        original_content = "# My Custom Project\n\nDo not modify."
        claude_md.write_text(original_content)

        # Create venv
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python3").touch()

        config = get_default_config()
        config['venv'] = {'auto_detect': True}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        # STORY-040: CLAUDE.md is regenerated with framework content
        new_content = claude_md.read_text()
        assert 'Virtual Environment' in new_content

        # STORY-040: User content migrated to CLAUDE.local.md
        local_md = claude_dir / "CLAUDE.local.md"
        assert local_md.exists()
        assert "My Custom Project" in local_md.read_text()

        # No .bak backup (migration goes to CLAUDE.local.md)
        backup_file = claude_dir / "CLAUDE.md.bak"
        assert not backup_file.exists()
