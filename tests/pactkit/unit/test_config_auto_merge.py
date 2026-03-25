"""
STORY-009: Config Auto-Merge — pactkit init auto-merges new components.
"""
from pathlib import Path
from unittest.mock import patch

import yaml

from pactkit import __version__

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config():
    from pactkit import config
    return config


def _write_yaml(path, data):
    """Write a dict as YAML to a file."""
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def _write_yaml_text(path, text):
    """Write raw YAML text to a file."""
    path.write_text(text)


# ===========================================================================
# Scenario 1: Fresh install (no yaml) — auto_merge returns empty
# ===========================================================================

class TestFreshInstallNoMerge:
    """auto_merge_config_file on missing file does nothing."""

    def test_missing_file_returns_empty(self, tmp_path):
        cfg = _config()
        result = cfg.auto_merge_config_file(tmp_path / 'nonexistent.yaml')
        assert result == []

    def test_missing_file_no_side_effects(self, tmp_path):
        cfg = _config()
        path = tmp_path / 'nonexistent.yaml'
        cfg.auto_merge_config_file(path)
        assert not path.exists()


# ===========================================================================
# Scenario 2: Upgrade with new component — auto-added
# ===========================================================================

class TestUpgradeAutoMerge:
    """New components in VALID_* are auto-appended."""

    def test_missing_command_auto_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        # Write yaml with all commands EXCEPT project-design
        commands = sorted(cfg.VALID_COMMANDS - {'project-design'})
        _write_yaml(yaml_path, {'commands': commands})

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('project-design' in item for item in added)

    def test_yaml_file_updated_on_disk(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-design'})
        _write_yaml(yaml_path, {'commands': commands})

        cfg.auto_merge_config_file(yaml_path)

        # Re-read yaml from disk
        updated = yaml.safe_load(yaml_path.read_text())
        assert 'project-design' in updated['commands']

    def test_missing_agent_auto_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        agents = sorted(cfg.VALID_AGENTS - {'code-explorer'})
        _write_yaml(yaml_path, {'agents': agents})

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('code-explorer' in item for item in added)

    def test_missing_skill_auto_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        skills = sorted(cfg.VALID_SKILLS - {'pactkit-board'})
        _write_yaml(yaml_path, {'skills': skills})

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('pactkit-board' in item for item in added)

    def test_missing_rule_auto_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        rules = sorted(cfg.VALID_RULES - {'06-mcp-integration'})
        _write_yaml(yaml_path, {'rules': rules})

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('06-mcp-integration' in item for item in added)

    def test_load_config_after_merge_has_new_items(self, tmp_path):
        """After auto_merge, load_config returns the merged list."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-design'})
        _write_yaml(yaml_path, {'commands': commands})

        cfg.auto_merge_config_file(yaml_path)
        loaded = cfg.load_config(yaml_path)
        assert 'project-design' in loaded['commands']


# ===========================================================================
# Scenario 3: User intentionally excluded a component
# ===========================================================================

class TestExcludeOptOut:
    """Items in exclude section are NOT auto-added."""

    def test_excluded_command_not_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-sprint'})
        data = {
            'commands': commands,
            'exclude': {'commands': ['project-sprint']},
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert not any('project-sprint' in item for item in added)

    def test_excluded_agent_not_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        agents = sorted(cfg.VALID_AGENTS - {'qa-engineer'})
        data = {
            'agents': agents,
            'exclude': {'agents': ['qa-engineer']},
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert not any('qa-engineer' in item for item in added)

    def test_exclude_preserved_in_yaml(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-sprint', 'project-design'})
        data = {
            'commands': commands,
            'exclude': {'commands': ['project-sprint']},
        }
        _write_yaml(yaml_path, data)

        cfg.auto_merge_config_file(yaml_path)

        updated = yaml.safe_load(yaml_path.read_text())
        assert 'project-sprint' in updated['exclude']['commands']
        # project-design was NOT excluded so it should be added
        assert 'project-design' in updated['commands']

    def test_exclude_some_add_others(self, tmp_path):
        """Exclude one missing item, auto-add the other."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-sprint', 'project-design'})
        data = {
            'commands': commands,
            'exclude': {'commands': ['project-sprint']},
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('project-design' in item for item in added)
        assert not any('project-sprint' in item for item in added)


# ===========================================================================
# Scenario 4: Multiple new components
# ===========================================================================

class TestMultipleNewComponents:
    """Multiple missing items are all auto-added."""

    def test_two_missing_commands_both_added(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-design', 'project-hotfix'})
        _write_yaml(yaml_path, {'commands': commands})

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('project-design' in item for item in added)
        assert any('project-hotfix' in item for item in added)

    def test_each_added_item_has_log_entry(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-design', 'project-hotfix'})
        _write_yaml(yaml_path, {'commands': commands})

        added = cfg.auto_merge_config_file(yaml_path)
        assert len([a for a in added if 'commands' in a]) >= 2

    def test_cross_category_merge(self, tmp_path):
        """Missing items in agents AND commands are both auto-added."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        data = {
            'agents': sorted(cfg.VALID_AGENTS - {'code-explorer'}),
            'commands': sorted(cfg.VALID_COMMANDS - {'project-design'}),
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('code-explorer' in item for item in added)
        assert any('project-design' in item for item in added)


# ===========================================================================
# Scenario 5: Backward compatibility
# ===========================================================================

class TestBackwardCompatibility:
    """Existing yaml without exclude section works correctly."""

    def test_no_exclude_section_works(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS - {'project-design'})
        _write_yaml(yaml_path, {'commands': commands})

        # Should not raise
        added = cfg.auto_merge_config_file(yaml_path)
        assert isinstance(added, list)

    def test_empty_yaml_returns_empty(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('')

        added = cfg.auto_merge_config_file(yaml_path)
        assert added == []

    def test_yaml_with_only_scalar_keys_backfills_lists(self, tmp_path):
        """BUG-013: missing list keys are backfilled with full defaults."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {
            'version': '1.0.0', 'stack': 'python',
            'ci': {'provider': 'none'},
            'issue_tracker': {'provider': 'none'},
            'hooks': {'pre_commit_lint': False, 'post_test_coverage': False, 'pre_push_check': False},
            'lint_blocking': False,
            'auto_fix': False,
        })

        added = cfg.auto_merge_config_file(yaml_path)
        section_reports = [r for r in added if r.startswith('section:')]
        assert 'section: agents' in section_reports
        assert 'section: commands' in section_reports
        assert 'section: skills' in section_reports
        assert 'section: rules' in section_reports

    def test_full_list_nothing_added(self, tmp_path):
        """If user already has all VALID items and sections, nothing is added."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {
            'version': __version__,
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'ci': {'provider': 'none'},
            'issue_tracker': {'provider': 'none'},
            'hooks': {'pre_commit_lint': False, 'post_test_coverage': False, 'pre_push_check': False},
            'lint_blocking': False,
            'auto_fix': False,
            'e2e': {'type': 'none', 'blocking': False, 'test_dir': 'tests/e2e', 'env_file': '.env.test',
                    'api_spec': '', 'compose_file': 'docker-compose.test.yml'},
            'venv': {'auto_detect': True},
            'release': {'github_release': False},
            'regression': {'strategy': 'impact', 'max_impact_tests': 50},
            'check': {'security_checklist': True},
            'done': {'lesson_quality_threshold': 15},
            'visualize': {'scan_excludes': ['venv', '.venv']},
        })

        added = cfg.auto_merge_config_file(yaml_path)
        assert added == []

    def test_load_config_unchanged_behavior(self, tmp_path):
        """load_config still respects partial lists (no auto-merge)."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'commands': ['project-plan', 'project-act']})

        loaded = cfg.load_config(yaml_path)
        assert loaded['commands'] == ['project-plan', 'project-act']


# ===========================================================================
# Scenario 6: Edge cases
# ===========================================================================

class TestEdgeCases:
    """Edge cases for auto-merge logic."""

    def test_empty_list_gets_all_valid_items(self, tmp_path):
        """Empty list → all VALID items are new → all added."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'commands': []})

        added = cfg.auto_merge_config_file(yaml_path)
        updated = yaml.safe_load(yaml_path.read_text())
        assert set(updated['commands']) == cfg.VALID_COMMANDS

    def test_unknown_items_preserved(self, tmp_path):
        """Unknown items in user list are left as-is."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        commands = sorted(cfg.VALID_COMMANDS) + ['my-custom-command']
        _write_yaml(yaml_path, {'commands': commands})

        cfg.auto_merge_config_file(yaml_path)
        updated = yaml.safe_load(yaml_path.read_text())
        assert 'my-custom-command' in updated['commands']

    def test_exclude_empty_dict_works(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        data = {
            'commands': sorted(cfg.VALID_COMMANDS - {'project-design'}),
            'exclude': {},
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('project-design' in item for item in added)

    def test_exclude_empty_list_works(self, tmp_path):
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        data = {
            'commands': sorted(cfg.VALID_COMMANDS - {'project-design'}),
            'exclude': {'commands': []},
        }
        _write_yaml(yaml_path, data)

        added = cfg.auto_merge_config_file(yaml_path)
        assert any('project-design' in item for item in added)


# ===========================================================================
# Scenario 7: Deployer integration — output message
# ===========================================================================

class TestDeployerIntegration:
    """Deployer prints auto-added items during init."""

    def test_deploy_auto_merge_output(self, tmp_path, capsys):
        from pactkit.generators.deployer import deploy

        claude_root = tmp_path / '.claude'
        claude_root.mkdir(parents=True)
        yaml_path = claude_root / 'pactkit.yaml'
        cfg = _config()
        commands = sorted(cfg.VALID_COMMANDS - {'project-design'})
        _write_yaml(yaml_path, {
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': commands,
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        })

        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy()

        output = capsys.readouterr().out
        assert 'Auto-added' in output
        assert 'project-design' in output

    def test_deploy_no_merge_message_when_up_to_date(self, tmp_path, capsys):
        from pactkit.generators.deployer import deploy

        claude_root = tmp_path / '.claude'
        claude_root.mkdir(parents=True)
        yaml_path = claude_root / 'pactkit.yaml'
        cfg = _config()
        _write_yaml(yaml_path, {
            'version': __version__,
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'ci': {'provider': 'none'},
            'issue_tracker': {'provider': 'none'},
            'hooks': {'pre_commit_lint': False, 'post_test_coverage': False, 'pre_push_check': False},
            'lint_blocking': False,
            'auto_fix': False,
            'e2e': {'type': 'none', 'blocking': False, 'test_dir': 'tests/e2e', 'env_file': '.env.test',
                    'api_spec': '', 'compose_file': 'docker-compose.test.yml'},
            'venv': {'auto_detect': True},
            'release': {'github_release': False},
            'regression': {'strategy': 'impact', 'max_impact_tests': 50},
            'check': {'security_checklist': True},
            'done': {'lesson_quality_threshold': 15},
            'visualize': {'scan_excludes': ['venv', '.venv']},
        })

        with patch.object(Path, 'home', return_value=tmp_path), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy()

        output = capsys.readouterr().out
        assert 'Auto-added' not in output
