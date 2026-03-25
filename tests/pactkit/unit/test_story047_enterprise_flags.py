"""
STORY-047: Enterprise Configuration Flags
Tests for enterprise config section (no_git, no_external, non_interactive, debug)
and CLI flags that override them.
"""
import warnings

# ===========================================================================
# R1: EnterpriseConfig dataclass
# ===========================================================================

class TestR1EnterpriseConfig:
    """EnterpriseConfig dataclass with correct defaults."""

    def test_import_enterprise_config(self):
        """EnterpriseConfig is importable from pactkit.config."""
        from pactkit.config import EnterpriseConfig  # noqa: F401

    def test_import_pactkit_config_has_enterprise(self):
        """PactKitConfig is importable from pactkit.config."""
        from pactkit.config import PactKitConfig  # noqa: F401

    def test_enterprise_config_defaults_all_false(self):
        """EnterpriseConfig() creates object with all-False defaults."""
        from pactkit.config import EnterpriseConfig
        cfg = EnterpriseConfig()
        assert cfg.no_git is False
        assert cfg.no_external is False
        assert cfg.non_interactive is False
        assert cfg.debug is False

    def test_enterprise_config_no_git_true(self):
        """EnterpriseConfig(no_git=True) creates object with no_git=True."""
        from pactkit.config import EnterpriseConfig
        cfg = EnterpriseConfig(no_git=True)
        assert cfg.no_git is True
        assert cfg.no_external is False

    def test_enterprise_config_no_external_true(self):
        """EnterpriseConfig(no_external=True) works."""
        from pactkit.config import EnterpriseConfig
        cfg = EnterpriseConfig(no_external=True)
        assert cfg.no_external is True

    def test_enterprise_config_non_interactive_true(self):
        """EnterpriseConfig(non_interactive=True) works."""
        from pactkit.config import EnterpriseConfig
        cfg = EnterpriseConfig(non_interactive=True)
        assert cfg.non_interactive is True

    def test_enterprise_config_debug_true(self):
        """EnterpriseConfig(debug=True) works."""
        from pactkit.config import EnterpriseConfig
        cfg = EnterpriseConfig(debug=True)
        assert cfg.debug is True


# ===========================================================================
# R1: PactKitConfig dataclass
# ===========================================================================

class TestR1PactKitConfig:
    """PactKitConfig has .enterprise attribute."""

    def test_pactkit_config_has_enterprise_attribute(self):
        """PactKitConfig has .enterprise attribute of type EnterpriseConfig."""
        from pactkit.config import EnterpriseConfig, PactKitConfig
        cfg = PactKitConfig()
        assert hasattr(cfg, 'enterprise')
        assert isinstance(cfg.enterprise, EnterpriseConfig)

    def test_pactkit_config_enterprise_defaults_all_false(self):
        """PactKitConfig().enterprise has all-False defaults."""
        from pactkit.config import PactKitConfig
        cfg = PactKitConfig()
        assert cfg.enterprise.no_git is False
        assert cfg.enterprise.no_external is False
        assert cfg.enterprise.non_interactive is False
        assert cfg.enterprise.debug is False

    def test_pactkit_config_accepts_enterprise_override(self):
        """PactKitConfig can be constructed with a custom EnterpriseConfig."""
        from pactkit.config import EnterpriseConfig, PactKitConfig
        ent = EnterpriseConfig(no_git=True, debug=True)
        cfg = PactKitConfig(enterprise=ent)
        assert cfg.enterprise.no_git is True
        assert cfg.enterprise.debug is True


# ===========================================================================
# R1: load_config parses enterprise section
# ===========================================================================

