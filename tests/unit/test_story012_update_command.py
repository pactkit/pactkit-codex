"""Tests for STORY-012: Incremental Update Command (`pactkit-codex update`)."""

from unittest.mock import patch

import pytest

from pactkit_codex import __version__


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    root = tmp_path / ".codex"
    root.mkdir(parents=True)
    return root


class TestAC1VersionFileCreatedOnInit:
    """AC1: Version file created on init."""

    def test_version_marker_written(self, codex_root):
        from pactkit_codex.generators.deployer import _deploy_codex

        _deploy_codex(target=codex_root)

        version_file = codex_root / ".pactkit-version"
        assert version_file.exists()
        assert version_file.read_text().strip() == __version__

    def test_version_marker_updated_on_redeploy(self, codex_root):
        from pactkit_codex.generators.deployer import _deploy_codex, _write_version_marker

        # Simulate old version
        _write_version_marker(codex_root, "0.0.1")
        assert (codex_root / ".pactkit-version").read_text().strip() == "0.0.1"

        # Redeploy updates version
        _deploy_codex(target=codex_root)
        assert (codex_root / ".pactkit-version").read_text().strip() == __version__


class TestAC2UpdateSkipsIfCurrent:
    """AC2: Update skips if current."""

    def test_update_skips_when_current(self, codex_root, capsys):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        _write_version_marker(codex_root, __version__)

        result = update(target=codex_root, force=False, if_needed=False, dry_run=False)

        assert result["action"] == "skip"
        captured = capsys.readouterr()
        assert "Already up to date" in captured.out


class TestAC3UpdateRegeneratesManagedFiles:
    """AC3: Update regenerates managed files."""

    def test_update_regenerates_when_outdated(self, codex_root):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        # Simulate old version deployed
        _write_version_marker(codex_root, "0.0.1")

        result = update(target=codex_root, force=False, if_needed=False, dry_run=False)

        assert result["action"] == "updated"
        # Version marker should be updated
        version_file = codex_root / ".pactkit-version"
        assert version_file.read_text().strip() == __version__
        # Managed files should exist
        assert (codex_root / "AGENTS.md").exists()
        assert (codex_root / "rules").is_dir()


class TestAC4UpdatePreservesUserFiles:
    """AC4: Update preserves user files."""

    def test_config_toml_not_overwritten(self, codex_root):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        # Create user config
        config_toml = codex_root / "config.toml"
        config_toml.write_text('model = "gpt-4o"\nmy_custom_key = "preserved"\n')
        _write_version_marker(codex_root, "0.0.1")

        update(target=codex_root, force=False, if_needed=False, dry_run=False)

        # User config preserved
        content = config_toml.read_text()
        assert "my_custom_key" in content

    def test_agents_local_md_not_overwritten(self, tmp_path):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        codex_root = tmp_path / ".codex"
        codex_root.mkdir(parents=True)
        project_root = tmp_path

        # Create user local file
        local_md = project_root / ".codex" / "AGENTS.local.md"
        local_md.parent.mkdir(parents=True, exist_ok=True)
        local_md.write_text("# My custom instructions\n")

        _write_version_marker(codex_root, "0.0.1")

        with patch("pactkit_codex.generators.deployer.Path.cwd", return_value=project_root):
            update(target=codex_root, force=False, if_needed=False, dry_run=False)

        # User local file preserved
        assert local_md.read_text() == "# My custom instructions\n"


class TestAC5ForceBypassesVersionCheck:
    """AC5: --force bypasses version check."""

    def test_force_regenerates_even_when_current(self, codex_root):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        _write_version_marker(codex_root, __version__)

        result = update(target=codex_root, force=True, if_needed=False, dry_run=False)

        assert result["action"] == "updated"


class TestAC6IfNeededSilentWhenCurrent:
    """AC6: --if-needed is silent when current."""

    def test_if_needed_no_output_when_current(self, codex_root, capsys):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        _write_version_marker(codex_root, __version__)
        capsys.readouterr()  # Clear output from setup

        result = update(target=codex_root, force=False, if_needed=True, dry_run=False)

        assert result["action"] == "skip"
        captured = capsys.readouterr()
        assert captured.out == ""  # Silent


class TestAC7DryRunShowsPlanWithoutChanges:
    """AC7: --dry-run shows plan without changes."""

    def test_dry_run_lists_files(self, codex_root, capsys):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        _write_version_marker(codex_root, "0.0.1")

        result = update(target=codex_root, force=False, if_needed=False, dry_run=True)

        assert result["action"] == "dry_run"
        captured = capsys.readouterr()
        assert "Would update" in captured.out
        assert "AGENTS.md" in captured.out

    def test_dry_run_no_file_changes(self, codex_root):
        from pactkit_codex.generators.deployer import _write_version_marker, update

        _write_version_marker(codex_root, "0.0.1")
        # No AGENTS.md yet
        assert not (codex_root / "AGENTS.md").exists()

        update(target=codex_root, force=False, if_needed=False, dry_run=True)

        # Still no AGENTS.md (dry run didn't create it)
        assert not (codex_root / "AGENTS.md").exists()


class TestVersionHelpers:
    """Test version marker helper functions."""

    def test_read_deployed_version_returns_none_if_missing(self, codex_root):
        from pactkit_codex.generators.deployer import _read_deployed_version

        assert _read_deployed_version(codex_root) is None

    def test_read_deployed_version_returns_version(self, codex_root):
        from pactkit_codex.generators.deployer import (
            _read_deployed_version,
            _write_version_marker,
        )

        _write_version_marker(codex_root, "1.2.3")
        assert _read_deployed_version(codex_root) == "1.2.3"
