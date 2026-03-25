"""Tests for BUG-020: CLAUDE.md backup and regenerate strategy.

NOTE: STORY-040 superseded BUG-021's skip-if-exists behavior.
Per STORY-040, CLAUDE.md is always regenerated, user content migrates to CLAUDE.local.md.
These tests are updated to reflect the new layered architecture behavior.

AC1: Existing file regenerated (user content migrated per STORY-040)
AC2: Fresh project generates file
AC3: N/A (backup to .bak removed, migration goes to CLAUDE.local.md)
AC4: N/A (no .bak notification, content preserved in CLAUDE.local.md)
"""
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestAC1ExistingFileBackedUp:
    """AC1: Existing CLAUDE.md regenerated, user content migrated (STORY-040 supersedes BUG-021)."""

    def test_backup_created_when_file_exists(self, tmp_path):
        """STORY-040: Existing user-modified file is regenerated, content migrated to CLAUDE.local.md."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        # Create existing user-modified CLAUDE.md
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        original_content = "# My Custom Project\n\nDo not lose this."
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
        assert 'Virtual Environment' in new_content  # Framework content
        # STORY-040: User content migrated to CLAUDE.local.md
        local_md = claude_dir / "CLAUDE.local.md"
        assert local_md.exists()
        assert "My Custom Project" in local_md.read_text()
        # No .bak backup (migration goes to CLAUDE.local.md)
        backup_file = claude_dir / "CLAUDE.md.bak"
        assert not backup_file.exists()

    def test_new_claude_md_has_venv_section(self, tmp_path):
        """STORY-040: Regenerated CLAUDE.md includes venv section when venv exists."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        # Create existing CLAUDE.md (user-modified)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        original_content = "# Old content"
        claude_md.write_text(original_content)

        # Create venv
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python3").touch()

        config = get_default_config()
        config['venv'] = {'auto_detect': True}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        # STORY-040: File is regenerated with venv section
        new_content = claude_md.read_text()
        assert 'Virtual Environment' in new_content
        assert '.venv/bin/activate' in new_content


class TestAC2FreshProjectUnchanged:
    """AC2: Fresh project (no existing CLAUDE.md) works as before."""

    def test_no_backup_when_no_existing_file(self, tmp_path):
        """No backup file created when CLAUDE.md doesn't exist."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create venv
        venv_dir = tmp_path / ".venv" / "bin"
        venv_dir.mkdir(parents=True)
        (venv_dir / "python3").touch()

        config = get_default_config()
        config['venv'] = {'auto_detect': True}

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        # Verify no backup exists
        backup_file = claude_dir / "CLAUDE.md.bak"
        assert not backup_file.exists(), "No backup should be created for fresh project"

        # But CLAUDE.md should exist
        claude_md = claude_dir / "CLAUDE.md"
        assert claude_md.exists()


class TestAC3BackupOverwritesPrevious:
    """AC3: N/A - .bak backup removed, migration goes to CLAUDE.local.md (STORY-040)."""

    def test_previous_backup_untouched(self, tmp_path):
        """STORY-040: Old .bak files are not touched, migration goes to CLAUDE.local.md."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        # Create existing user-modified CLAUDE.md
        claude_md = claude_dir / "CLAUDE.md"
        current_content = "# Current content"
        claude_md.write_text(current_content)

        # Create old backup (should remain untouched - we don't delete user files)
        backup_file = claude_dir / "CLAUDE.md.bak"
        old_backup_content = "# Old backup - should remain"
        backup_file.write_text(old_backup_content)

        config = get_default_config()

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        # STORY-040: CLAUDE.md regenerated, old backup untouched
        new_content = claude_md.read_text()
        assert 'Dev Commands' in new_content  # Framework content
        assert backup_file.read_text() == old_backup_content  # Untouched
        # User content migrated to CLAUDE.local.md
        local_md = claude_dir / "CLAUDE.local.md"
        assert local_md.exists()
        assert "Current content" in local_md.read_text()


class TestAC4NotificationPrinted:
    """AC4: N/A - No .bak notification, content preserved in CLAUDE.local.md (STORY-040)."""

    def test_backup_notification_printed(self, tmp_path, capsys):
        """STORY-040: No .bak backup notification, content migrated to CLAUDE.local.md."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        original_content = "# Existing content"
        claude_md.write_text(original_content)

        config = get_default_config()

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        captured = capsys.readouterr()
        # STORY-040: No .bak backup notification
        assert "Backed up CLAUDE.md" not in captured.out
        # STORY-040: CLAUDE.md is regenerated
        new_content = claude_md.read_text()
        assert 'Dev Commands' in new_content  # Framework content
        # User content migrated to CLAUDE.local.md
        local_md = claude_dir / "CLAUDE.local.md"
        assert "Existing content" in local_md.read_text()

    def test_no_notification_when_no_backup_needed(self, tmp_path, capsys):
        """No backup notification when file doesn't exist."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md_if_missing

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        config = get_default_config()

        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md_if_missing(config)

        captured = capsys.readouterr()
        assert "Backed up" not in captured.out
