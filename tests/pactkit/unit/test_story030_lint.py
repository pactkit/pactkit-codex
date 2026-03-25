"""Tests for STORY-030: Smart Lint Integration in Done Command.

AC1: Default lint_blocking is false
AC2: lint_blocking configurable
AC3: auto_fix configurable
AC5: Done command prompt mentions lint
"""
import sys
import warnings
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestAC1DefaultLintConfig:

    def test_default_lint_blocking_false(self):
        """Default config has lint_blocking: false."""
        from pactkit.config import get_default_config
        config = get_default_config()
        assert config.get('lint_blocking') is False

    def test_default_auto_fix_false(self):
        """Default config has auto_fix: false."""
        from pactkit.config import get_default_config
        config = get_default_config()
        assert config.get('auto_fix') is False

    def test_default_yaml_contains_lint_settings(self):
        """generate_default_yaml includes lint settings."""
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert 'lint_blocking' in yaml_text
        assert 'auto_fix' in yaml_text


class TestAC2LintBlockingConfig:

    def test_lint_blocking_accepted_by_validator(self):
        """lint_blocking: true passes validation without warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['lint_blocking'] = True
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        lint_warnings = [str(x.message) for x in w if 'lint' in str(x.message).lower()]
        assert not lint_warnings


class TestAC3AutoFixConfig:

    def test_auto_fix_accepted_by_validator(self):
        """auto_fix: true passes validation without warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['auto_fix'] = True
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        fix_warnings = [str(x.message) for x in w if 'auto_fix' in str(x.message).lower()]
        assert not fix_warnings


class TestAC5DoneCommandLintIntegration:

    def test_done_command_mentions_lint(self):
        """Done command playbook includes lint gate instructions."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'lint' in done_content.lower()

    def test_done_command_mentions_lint_blocking(self):
        """Done command playbook mentions lint_blocking option."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'lint_blocking' in done_content

    def test_done_command_mentions_auto_fix(self):
        """Done command playbook mentions auto_fix option."""
        from pactkit.prompts import COMMANDS_CONTENT
        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'auto_fix' in done_content

    def test_lang_profiles_have_lint_commands(self):
        """LANG_PROFILES include lint_command entries."""
        from pactkit.prompts.workflows import LANG_PROFILES
        for stack, profile in LANG_PROFILES.items():
            assert 'lint_command' in profile, f'{stack} missing lint_command'