class TestR1LoadConfigEnterprise:
    """load_config parses enterprise section correctly."""

    def test_load_config_with_enterprise_section(self, tmp_path):
        """Loading a YAML with enterprise section parses correctly."""
        from pactkit.config import load_config

        yaml_content = """\
version: "0.0.1"
stack: python
agents: []
commands: []
skills: []
rules: []
enterprise:
  no_git: true
  no_external: false
  non_interactive: true
  debug: false
"""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(yaml_content)

        config = load_config(yaml_path)
        ent = config.get('enterprise', {})
        assert ent.get('no_git') is True
        assert ent.get('no_external') is False
        assert ent.get('non_interactive') is True
        assert ent.get('debug') is False

    def test_load_config_without_enterprise_returns_defaults(self, tmp_path):
        """Loading YAML without enterprise section returns default-like config."""
        from pactkit.config import load_config

        yaml_content = """\
version: "0.0.1"
stack: python
agents: []
commands: []
skills: []
rules: []
"""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(yaml_content)

        config = load_config(yaml_path)
        # enterprise section should not raise — either absent or default
        ent = config.get('enterprise', {})
        # If present, no_git should default to False
        if ent:
            assert ent.get('no_git', False) is False

    def test_validate_config_accepts_enterprise_section(self, tmp_path):
        """validate_config does not warn or raise on enterprise section."""
        from pactkit.config import load_config, validate_config

        yaml_content = """\
version: "0.0.1"
stack: python
agents:
  - senior-developer
commands:
  - project-act
skills:
  - pactkit-visualize
rules:
  - 01-core-protocol
enterprise:
  no_git: true
  no_external: false
  non_interactive: false
  debug: true
"""
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text(yaml_content)

        config = load_config(yaml_path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            validate_config(config)

        # No warnings about enterprise section
        enterprise_warnings = [
            w for w in caught
            if 'enterprise' in str(w.message).lower()
        ]
        assert len(enterprise_warnings) == 0


# ===========================================================================
# R2: CLI flags
# ===========================================================================

class TestR2CLIFlags:
    """CLI init and update have --no-git, --no-external, --non-interactive flags."""

    def _get_help(self, subcmd):
        """Get help text for a subcommand.

        Calls the pactkit CLI via its installed entry point script.
        Falls back to invoking the main() function directly via importlib
        if the pactkit binary is not found.
        """
        import io
        from contextlib import redirect_stderr, redirect_stdout
        from unittest.mock import patch

        from pactkit.cli import main

        buf = io.StringIO()
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                with patch('sys.argv', ['pactkit', subcmd, '--help']):
                    try:
                        main()
                    except SystemExit:
                        pass
        except SystemExit:
            pass
        return buf.getvalue()

    def test_init_has_no_git_flag(self):
        """pactkit init --help shows --no-git flag."""
        help_text = self._get_help('init')
        assert '--no-git' in help_text

    def test_init_has_no_external_flag(self):
        """pactkit init --help shows --no-external flag."""
        help_text = self._get_help('init')
        assert '--no-external' in help_text

    def test_init_has_non_interactive_flag(self):
        """pactkit init --help shows --non-interactive flag."""
        help_text = self._get_help('init')
        assert '--non-interactive' in help_text

    def test_update_has_no_git_flag(self):
        """pactkit update --help shows --no-git flag."""
        help_text = self._get_help('update')
        assert '--no-git' in help_text

    def test_update_has_no_external_flag(self):
        """pactkit update --help shows --no-external flag."""
        help_text = self._get_help('update')
        assert '--no-external' in help_text

    def test_update_has_non_interactive_flag(self):
        """pactkit update --help shows --non-interactive flag."""
        help_text = self._get_help('update')
        assert '--non-interactive' in help_text


# ===========================================================================
# R3: project-done.md playbook mentions enterprise.no_git
# ===========================================================================

class TestR3PlaybookEnterpriseCheck:
    """project-done.md Phase 4 mentions enterprise/no_git check."""

    def test_project_done_mentions_no_git(self):
        """project-done.md should mention enterprise.no_git in Phase 4."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        assert 'enterprise' in done_content.lower() or 'no_git' in done_content

    def test_project_done_has_git_operations_note(self):
        """project-done.md Phase 4 has a check about git operations being disabled."""
        from pactkit.prompts.commands import COMMANDS_CONTENT

        done_content = COMMANDS_CONTENT.get('project-done.md', '')
        # Either enterprise.no_git or a note about disabling git operations
        has_enterprise_check = (
            'enterprise.no_git' in done_content
            or ('enterprise' in done_content and 'no_git' in done_content)
        )
        assert has_enterprise_check, (
            "project-done.md should mention enterprise.no_git in Phase 4 git commit section"
        )
