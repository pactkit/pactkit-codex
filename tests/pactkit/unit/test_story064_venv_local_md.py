"""Tests for STORY-064: Persist Venv Config in CLAUDE.local.md Managed Block."""
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

MANAGED_START = "<!-- pactkit:venv:start -->"
MANAGED_END = "<!-- pactkit:venv:end -->"


def _make_project(tmp_path, venv_name=".venv", *, create_venv=True):
    """Set up a minimal project directory with optional venv."""
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    if create_venv:
        venv_bin = tmp_path / venv_name / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python3").touch()
    return claude_dir


def _run_generate(tmp_path, config_override=None):
    from pactkit.config import get_default_config
    from pactkit.generators.deployer import _generate_project_claude_md

    config = get_default_config()
    config['venv'] = {'auto_detect': True}
    if config_override:
        config.update(config_override)

    with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        _generate_project_claude_md(config)


# ---------------------------------------------------------------------------
# AC1: Managed block written on first init with venv
# ---------------------------------------------------------------------------

class TestAC1ManagedBlockWrittenOnInit:
    def test_managed_block_present_after_init(self, tmp_path):
        """When venv is detected, CLAUDE.local.md gets a managed block."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        assert local_md.exists()
        content = local_md.read_text()
        assert MANAGED_START in content
        assert MANAGED_END in content

    def test_managed_block_has_correct_venv_paths(self, tmp_path):
        """Managed block contains the correct activate / python / pytest / pip paths."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        content = (tmp_path / ".claude" / "CLAUDE.local.md").read_text()
        assert ".venv/bin/python3" in content
        assert ".venv/bin/activate" in content
        assert ".venv/bin/pytest" in content
        assert ".venv/bin/pip" in content

    def test_managed_block_at_top_of_file(self, tmp_path):
        """Managed block is placed before user content."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        content = (tmp_path / ".claude" / "CLAUDE.local.md").read_text()
        start_idx = content.index(MANAGED_START)
        end_idx = content.index(MANAGED_END)
        assert start_idx < end_idx


# ---------------------------------------------------------------------------
# AC2: Block persists when venv detection fails on update
# ---------------------------------------------------------------------------

class TestAC2BlockPersistedOnDetectionFailure:
    def test_block_preserved_when_venv_removed(self, tmp_path):
        """After venv is removed, re-running deploy keeps the managed block."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        # Confirm block was written
        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        original = local_md.read_text()
        assert MANAGED_START in original

        # Now remove venv and re-run (detection will fail)
        import shutil
        shutil.rmtree(tmp_path / ".venv")
        _run_generate(tmp_path)

        updated = local_md.read_text()
        assert MANAGED_START in updated
        assert ".venv/bin/python3" in updated

    def test_block_content_unchanged_when_venv_removed(self, tmp_path):
        """Block content stays the same when detection fails."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        first_content = local_md.read_text()

        import shutil
        shutil.rmtree(tmp_path / ".venv")
        _run_generate(tmp_path)

        second_content = local_md.read_text()
        assert first_content == second_content


# ---------------------------------------------------------------------------
# AC3: Block updated when venv path changes
# ---------------------------------------------------------------------------

class TestAC3BlockUpdatedOnPathChange:
    def test_block_updated_when_venv_path_changes(self, tmp_path):
        """When a different venv is detected, the managed block is updated."""
        _make_project(tmp_path, ".venv")
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        assert ".venv/bin/python3" in local_md.read_text()

        # Create a second venv and point config to it
        new_venv_bin = tmp_path / "custom_venv" / "bin"
        new_venv_bin.mkdir(parents=True)
        (new_venv_bin / "python3").touch()

        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md
        config = get_default_config()
        config['venv'] = {'path': 'custom_venv'}
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md(config)

        updated = local_md.read_text()
        assert "custom_venv/bin/python3" in updated

    def test_old_venv_path_not_in_block_after_update(self, tmp_path):
        """Old venv path is replaced, not appended."""
        _make_project(tmp_path, ".venv")
        _run_generate(tmp_path)

        new_venv_bin = tmp_path / "custom_venv" / "bin"
        new_venv_bin.mkdir(parents=True)
        (new_venv_bin / "python3").touch()

        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md
        config = get_default_config()
        config['venv'] = {'path': 'custom_venv'}
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md(config)

        content = (tmp_path / ".claude" / "CLAUDE.local.md").read_text()
        # Old path no longer in the managed block region
        start = content.index(MANAGED_START)
        end = content.index(MANAGED_END)
        block = content[start:end]
        assert ".venv/bin" not in block


# ---------------------------------------------------------------------------
# AC4: User customizations outside markers preserved
# ---------------------------------------------------------------------------

class TestAC4UserContentPreserved:
    def test_user_content_below_markers_preserved_on_update(self, tmp_path):
        """User text after the end marker is untouched after update."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        # Append user customization
        local_md.write_text(local_md.read_text() + "\n## My Custom Section\nHello world\n")

        # Re-run with a new venv
        new_venv_bin = tmp_path / "new_venv" / "bin"
        new_venv_bin.mkdir(parents=True)
        (new_venv_bin / "python3").touch()

        from pactkit.config import get_default_config
        from pactkit.generators.deployer import _generate_project_claude_md
        config = get_default_config()
        config['venv'] = {'path': 'new_venv'}
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            _generate_project_claude_md(config)

        updated = local_md.read_text()
        assert "## My Custom Section" in updated
        assert "Hello world" in updated

    def test_user_content_before_markers_preserved(self, tmp_path):
        """If user adds content before the managed block, it is not deleted."""
        _make_project(tmp_path)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        # Prepend user content BEFORE the managed block (unusual but possible)
        original = local_md.read_text()
        local_md.write_text("# User Preamble\n\n" + original)

        # Re-run (same venv)
        _run_generate(tmp_path)

        updated = local_md.read_text()
        assert "# User Preamble" in updated


# ---------------------------------------------------------------------------
# AC5: No managed block written when no venv
# ---------------------------------------------------------------------------

class TestAC5NoBlockWhenNoVenv:
    def test_no_managed_block_when_no_venv(self, tmp_path):
        """When venv is absent, CLAUDE.local.md has no managed block."""
        _make_project(tmp_path, create_venv=False)
        _run_generate(tmp_path)

        local_md = tmp_path / ".claude" / "CLAUDE.local.md"
        content = local_md.read_text()
        assert MANAGED_START not in content
        assert MANAGED_END not in content
