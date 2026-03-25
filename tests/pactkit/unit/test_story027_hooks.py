"""Tests for STORY-027: Safe Opt-in Hook Templates.

AC1: Default config has all hooks disabled
AC2: Hook enablement deploys script
AC4: No prompt-type hooks in output
AC7: Invalid hook name warning
"""
import sys
import warnings
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestAC1DefaultDisabled:

    def test_default_config_has_hooks_section(self):
        """get_default_config includes hooks with all false."""
        from pactkit.config import get_default_config
        config = get_default_config()
        assert 'hooks' in config
        hooks = config['hooks']
        assert isinstance(hooks, dict)
        for key, val in hooks.items():
            assert val is False, f'Hook {key} should default to False'

    def test_default_yaml_contains_hooks(self):
        """generate_default_yaml includes hooks section."""
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert 'hooks:' in yaml_text
        assert 'pre_commit_lint: false' in yaml_text

    def test_default_deploy_no_hook_scripts(self, tmp_path):
        """Default deployment creates no hook scripts."""
        from pactkit.generators.deployer import deploy
        deploy(target=str(tmp_path / '.claude'))
        hooks_dir = tmp_path / '.claude' / 'hooks'
        if hooks_dir.exists():
            scripts = list(hooks_dir.glob('*'))
            assert len(scripts) == 0, f'Expected no hook scripts, found {scripts}'


class TestAC2HookEnablement:

    def test_enabled_hook_deploys_script(self, tmp_path):
        """Enabling pre_commit_lint deploys a script file."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        config['hooks'] = {'pre_commit_lint': True, 'post_test_coverage': False, 'pre_push_check': False}
        deploy(config=config, target=str(tmp_path / '.claude'))
        hooks_dir = tmp_path / '.claude' / 'hooks'
        assert hooks_dir.exists()
        scripts = list(hooks_dir.glob('*'))
        assert len(scripts) >= 1, 'Expected at least one hook script'


class TestAC4CommandTypeOnly:

    def test_hook_scripts_are_shell_scripts(self, tmp_path):
        """Deployed hook scripts are shell scripts (command type)."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        config['hooks'] = {'pre_commit_lint': True, 'post_test_coverage': True, 'pre_push_check': True}
        deploy(config=config, target=str(tmp_path / '.claude'))
        hooks_dir = tmp_path / '.claude' / 'hooks'
        for script in hooks_dir.glob('*'):
            content = script.read_text()
            assert content.startswith('#!/'), f'{script.name} should start with shebang'
            # Must not invoke claude/agent
            assert 'claude' not in content.lower() or 'claude/hooks' in content.lower()

    def test_hook_scripts_exit_zero(self, tmp_path):
        """All hook scripts exit 0 (report-only, non-blocking)."""
        from pactkit.config import get_default_config
        from pactkit.generators.deployer import deploy
        config = get_default_config()
        config['hooks'] = {'pre_commit_lint': True, 'post_test_coverage': True, 'pre_push_check': True}
        deploy(config=config, target=str(tmp_path / '.claude'))
        hooks_dir = tmp_path / '.claude' / 'hooks'
        for script in hooks_dir.glob('*'):
            content = script.read_text()
            assert 'exit 0' in content, f'{script.name} should contain exit 0'


class TestAC7InvalidHookWarning:

    def test_invalid_hook_name_emits_warning(self):
        """Unknown hook name triggers validation warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['hooks'] = {'invalid_hook': True}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('invalid_hook' in m for m in msgs), (
            f'Expected warning about invalid_hook, got: {msgs}'
        )


class TestValidHookTemplates:

    def test_valid_hook_templates_defined(self):
        from pactkit.config import VALID_HOOK_TEMPLATES
        assert 'pre_commit_lint' in VALID_HOOK_TEMPLATES
        assert 'post_test_coverage' in VALID_HOOK_TEMPLATES
        assert 'pre_push_check' in VALID_HOOK_TEMPLATES
