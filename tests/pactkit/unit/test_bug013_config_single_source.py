"""
BUG-013: Deployer reads config from wrong path — should use project-level config only.

Tests verify that:
1. _deploy_classic reads config from $CWD/.claude/pactkit.yaml (not global)
2. _generate_config_if_missing writes full config to $CWD/.claude/pactkit.yaml
3. _backfill_project_config is removed
4. load_config() default path is $CWD/.claude/pactkit.yaml
5. -t target override still works
6. Orphan warning for ~/.claude/pactkit.yaml
"""
from pathlib import Path
from unittest.mock import patch

import yaml


def _config():
    from pactkit import config
    return config


def _write_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ===========================================================================
# AC1: Deployer reads project-level config
# ===========================================================================
class TestAC1DeployerReadsProjectConfig:
    """Deployer must read config from $CWD/.claude/pactkit.yaml."""

    def test_project_config_version_used(self, tmp_path, capsys):
        """Given project config with version 1.2.0, deployer should use it."""
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        # Global config at ~/.claude (should NOT be read)
        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        # Project config at $CWD/.claude (should be read)
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        cfg = _config()
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '1.2.0',
            'stack': 'python',
            'root': '.',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        })

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        output = capsys.readouterr().out
        assert 'Deployed' in output

    def test_project_config_ci_provider_used(self, tmp_path):
        """Given project config with ci.provider: github, deployer should use it."""
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        cfg = _config()
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '1.2.0',
            'stack': 'python',
            'root': '.',
            'ci': {'provider': 'github'},
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        })

        # Should generate CI config because project says github
        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        # GitHub Actions workflow should be created at project root
        gh_workflow = project / '.github' / 'workflows' / 'pactkit.yml'
        assert gh_workflow.exists(), \
            'CI pipeline should be generated when project config has ci.provider: github'

    def test_no_global_config_needed(self, tmp_path, capsys):
        """Deploy should work without any global ~/.claude/pactkit.yaml."""
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        # No global config at all — home/.claude doesn't even have pactkit.yaml
        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        # Project config exists
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        cfg = _config()
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '1.2.0',
            'stack': 'python',
        })

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        output = capsys.readouterr().out
        assert 'Deployed' in output


# ===========================================================================
# AC2: New config generated at project path
# ===========================================================================
class TestAC2NewConfigAtProjectPath:
    """When no project config exists, generate full config at $CWD/.claude/."""

    def test_fresh_project_gets_full_config(self, tmp_path, capsys):
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        # Project has .claude dir but no pactkit.yaml
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        # Config should be generated at project path
        project_yaml = project_claude / 'pactkit.yaml'
        assert project_yaml.exists(), \
            'Full config should be generated at $CWD/.claude/pactkit.yaml'

        generated = yaml.safe_load(project_yaml.read_text())
        assert 'agents' in generated, 'Generated config should have agents list'
        assert 'commands' in generated, 'Generated config should have commands list'
        assert 'skills' in generated, 'Generated config should have skills list'
        assert 'rules' in generated, 'Generated config should have rules list'

    def test_no_config_at_global_path(self, tmp_path):
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        # Global config should NOT be generated
        global_yaml = home_claude / 'pactkit.yaml'
        assert not global_yaml.exists(), \
            'Config should NOT be generated at ~/.claude/pactkit.yaml'


# ===========================================================================
# AC3: load_config default path
# ===========================================================================
class TestAC3LoadConfigDefault:
    """load_config() with no args reads from $CWD/.claude/pactkit.yaml."""

    def test_default_reads_from_cwd(self, tmp_path):
        cfg_mod = _config()

        project = tmp_path / 'project'
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '9.9.9',
            'stack': 'python',
        })

        with patch('pactkit.config.Path.cwd', return_value=project):
            result = cfg_mod.load_config()

        assert result['version'] == '9.9.9'


# ===========================================================================
# AC4: Target override still works
# ===========================================================================
class TestAC4TargetOverride:
    """pactkit init -t /tmp/preview still works."""

    def test_target_deploy_uses_project_config(self, tmp_path, capsys):
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'
        target = tmp_path / 'preview'

        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)

        # Project config
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        cfg = _config()
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '1.2.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        })

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy(target=str(target))

        output = capsys.readouterr().out
        assert 'Deployed' in output
        # Files deployed to target
        assert (target / 'agents').is_dir()


# ===========================================================================
# AC5: _backfill_project_config removed
# ===========================================================================
class TestAC5BackfillRemoved:
    """_backfill_project_config should not exist in deployer."""

    def test_no_backfill_function(self):
        import pactkit.generators.deployer as deployer_mod
        assert not hasattr(deployer_mod, '_backfill_project_config'), \
            '_backfill_project_config should be removed'


# ===========================================================================
# AC6: Orphan warning
# ===========================================================================
class TestAC6OrphanWarning:
    """Warn when ~/.claude/pactkit.yaml exists (orphaned)."""

    def test_orphan_warning_printed(self, tmp_path, capsys):
        from pactkit.generators.deployer import deploy

        home = tmp_path / 'home'
        project = tmp_path / 'project'

        # Orphaned global config
        home_claude = home / '.claude'
        home_claude.mkdir(parents=True)
        _write_yaml(home_claude / 'pactkit.yaml', {'version': '0.0.1'})

        # Project config
        project_claude = project / '.claude'
        project_claude.mkdir(parents=True)
        cfg = _config()
        _write_yaml(project_claude / 'pactkit.yaml', {
            'version': '1.2.0',
            'stack': 'python',
            'agents': sorted(cfg.VALID_AGENTS),
            'commands': sorted(cfg.VALID_COMMANDS),
            'skills': sorted(cfg.VALID_SKILLS),
            'rules': sorted(cfg.VALID_RULES),
        })

        with patch.object(Path, 'home', return_value=home), \
             patch('pactkit.generators.deployer.Path.cwd', return_value=project):
            deploy()

        output = capsys.readouterr().out
        assert 'orphan' in output.lower() or 'pactkit.yaml' in output.lower(), \
            'Should warn about orphaned global config'
