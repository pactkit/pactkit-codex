"""
BUG-023: _rewrite_yaml drops unknown user-defined config keys.
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
# R1: Preserve Unknown Keys (AC1, AC2)
# ===========================================================================

class TestR1PreserveUnknownKeys:
    """AC1-AC2: Custom/unknown keys are preserved after rewrite."""

    def test_single_custom_key_preserved(self, tmp_path):
        """AC1: Custom key 'team' is preserved after rewrite."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        # Create a config with known keys + unknown key
        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'team': 'backend',  # Unknown key
        }
        _write_yaml(yaml_path, data)

        # Trigger rewrite via auto_merge_config_file
        # (need to ensure something triggers a rewrite)
        cfg._rewrite_yaml(yaml_path, data)

        # Re-read and verify
        result = yaml.safe_load(yaml_path.read_text())
        assert result.get('team') == 'backend'

    def test_nested_custom_key_preserved(self, tmp_path):
        """AC2: Nested custom key 'deploy.target' is preserved."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'deploy': {'target': 'staging', 'region': 'us-east-1'},  # Unknown nested
        }
        _write_yaml(yaml_path, data)

        cfg._rewrite_yaml(yaml_path, data)

        result = yaml.safe_load(yaml_path.read_text())
        assert result.get('deploy') == {'target': 'staging', 'region': 'us-east-1'}

    def test_multiple_custom_keys_preserved(self, tmp_path):
        """Multiple unknown keys are all preserved."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'team': 'backend',
            'env': 'production',
            'custom_paths': ['/opt/app', '/var/log'],
        }
        _write_yaml(yaml_path, data)

        cfg._rewrite_yaml(yaml_path, data)

        result = yaml.safe_load(yaml_path.read_text())
        assert result.get('team') == 'backend'
        assert result.get('env') == 'production'
        assert result.get('custom_paths') == ['/opt/app', '/var/log']


# ===========================================================================
# R2: Round-Trip Safety
# ===========================================================================

class TestR2RoundTripSafety:
    """Data loaded from file should survive rewrite without loss."""

    def test_round_trip_preserves_all_keys(self, tmp_path):
        """Load -> rewrite -> load should not lose any keys."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        original_data = {
            'version': '2.0.0',
            'stack': 'node',
            'agents': ['senior-developer', 'qa-engineer'],
            'commands': ['project-plan', 'project-act'],
            'skills': ['pactkit-visualize'],
            'rules': ['01-core-protocol'],
            'ci': {'provider': 'github'},
            'hooks': {'pre_commit_lint': True},
            'team': 'platform',  # Custom
            'metadata': {'owner': 'alice'},  # Custom nested
        }
        _write_yaml(yaml_path, original_data)

        # Load and rewrite
        loaded = yaml.safe_load(yaml_path.read_text())
        cfg._rewrite_yaml(yaml_path, loaded)

        # Verify round-trip
        result = yaml.safe_load(yaml_path.read_text())
        assert result.get('team') == 'platform'
        assert result.get('metadata') == {'owner': 'alice'}
        # Known keys should also be present
        assert result.get('stack') == 'node'


# ===========================================================================
# R3: Comment Marker for Unknown Keys (AC3)
# ===========================================================================

class TestR3CommentMarker:
    """AC3: Custom keys appear under a '# Custom' comment section."""

    def test_custom_keys_have_comment_section(self, tmp_path):
        """Custom keys should appear under a comment marker."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'team': 'backend',
            'env': 'staging',
        }
        _write_yaml(yaml_path, data)

        cfg._rewrite_yaml(yaml_path, data)

        content = yaml_path.read_text()
        # Should have a comment marker for custom keys
        assert '# Custom' in content
        # Custom keys should appear after the comment
        lines = content.split('\n')
        custom_comment_idx = None
        for i, line in enumerate(lines):
            if '# Custom' in line:
                custom_comment_idx = i
                break
        assert custom_comment_idx is not None
        # 'team' and 'env' should appear after the comment
        remaining = '\n'.join(lines[custom_comment_idx:])
        assert 'team:' in remaining
        assert 'env:' in remaining


# ===========================================================================
# R4: Backward Compatibility (AC4)
# ===========================================================================

class TestR4BackwardCompatibility:
    """AC4: Files without custom keys produce unchanged output."""

    def test_no_custom_keys_no_extra_section(self, tmp_path):
        """Standard config without custom keys should not have '# Custom' section."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        # Standard config only
        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
            'ci': {'provider': 'none'},
            'issue_tracker': {'provider': 'none'},
            'hooks': {'pre_commit_lint': False, 'post_test_coverage': False, 'pre_push_check': False},
            'lint_blocking': False,
            'auto_fix': False,
            'venv': {'auto_detect': True},
        }
        _write_yaml(yaml_path, data)

        cfg._rewrite_yaml(yaml_path, data)

        content = yaml_path.read_text()
        # No '# Custom' section when no unknown keys
        assert '# Custom' not in content


# ===========================================================================
# AC5: Known Key Values Still Normalized
# ===========================================================================

class TestAC5KnownKeysNormalized:
    """AC5: Known keys are normalized while custom keys are preserved."""

    def test_lint_blocking_normalized(self, tmp_path):
        """lint_blocking: True (capital) should become lowercase true."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        data = {
            'version': '1.0.0',
            'stack': 'python',
            'lint_blocking': True,  # Will be normalized
            'team': 'backend',  # Custom, preserved as-is
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        }
        _write_yaml(yaml_path, data)

        cfg._rewrite_yaml(yaml_path, data)

        content = yaml_path.read_text()
        # lint_blocking should be normalized to lowercase
        assert 'lint_blocking: true' in content
        # Custom key preserved
        result = yaml.safe_load(content)
        assert result.get('team') == 'backend'


# ===========================================================================
# Integration: auto_merge_config_file triggers _rewrite_yaml
# ===========================================================================

class TestIntegrationAutoMerge:
    """Verify auto_merge_config_file preserves custom keys."""

    def test_auto_merge_preserves_custom_keys(self, tmp_path):
        """When auto_merge triggers rewrite, custom keys survive."""
        cfg = _config()
        yaml_path = tmp_path / 'pactkit.yaml'

        # Missing one skill to trigger auto-add
        data = {
            'version': '1.0.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS - {'pactkit-board'}),  # Missing one
            'rules': sorted(cfg.VALID_RULES),
            'ci': {'provider': 'none'},
            'issue_tracker': {'provider': 'none'},
            'hooks': {'pre_commit_lint': False, 'post_test_coverage': False, 'pre_push_check': False},
            'lint_blocking': False,
            'auto_fix': False,
            'venv': {'auto_detect': True},
            'team': 'backend',  # Custom key
        }
        _write_yaml(yaml_path, data)

        # This should trigger a rewrite
        added = cfg.auto_merge_config_file(yaml_path)
        assert len(added) > 0  # Something was added

        # Custom key should survive
        result = yaml.safe_load(yaml_path.read_text())
        assert result.get('team') == 'backend'
