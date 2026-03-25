"""Tests for STORY-033: Config auto-backfill for missing sections on update.

AC1: Missing non-list sections are backfilled
AC2: Existing user values are not overwritten
AC3: _rewrite_yaml writes all sections
AC4: Backfill reports added sections
AC5: Fresh init still generates complete config
"""
import sys
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pactkit.config import (  # noqa: E402
    auto_merge_config_file,
    generate_default_yaml,
    get_default_config,
)

# ===========================================================================
# AC1: Missing non-list sections are backfilled
# ===========================================================================

class TestAC1BackfillMissingSections:

    def test_hooks_section_added(self, tmp_path):
        """Missing hooks section is backfilled with defaults."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        auto_merge_config_file(yaml_path)
        content = yaml_path.read_text()
        assert 'hooks:' in content

    def test_ci_section_added(self, tmp_path):
        """Missing ci section is backfilled with defaults."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        auto_merge_config_file(yaml_path)
        content = yaml_path.read_text()
        assert 'ci:' in content
        assert 'provider: none' in content

    def test_issue_tracker_section_added(self, tmp_path):
        """Missing issue_tracker section is backfilled with defaults."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        auto_merge_config_file(yaml_path)
        content = yaml_path.read_text()
        assert 'issue_tracker:' in content

    def test_lint_blocking_added(self, tmp_path):
        """Missing lint_blocking is backfilled with default false."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        auto_merge_config_file(yaml_path)
        content = yaml_path.read_text()
        assert 'lint_blocking: false' in content

    def test_auto_fix_added(self, tmp_path):
        """Missing auto_fix is backfilled with default false."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        auto_merge_config_file(yaml_path)
        content = yaml_path.read_text()
        assert 'auto_fix: false' in content

    def test_original_values_preserved(self, tmp_path):
        """Original stack/root values are preserved; version is synced to __version__ (BUG-026)."""
        from pactkit import __version__
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: node\nversion: "2.0.0"\nroot: src\n')
        auto_merge_config_file(yaml_path)
        data = yaml.safe_load(yaml_path.read_text())
        assert data['stack'] == 'node'
        assert data['version'] == __version__
        assert data['root'] == 'src'


# ===========================================================================
# AC2: Existing user values are not overwritten
# ===========================================================================

class TestAC2ExistingValuesPreserved:

    def test_existing_hooks_not_overwritten(self, tmp_path):
        """User's existing hooks config is preserved."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(
            'stack: python\nversion: "1.2.0"\nroot: .\n'
            'hooks:\n  pre_commit_lint: true\n'
        )
        auto_merge_config_file(yaml_path)
        data = yaml.safe_load(yaml_path.read_text())
        assert data['hooks']['pre_commit_lint'] is True

    def test_existing_ci_not_overwritten(self, tmp_path):
        """User's existing ci config is preserved."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(
            'stack: python\nversion: "1.2.0"\nroot: .\n'
            'ci:\n  provider: github\n'
        )
        auto_merge_config_file(yaml_path)
        data = yaml.safe_load(yaml_path.read_text())
        assert data['ci']['provider'] == 'github'

    def test_existing_lint_blocking_not_overwritten(self, tmp_path):
        """User's lint_blocking: true is preserved."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(
            'stack: python\nversion: "1.2.0"\nroot: .\n'
            'lint_blocking: true\n'
        )
        auto_merge_config_file(yaml_path)
        data = yaml.safe_load(yaml_path.read_text())
        assert data['lint_blocking'] is True


# ===========================================================================
# AC3: _rewrite_yaml writes all sections
# ===========================================================================

