"""Tests for STORY-028: Context-Aware Rule Scoping.

AC1: Unscoped rule has no includeFiles
AC2: Scoped rule gets includeFiles in frontmatter
AC3: Invalid glob pattern warns
AC4: Backward compat — no scope fields works
"""
import re
import sys
import warnings
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _deploy_rules_to(tmp_path, config=None):
    """Deploy and return the rules directory."""
    from pactkit.generators.deployer import deploy
    deploy(config=config, target=str(tmp_path / '.claude'))
    return tmp_path / '.claude' / 'rules'


class TestAC1UnscopedRule:

    def test_unscoped_rules_no_include_files(self, tmp_path):
        """Rules without scope have no includeFiles in content."""
        rules_dir = _deploy_rules_to(tmp_path)
        for rule_file in rules_dir.glob('*.md'):
            content = rule_file.read_text()
            # Unscoped rules should not have includeFiles
            if '---' in content:
                # Check frontmatter if present
                match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if match:
                    fm = yaml.safe_load(match.group(1))
                    if fm and isinstance(fm, dict):
                        assert 'includeFiles' not in fm, (
                            f'{rule_file.name} should not have includeFiles without scope'
                        )


class TestAC2ScopedRule:

    def test_scoped_rule_gets_include_files(self, tmp_path):
        """Rule with scope gets includeFiles in deployed frontmatter."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['rule_scopes'] = {'06-mcp-integration': 'src/integrations/**'}
        rules_dir = _deploy_rules_to(tmp_path, config=config)
        rule_file = rules_dir / '06-mcp-integration.md'
        assert rule_file.exists()
        content = rule_file.read_text()
        assert 'includeFiles' in content

    def test_scoped_rule_contains_glob_pattern(self, tmp_path):
        """includeFiles contains the specified glob pattern."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['rule_scopes'] = {'06-mcp-integration': 'src/integrations/**'}
        rules_dir = _deploy_rules_to(tmp_path, config=config)
        rule_file = rules_dir / '06-mcp-integration.md'
        content = rule_file.read_text()
        assert 'src/integrations/**' in content


class TestAC3InvalidGlobWarning:

    def test_invalid_glob_pattern_emits_warning(self):
        """Invalid glob pattern in rule_scopes triggers warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['rule_scopes'] = {'01-core-protocol': '[invalid'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('[invalid' in m or 'glob' in m.lower() for m in msgs), (
            f'Expected warning about invalid glob, got: {msgs}'
        )

    def test_unknown_rule_in_scopes_emits_warning(self):
        """Unknown rule ID in rule_scopes triggers warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['rule_scopes'] = {'99-nonexistent': 'src/**'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('99-nonexistent' in m for m in msgs), (
            f'Expected warning about 99-nonexistent, got: {msgs}'
        )


class TestAC4BackwardCompat:

    def test_config_without_rule_scopes_works(self, tmp_path):
        """Config without rule_scopes deploys successfully."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config.pop('rule_scopes', None)
        rules_dir = _deploy_rules_to(tmp_path, config=config)
        assert any(rules_dir.glob('*.md'))

    def test_deploy_with_empty_rule_scopes(self, tmp_path):
        """Empty rule_scopes dict deploys successfully."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['rule_scopes'] = {}
        rules_dir = _deploy_rules_to(tmp_path, config=config)
        assert any(rules_dir.glob('*.md'))
