"""
BUG-010: _rewrite_yaml drops agent_models and rule_scopes sections.

Tests verify that _rewrite_yaml preserves all config sections through
a round-trip cycle, and that _deploy_hooks uses stack-aware lint commands.
"""
import sys
from pathlib import Path

import yaml

# Ensure project root is importable
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pactkit.config import (  # noqa: E402
    _rewrite_yaml,
    auto_merge_config_file,
    get_default_config,
)


# ===========================================================================
# AC1: agent_models preserved through rewrite cycle
# ===========================================================================
class TestAC1AgentModelsPreserved:
    """agent_models must survive a _rewrite_yaml round-trip."""

    def test_rewrite_preserves_agent_models(self, tmp_path):
        """_rewrite_yaml should serialize agent_models to the output file."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['agent_models'] = {'system-architect': 'opus', 'qa-engineer': 'haiku'}

        _rewrite_yaml(yaml_file, data)

        content = yaml_file.read_text(encoding='utf-8')
        assert 'agent_models' in content
        assert 'system-architect' in content
        assert 'opus' in content

    def test_auto_merge_preserves_agent_models(self, tmp_path):
        """auto_merge_config_file must not lose agent_models."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['agent_models'] = {'system-architect': 'opus'}
        _rewrite_yaml(yaml_file, data)

        auto_merge_config_file(yaml_file)

        reloaded = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))
        assert 'agent_models' in reloaded
        assert reloaded['agent_models']['system-architect'] == 'opus'


# ===========================================================================
# AC2: rule_scopes preserved through rewrite cycle
# ===========================================================================
class TestAC2RuleScopesPreserved:
    """rule_scopes must survive a _rewrite_yaml round-trip."""

    def test_rewrite_preserves_rule_scopes(self, tmp_path):
        """_rewrite_yaml should serialize rule_scopes to the output file."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['rule_scopes'] = {'01-core-protocol': 'src/**/*.py'}

        _rewrite_yaml(yaml_file, data)

        content = yaml_file.read_text(encoding='utf-8')
        assert 'rule_scopes' in content
        assert '01-core-protocol' in content
        assert 'src/**/*.py' in content

    def test_auto_merge_preserves_rule_scopes(self, tmp_path):
        """auto_merge_config_file must not lose rule_scopes."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['rule_scopes'] = {
            '01-core-protocol': 'src/**/*.py',
            '05-workflow-conventions': ['*.md', 'docs/**'],
        }
        _rewrite_yaml(yaml_file, data)

        auto_merge_config_file(yaml_file)

        reloaded = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))
        assert 'rule_scopes' in reloaded
        assert reloaded['rule_scopes']['01-core-protocol'] == 'src/**/*.py'

    def test_rule_scopes_list_pattern_preserved(self, tmp_path):
        """rule_scopes with list-type glob patterns should survive round-trip."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['rule_scopes'] = {'06-mcp-integration': ['src/**/*.py', 'tests/**/*.py']}

        _rewrite_yaml(yaml_file, data)

        reloaded = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))
        assert reloaded['rule_scopes']['06-mcp-integration'] == ['src/**/*.py', 'tests/**/*.py']


# ===========================================================================
# AC3: Hooks use correct stack lint command
# ===========================================================================
class TestAC3HooksStackAware:
    """_deploy_hooks must use the project's configured stack lint command."""

    def test_hooks_use_node_lint_for_node_stack(self, tmp_path):
        """When stack is 'node', pre_commit_lint hook should use node linter."""
        from pactkit.generators.deployer import _deploy_hooks

        hooks_dir = tmp_path / "hooks"
        hooks_config = {'pre_commit_lint': True}

        _deploy_hooks(hooks_dir, hooks_config, stack='node')

        hook_file = hooks_dir / "pre-commit-lint"
        content = hook_file.read_text(encoding='utf-8')
        # Should NOT contain the python linter
        assert 'ruff' not in content
        # Should contain the node linter
        assert 'eslint' in content

    def test_hooks_use_python_lint_for_python_stack(self, tmp_path):
        """When stack is 'python', pre_commit_lint hook should use python linter."""
        from pactkit.generators.deployer import _deploy_hooks

        hooks_dir = tmp_path / "hooks"
        hooks_config = {'pre_commit_lint': True}

        _deploy_hooks(hooks_dir, hooks_config, stack='python')

        hook_file = hooks_dir / "pre-commit-lint"
        content = hook_file.read_text(encoding='utf-8')
        assert 'ruff' in content

    def test_hooks_default_to_python_when_no_stack(self, tmp_path):
        """When no stack is specified, hooks should default to python lint."""
        from pactkit.generators.deployer import _deploy_hooks

        hooks_dir = tmp_path / "hooks"
        hooks_config = {'pre_commit_lint': True}

        _deploy_hooks(hooks_dir, hooks_config)

        hook_file = hooks_dir / "pre-commit-lint"
        content = hook_file.read_text(encoding='utf-8')
        assert 'ruff' in content


# ===========================================================================
# AC4: Round-trip fidelity
# ===========================================================================
class TestAC4RoundTripFidelity:
    """Full round-trip: all sections preserved through _rewrite_yaml."""

    def test_full_config_round_trip(self, tmp_path):
        """A fully-populated config must survive a write→read→write→read cycle."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        data['agent_models'] = {'system-architect': 'opus'}
        data['rule_scopes'] = {'01-core-protocol': 'src/**/*.py'}
        data['exclude'] = {'agents': ['system-medic']}

        # First write
        _rewrite_yaml(yaml_file, data)
        first_read = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))

        # Second write (simulates another pactkit update)
        _rewrite_yaml(yaml_file, first_read)
        second_read = yaml.safe_load(yaml_file.read_text(encoding='utf-8'))

        # All sections must be present after two cycles
        assert 'agent_models' in second_read
        assert second_read['agent_models']['system-architect'] == 'opus'
        assert 'rule_scopes' in second_read
        assert second_read['rule_scopes']['01-core-protocol'] == 'src/**/*.py'
        assert 'exclude' in second_read
        assert 'ci' in second_read
        assert 'hooks' in second_read
        assert 'lint_blocking' in second_read

    def test_empty_optional_sections_not_written(self, tmp_path):
        """If agent_models/rule_scopes are absent, they should not appear."""
        yaml_file = tmp_path / "pactkit.yaml"
        data = get_default_config()
        # No agent_models or rule_scopes in default config

        _rewrite_yaml(yaml_file, data)

        content = yaml_file.read_text(encoding='utf-8')
        assert 'agent_models' not in content
        assert 'rule_scopes' not in content
