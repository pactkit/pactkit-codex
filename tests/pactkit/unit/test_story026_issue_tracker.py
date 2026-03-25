"""Tests for STORY-026: Conditional Issue Tracker Integration.

AC1: Default config has issue_tracker: {provider: none}
AC5: Invalid provider emits warning
AC6: Backward compatibility — missing section loads ok
"""
import sys
import warnings
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ===========================================================================
# AC1: Default Configuration
# ===========================================================================

class TestAC1DefaultConfiguration:

    def test_default_config_has_issue_tracker_none(self):
        """get_default_config includes issue_tracker: {provider: none}."""
        from pactkit.config import get_default_config
        config = get_default_config()
        assert 'issue_tracker' in config
        assert config['issue_tracker'] == {'provider': 'none'}

    def test_default_yaml_contains_issue_tracker(self):
        """generate_default_yaml includes issue_tracker section."""
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert 'issue_tracker:' in yaml_text
        assert 'provider: none' in yaml_text


# ===========================================================================
# AC5: Invalid Provider Warning
# ===========================================================================

class TestAC5InvalidProviderWarning:

    def test_invalid_issue_provider_emits_warning(self):
        """Invalid issue_tracker provider triggers a warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['issue_tracker'] = {'provider': 'jira'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('jira' in m for m in msgs), (
            f'Expected warning about jira, got: {msgs}'
        )

    def test_valid_providers_no_warning(self):
        """Valid issue_tracker providers produce no warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        for provider in ('github', 'none'):
            config['issue_tracker'] = {'provider': provider}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                validate_config(config)
            issue_warnings = [
                str(x.message) for x in w
                if 'issue' in str(x.message).lower() or 'provider' in str(x.message).lower()
            ]
            assert not issue_warnings, (
                f'Unexpected warning for {provider}: {issue_warnings}'
            )


# ===========================================================================
# AC6: Backward Compatibility
# ===========================================================================

class TestAC6BackwardCompatibility:

    def test_config_without_issue_tracker_loads_ok(self, tmp_path):
        """Config without issue_tracker section loads without error."""
        from pactkit.config import load_config
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('version: "1.0.0"\nstack: python\n')
        config = load_config(yaml_path)
        it = config.get('issue_tracker', {'provider': 'none'})
        assert it.get('provider') == 'none'

    def test_deploy_without_issue_tracker(self, tmp_path):
        """Deploy with missing issue_tracker section succeeds."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        config.pop('issue_tracker', None)
        deploy(config=config, target=str(tmp_path / '.claude'))


# ===========================================================================
# VALID_ISSUE_PROVIDERS constant
# ===========================================================================

class TestValidIssueProviders:

    def test_valid_issue_providers_defined(self):
        from pactkit.config import VALID_ISSUE_PROVIDERS
        assert 'github' in VALID_ISSUE_PROVIDERS
        assert 'none' in VALID_ISSUE_PROVIDERS


# ===========================================================================
# Plan/Done commands contain issue tracker instructions
# ===========================================================================

class TestCommandPromptIntegration:

    def test_plan_command_mentions_issue_tracker(self):
        """Plan command playbook has issue tracker instructions."""
        from pactkit.prompts import COMMANDS_CONTENT
        plan_content = COMMANDS_CONTENT.get('project-plan.md', '')
        assert 'issue_tracker' in plan_content or 'issue tracker' in plan_content.lower()

    def test_done_command_mentions_issue_tracker(self):
        """Done command playbook has issue tracker instructions."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'issue_tracker' in done_content or 'issue tracker' in done_content.lower()