class TestAC3RewriteYamlComplete:

    def test_rewrite_includes_hooks(self, tmp_path):
        """_rewrite_yaml output includes hooks section."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        content = yaml_path.read_text()
        assert 'hooks:' in content
        assert 'pre_commit_lint' in content

    def test_rewrite_includes_ci(self, tmp_path):
        """_rewrite_yaml output includes ci section."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        content = yaml_path.read_text()
        assert 'ci:' in content
        assert 'provider: none' in content

    def test_rewrite_includes_issue_tracker(self, tmp_path):
        """_rewrite_yaml output includes issue_tracker section."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        content = yaml_path.read_text()
        assert 'issue_tracker:' in content

    def test_rewrite_includes_lint_blocking(self, tmp_path):
        """_rewrite_yaml output includes lint_blocking."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        content = yaml_path.read_text()
        assert 'lint_blocking:' in content

    def test_rewrite_includes_auto_fix(self, tmp_path):
        """_rewrite_yaml output includes auto_fix."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        content = yaml_path.read_text()
        assert 'auto_fix:' in content

    def test_rewrite_roundtrip_valid_yaml(self, tmp_path):
        """_rewrite_yaml produces valid YAML that can be re-loaded."""
        from pactkit.config import _rewrite_yaml
        yaml_path = tmp_path / 'pactkit.yaml'
        data = get_default_config()
        _rewrite_yaml(yaml_path, data)
        reloaded = yaml.safe_load(yaml_path.read_text())
        assert isinstance(reloaded, dict)
        assert 'hooks' in reloaded
        assert 'ci' in reloaded
        assert 'issue_tracker' in reloaded


# ===========================================================================
# AC4: Backfill reports added sections
# ===========================================================================

class TestAC4BackfillReport:

    def test_reports_hooks_added(self, tmp_path):
        """Return value includes 'section: hooks' when hooks was missing."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        result = auto_merge_config_file(yaml_path)
        assert 'section: hooks' in result

    def test_reports_ci_added(self, tmp_path):
        """Return value includes 'section: ci' when ci was missing."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        result = auto_merge_config_file(yaml_path)
        assert 'section: ci' in result

    def test_no_report_when_all_sections_exist(self, tmp_path):
        """No section report when all sections (including lists) already present."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(
            'stack: python\nversion: "1.2.0"\nroot: .\n'
            'agents:\n  - system-architect\n'
            'commands:\n  - project-plan\n'
            'skills:\n  - pactkit-board\n'
            'rules:\n  - 01-core-protocol\n'
            'hooks:\n  pre_commit_lint: false\n'
            'ci:\n  provider: none\n'
            'issue_tracker:\n  provider: none\n'
            'lint_blocking: false\n'
            'auto_fix: false\n'
            'e2e:\n  type: none\n'
            'venv:\n  auto_detect: true\n'
            'release:\n  github_release: false\n'
            'regression:\n  strategy: impact\n  max_impact_tests: 50\n'
            'check:\n  security_checklist: true\n'
            'done:\n  lesson_quality_threshold: 15\n'
            'visualize:\n  scan_excludes:\n    - venv\n'
        )
        result = auto_merge_config_file(yaml_path)
        section_reports = [r for r in result if r.startswith('section:')]
        assert len(section_reports) == 0

    def test_reports_multiple_sections(self, tmp_path):
        """All missing sections reported when all are absent (BUG-013: includes lists)."""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('stack: python\nversion: "1.2.0"\nroot: .\n')
        result = auto_merge_config_file(yaml_path)
        section_reports = [r for r in result if r.startswith('section:')]
        # 4 list-type (agents, commands, skills, rules) + 12 non-list (ci, issue_tracker, hooks, lint_blocking, auto_fix, e2e, venv, release, regression, check, done, visualize)
        assert len(section_reports) == 16


# ===========================================================================
# AC5: Fresh init still generates complete config
# ===========================================================================

class TestAC5FreshInit:

    def test_generate_default_yaml_has_hooks(self):
        """generate_default_yaml() includes hooks section."""
        content = generate_default_yaml()
        assert 'hooks:' in content

    def test_generate_default_yaml_has_ci(self):
        """generate_default_yaml() includes ci section."""
        content = generate_default_yaml()
        assert 'ci:' in content

    def test_generate_default_yaml_has_lint_blocking(self):
        """generate_default_yaml() includes lint_blocking."""
        content = generate_default_yaml()
        assert 'lint_blocking:' in content

    def test_fresh_deploy_generates_complete_config(self, tmp_path):
        """Fresh deploy generates pactkit.yaml at $CWD/.claude/ with all sections (BUG-013)."""
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(target=str(tmp_path / '.claude'))
        yaml_path = tmp_path / '.claude' / 'pactkit.yaml'
        assert yaml_path.exists()
        content = yaml_path.read_text()
        assert 'hooks:' in content
        assert 'ci:' in content
        assert 'issue_tracker:' in content
        assert 'lint_blocking:' in content
        assert 'auto_fix:' in content
