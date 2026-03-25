"""
STORY-010: Release v1.1.0 — docs sync + version alignment.
(Updated for STORY-011: 14→8 commands, 3→9 skills; STORY-051: 8→11 commands)
"""
from pathlib import Path


def _root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


# ===========================================================================
# Scenario 1: README accuracy
# ===========================================================================

class TestReadmeAccuracy:
    """README must reflect 11 commands and 10 skills."""

    def test_command_count_in_tagline(self):
        readme = (_root() / 'README.md').read_text()
        assert '11 commands' in readme

    def test_command_count_in_quickstart(self):
        readme = (_root() / 'README.md').read_text()
        assert '11 commands' in readme

    def test_no_stale_14_commands(self):
        readme = (_root() / 'README.md').read_text()
        assert '14 commands' not in readme
        assert '14 command' not in readme

    def test_project_status_in_skills_table(self):
        """project-status is now pactkit-status skill, mentioned in README."""
        readme = (_root() / 'README.md').read_text()
        assert 'pactkit-status' in readme or 'Status' in readme

    def test_11_command_playbooks_in_config(self):
        readme = (_root() / 'README.md').read_text()
        assert '11 command playbooks' in readme or '11 command' in readme


# ===========================================================================
# Scenario 2: Version consistency
# ===========================================================================

class TestVersionConsistency:
    """pyproject.toml and __init__.py must agree on version."""

    def test_init_version_matches_pyproject(self):
        import re

        from pactkit import __version__
        content = (_root() / 'pyproject.toml').read_text()
        m = re.search(r'^version\s*=\s*"(.+?)"', content, re.MULTILINE)
        assert m, "version not found in pyproject.toml"
        assert __version__ == m.group(1)

    def test_config_default_version_matches_package(self):
        """BUG-026: config.py default version must match installed __version__."""
        from pactkit import __version__
        from pactkit.config import get_default_config
        cfg = get_default_config()
        assert cfg['version'] == __version__

    def test_cli_version_output(self):
        """CLI version command should reference __version__."""
        import inspect

        from pactkit.cli import main
        source = inspect.getsource(main)
        assert '__version__' in source


# ===========================================================================
# Scenario 3: CLAUDE.md accuracy (STORY-040: layered architecture)
# ===========================================================================

class TestClaudeMdAccuracy:
    """Project .claude/CLAUDE.md (framework) and CLAUDE.local.md (user) content.

    STORY-040 split CLAUDE.md into two files:
    - CLAUDE.md: framework content (venv, dev commands)
    - CLAUDE.local.md: user content (architecture, counts)
    """

    def test_no_stale_846_tests_in_local(self):
        """Stale test count should not appear in CLAUDE.local.md."""
        claude_local = _root() / '.claude' / 'CLAUDE.local.md'
        if claude_local.exists():
            content = claude_local.read_text()
            assert '846 tests' not in content

    def test_no_stale_14_commands_in_local(self):
        """Stale command count should not appear in CLAUDE.local.md."""
        claude_local = _root() / '.claude' / 'CLAUDE.local.md'
        if claude_local.exists():
            content = claude_local.read_text()
            assert '14 command' not in content

    def test_framework_claude_md_has_dev_commands(self):
        """Framework CLAUDE.md should have dev commands section."""
        claude_md = (_root() / '.claude' / 'CLAUDE.md').read_text()
        # STORY-040: framework file has dev commands, not component counts
        assert 'Dev Commands' in claude_md or 'pytest' in claude_md


# ===========================================================================
# Scenario 4: CHANGELOG exists
# ===========================================================================

class TestChangelog:
    """CHANGELOG.md should exist with v1.1.0 entry."""

    def test_changelog_exists(self):
        assert (_root() / 'CHANGELOG.md').is_file()

    def test_has_v110_section(self):
        content = (_root() / 'CHANGELOG.md').read_text()
        assert '1.1.0' in content

    def test_mentions_auto_merge(self):
        content = (_root() / 'CHANGELOG.md').read_text()
        assert 'auto-merge' in content.lower() or 'Auto-Merge' in content

    def test_mentions_project_status(self):
        content = (_root() / 'CHANGELOG.md').read_text()
        assert 'project-status' in content
