"""
BUG-022: load_config shallow merge loses nested dict defaults.
"""
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _config():
    from pactkit import config
    return config


def _write_yaml(path, data):
    """Write a dict as YAML to a file."""
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ===========================================================================
# R1: Deep Merge for Nested Dict Sections (AC1, AC3)
# ===========================================================================

class TestR1DeepMergeVenv:
    """AC1: Partial venv section preserves defaults."""

    def test_partial_venv_preserves_auto_detect(self, tmp_path):
        """Given user specifies venv.path, auto_detect should still be present."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'venv': {'path': '.venv'}})

        result = cfg.load_config(yaml_path)
        assert result['venv'].get('auto_detect') is True  # default
        assert result['venv'].get('path') == '.venv'  # user value

    def test_user_venv_override_wins(self, tmp_path):
        """AC2: User's auto_detect=false wins over default True."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'venv': {'auto_detect': False}})

        result = cfg.load_config(yaml_path)
        assert result['venv']['auto_detect'] is False


class TestR1DeepMergeHooks:
    """AC3: Partial hooks section preserves defaults."""

    def test_partial_hooks_preserves_other_keys(self, tmp_path):
        """Given user enables one hook, other hooks should remain False (default)."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'hooks': {'pre_commit_lint': True}})

        result = cfg.load_config(yaml_path)
        assert result['hooks']['pre_commit_lint'] is True
        assert result['hooks'].get('post_test_coverage') is False  # default
        assert result['hooks'].get('pre_push_check') is False  # default


class TestR1DeepMergeCi:
    """AC4: Full CI section override works as before."""

    def test_full_ci_section_override(self, tmp_path):
        """User specifies complete ci section, should work as before."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'ci': {'provider': 'github'}})

        result = cfg.load_config(yaml_path)
        assert result['ci']['provider'] == 'github'


class TestR1DeepMergeIssueTracker:
    """Deep merge also applies to issue_tracker section."""

    def test_partial_issue_tracker(self, tmp_path):
        """Partial issue_tracker section should deep merge."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        # Default issue_tracker has provider: none
        # If user specifies extra keys, both should be present
        _write_yaml(yaml_path, {'issue_tracker': {'provider': 'github'}})

        result = cfg.load_config(yaml_path)
        assert result['issue_tracker']['provider'] == 'github'


# ===========================================================================
# R2: Non-Dict Keys Unchanged (AC5)
# ===========================================================================

class TestR2NonDictKeysUnchanged:
    """AC5: Non-dict keys (stack, lint_blocking) use shallow override."""

    def test_stack_override(self, tmp_path):
        """String key 'stack' should be directly overridden."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'stack': 'node'})

        result = cfg.load_config(yaml_path)
        assert result['stack'] == 'node'

    def test_lint_blocking_override(self, tmp_path):
        """Boolean key 'lint_blocking' should be directly overridden."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'lint_blocking': True})

        result = cfg.load_config(yaml_path)
        assert result['lint_blocking'] is True


# ===========================================================================
# R2: List Keys Fully Replaced (AC6)
# ===========================================================================

class TestR2ListKeysReplaced:
    """AC6: List keys (agents, commands, etc.) are fully replaced, not merged."""

    def test_agents_list_replaced(self, tmp_path):
        """User's agents list replaces default, not merged."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'agents': ['senior-developer']})

        result = cfg.load_config(yaml_path)
        assert result['agents'] == ['senior-developer']
        # Should NOT contain default agents
        assert 'system-architect' not in result['agents']

    def test_commands_list_replaced(self, tmp_path):
        """User's commands list replaces default, not merged."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'commands': ['project-plan', 'project-act']})

        result = cfg.load_config(yaml_path)
        assert result['commands'] == ['project-plan', 'project-act']


# ===========================================================================
# R3: Explicit User Values Win
# ===========================================================================

class TestR3UserValuesWin:
    """User explicitly specified values must override defaults."""

    def test_user_override_all_venv_keys(self, tmp_path):
        """User specifies both auto_detect and path, both should appear."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        _write_yaml(yaml_path, {'venv': {'auto_detect': False, 'path': 'custom_venv'}})

        result = cfg.load_config(yaml_path)
        assert result['venv']['auto_detect'] is False
        assert result['venv']['path'] == 'custom_venv'


# ===========================================================================
# R4: Backward Compatibility
# ===========================================================================

class TestR4BackwardCompatibility:
    """Existing pactkit.yaml files produce identical results."""

    def test_complete_nested_section_unchanged(self, tmp_path):
        """User with complete nested sections should get identical merge results."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        # Full hooks section matching defaults
        full_hooks = {
            'pre_commit_lint': True,
            'post_test_coverage': True,
            'pre_push_check': False,
        }
        _write_yaml(yaml_path, {'hooks': full_hooks})

        result = cfg.load_config(yaml_path)
        assert result['hooks'] == full_hooks

    def test_empty_file_returns_defaults(self, tmp_path):
        """Empty file should return defaults (existing behavior)."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('')

        result = cfg.load_config(yaml_path)
        default = cfg.get_default_config()
        assert result == default
