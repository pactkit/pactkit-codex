"""Tests for STORY-060: Fix /project-init Hang — Non-interactive Guard & Scan Limits.

AC1: Phase 0.5 playbook text has no interactive prompt
AC2: Enterprise flags forwarded from cli.py to deploy()
AC3: deploy() accepts no_git, no_external, non_interactive (no **_kwargs)
AC4: upgrade subparser accepts --no-git
AC5: _scan_files() truncates at MAX_SCAN_FILES
AC6: Bare except clauses narrowed (MemoryError propagates)
"""
import inspect
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# --- AC1: Phase 0.5 Non-interactive ---

class TestPhase05NonInteractive:
    """Phase 0.5 Git Guard must not contain interactive prompts."""

    def test_no_ask_user_in_phase_05(self):
        """The playbook text must not instruct the agent to 'Ask the user'."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        PROJECT_INIT_PROMPT = COMMANDS_CONTENT["project-init.md"]
        # Find Phase 0.5 section
        lines = PROJECT_INIT_PROMPT.split('\n')
        in_phase_05 = False
        phase_05_text = []
        for line in lines:
            if 'Phase 0.5' in line:
                in_phase_05 = True
            elif in_phase_05 and line.startswith('## '):
                break
            if in_phase_05:
                phase_05_text.append(line)
        section = '\n'.join(phase_05_text)
        assert 'Ask the user' not in section, (
            "Phase 0.5 must not contain 'Ask the user' — it blocks in non-interactive contexts"
        )

    def test_phase_05_has_warning(self):
        """Phase 0.5 must print a warning when not in a git repo."""
        from pactkit.prompts.commands import COMMANDS_CONTENT
        PROJECT_INIT_PROMPT = COMMANDS_CONTENT["project-init.md"]
        lines = PROJECT_INIT_PROMPT.split('\n')
        in_phase_05 = False
        phase_05_text = []
        for line in lines:
            if 'Phase 0.5' in line:
                in_phase_05 = True
            elif in_phase_05 and line.startswith('## '):
                break
            if in_phase_05:
                phase_05_text.append(line)
        section = '\n'.join(phase_05_text)
        assert '⚠️' in section or 'warning' in section.lower(), (
            "Phase 0.5 must include a warning message for non-git directories"
        )


# --- AC2: Enterprise Flags Forwarded ---

class TestEnterpriseFlagsForwarded:
    """cli.py must forward --no-git, --no-external, --non-interactive to deploy()."""

    def test_init_forwards_no_git(self):
        """pactkit init --no-git must pass no_git=True to deploy()."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'init', '--no-git', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('no_git') is True

    def test_init_forwards_non_interactive(self):
        """pactkit init --non-interactive must pass non_interactive=True to deploy()."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'init', '--non-interactive', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('non_interactive') is True

    def test_init_forwards_no_external(self):
        """pactkit init --no-external must pass no_external=True to deploy()."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'init', '--no-external', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('no_external') is True

    def test_update_forwards_flags(self):
        """pactkit update --no-git --non-interactive must forward both flags."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'update', '--no-git', '--non-interactive', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('no_git') is True
            assert kwargs.get('non_interactive') is True


# --- AC3: deploy() Signature Updated ---

class TestDeploySignature:
    """deploy() must accept no_git, no_external, non_interactive without **_kwargs."""

    def test_deploy_accepts_enterprise_flags(self):
        """deploy() must accept all three enterprise flags without raising TypeError."""
        from pactkit.generators.deployer import deploy
        sig = inspect.signature(deploy)
        param_names = list(sig.parameters.keys())
        assert 'no_git' in param_names
        assert 'no_external' in param_names
        assert 'non_interactive' in param_names

    def test_deploy_no_kwargs_catchall(self):
        """deploy() must not use **_kwargs or **kwargs catch-all."""
        from pactkit.generators.deployer import deploy
        sig = inspect.signature(deploy)
        for param in sig.parameters.values():
            assert param.kind != inspect.Parameter.VAR_KEYWORD, (
                f"deploy() must not have **kwargs catch-all, found: **{param.name}"
            )

    def test_deploy_flags_default_false(self):
        """Enterprise flags must default to False."""
        from pactkit.generators.deployer import deploy
        sig = inspect.signature(deploy)
        assert sig.parameters['no_git'].default is False
        assert sig.parameters['no_external'].default is False
        assert sig.parameters['non_interactive'].default is False


# --- AC4: upgrade Subparser Parity ---

class TestUpgradeSubparserParity:
    """upgrade subparser must accept the same enterprise flags as init/update."""

    def test_upgrade_accepts_no_git(self):
        """pactkit upgrade --no-git must be accepted by argparse."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'upgrade', '--no-git', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('no_git') is True

    def test_upgrade_accepts_non_interactive(self):
        """pactkit upgrade --non-interactive must be accepted."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'upgrade', '--non-interactive', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('non_interactive') is True

    def test_upgrade_accepts_no_external(self):
        """pactkit upgrade --no-external must be accepted."""
        from pactkit.cli import main
        with patch('pactkit.generators.deployer.deploy') as mock_deploy, \
             patch('sys.argv', ['pactkit', 'upgrade', '--no-external', '-t', '/tmp/test']):
            main()
            mock_deploy.assert_called_once()
            _, kwargs = mock_deploy.call_args
            assert kwargs.get('no_external') is True


# --- AC5: Scan Truncation ---

class TestScanTruncation:
    """_scan_files() must enforce MAX_SCAN_FILES limit."""

    def _exec_visualize(self):
        from pactkit.prompts import VISUALIZE_SOURCE
        g = {}
        exec(VISUALIZE_SOURCE, g)
        return g

    def test_max_scan_files_constant_exists(self):
        """MAX_SCAN_FILES must be defined."""
        g = self._exec_visualize()
        assert 'MAX_SCAN_FILES' in g, "MAX_SCAN_FILES constant must exist in visualize.py"
        assert g['MAX_SCAN_FILES'] == 500

    def test_scan_truncates_at_limit(self, tmp_path):
        """_scan_files must return at most MAX_SCAN_FILES files."""
        g = self._exec_visualize()
        max_files = g['MAX_SCAN_FILES']

        # Create more than MAX_SCAN_FILES .py files
        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        for i in range(max_files + 50):
            (src_dir / f'mod_{i}.py').write_text(f'x = {i}', encoding='utf-8')

        all_files, _, _ = g['_scan_files'](tmp_path)
        assert len(all_files) <= max_files, (
            f"_scan_files returned {len(all_files)} files, expected <= {max_files}"
        )

    def test_scan_warning_on_truncation(self, tmp_path, capsys):
        """_scan_files must print a warning to stderr when truncating."""
        g = self._exec_visualize()
        max_files = g['MAX_SCAN_FILES']

        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        for i in range(max_files + 10):
            (src_dir / f'mod_{i}.py').write_text(f'x = {i}', encoding='utf-8')

        g['_scan_files'](tmp_path)
        captured = capsys.readouterr()
        assert 'truncated' in captured.err.lower() or 'Scan truncated' in captured.err, (
            "Expected truncation warning on stderr"
        )

    def test_scan_no_warning_under_limit(self, tmp_path, capsys):
        """No warning when file count is under the limit."""
        g = self._exec_visualize()

        src_dir = tmp_path / 'src'
        src_dir.mkdir()
        for i in range(5):
            (src_dir / f'mod_{i}.py').write_text(f'x = {i}', encoding='utf-8')

        g['_scan_files'](tmp_path)
        captured = capsys.readouterr()
        assert 'truncated' not in captured.err.lower()


# --- AC6: Narrow Exception Handling ---

class TestNarrowExceptionHandling:
    """Bare 'except: pass' must be replaced with specific exception types."""

    def test_no_bare_except_in_visualize_source(self):
        """visualize.py source must not contain 'except: pass'."""
        from pactkit.prompts import VISUALIZE_SOURCE
        # Check for bare except
        lines = VISUALIZE_SOURCE.split('\n')
        bare_excepts = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped == 'except: pass' or stripped == 'except:':
                bare_excepts.append(i)
        assert bare_excepts == [], (
            f"Found bare 'except: pass' at lines: {bare_excepts}. "
            "Use 'except (SyntaxError, UnicodeDecodeError, ValueError): pass' instead."
        )
