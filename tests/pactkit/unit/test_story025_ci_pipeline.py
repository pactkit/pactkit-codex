"""Tests for STORY-025: Conditional CI/CD Pipeline Generation.

AC1: Default config has ci: {provider: none}, no CI files
AC2: GitHub CI generation creates .github/workflows/pactkit.yml
AC3: GitLab CI generation creates .gitlab-ci.yml
AC4: provider: none generates no CI files
AC5: Invalid provider emits warning, treated as none
AC6: Missing ci section backward compatible
AC7: CI file content validation (pytest, lint, triggers)
"""
import sys
import warnings
from pathlib import Path

import yaml

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deploy_to(tmp_path, config=None):
    """Deploy PactKit to tmp_path and return the claude root (BUG-013: mock CWD)."""
    from unittest.mock import patch

    from pactkit.generators.deployer import deploy
    with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
        deploy(config=config, target=str(tmp_path / '.claude'))
    return tmp_path / '.claude'


# ===========================================================================
# AC1: Default Configuration — ci defaults to none, no CI files
# ===========================================================================

class TestAC1DefaultConfiguration:

    def test_default_config_has_ci_none(self):
        """get_default_config includes ci: {provider: none}."""
        from pactkit.config import get_default_config
        config = get_default_config()
        assert 'ci' in config
        assert config['ci'] == {'provider': 'none'}

    def test_default_yaml_contains_ci_section(self):
        """generate_default_yaml includes ci provider: none."""
        from pactkit.config import generate_default_yaml
        yaml_text = generate_default_yaml()
        assert 'ci:' in yaml_text
        assert 'provider: none' in yaml_text

    def test_default_deploy_no_ci_files(self, tmp_path):
        """Default deployment creates no CI files."""
        claude_root = _deploy_to(tmp_path)
        project_root_dir = tmp_path
        assert not (project_root_dir / '.github').exists()
        assert not (project_root_dir / '.gitlab-ci.yml').exists()


# ===========================================================================
# AC2: GitHub CI Generation
# ===========================================================================

class TestAC2GitHubCI:

    def test_github_ci_creates_workflow(self, tmp_path):
        """provider: github creates .github/workflows/pactkit.yml."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        assert workflow.exists(), '.github/workflows/pactkit.yml not created'

    def test_github_ci_is_valid_yaml(self, tmp_path):
        """Generated GitHub workflow is valid YAML."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        parsed = yaml.safe_load(workflow.read_text())
        assert isinstance(parsed, dict)

    def test_github_ci_contains_pytest(self, tmp_path):
        """GitHub workflow contains pytest command."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        content = workflow.read_text()
        assert 'pytest' in content

    def test_github_ci_contains_lint(self, tmp_path):
        """GitHub workflow contains linting command."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        content = workflow.read_text()
        # Should contain some form of lint command
        assert 'lint' in content.lower() or 'ruff' in content or 'eslint' in content


# ===========================================================================
# AC3: GitLab CI Generation
# ===========================================================================

class TestAC3GitLabCI:

    def test_gitlab_ci_creates_file(self, tmp_path):
        """provider: gitlab creates .gitlab-ci.yml in project root."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'gitlab'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        ci_file = tmp_path / '.gitlab-ci.yml'
        assert ci_file.exists(), '.gitlab-ci.yml not created'

    def test_gitlab_ci_is_valid_yaml(self, tmp_path):
        """Generated GitLab CI file is valid YAML."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'gitlab'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        ci_file = tmp_path / '.gitlab-ci.yml'
        parsed = yaml.safe_load(ci_file.read_text())
        assert isinstance(parsed, dict)

    def test_gitlab_ci_contains_test_stage(self, tmp_path):
        """GitLab CI contains test commands."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'gitlab'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        ci_file = tmp_path / '.gitlab-ci.yml'
        content = ci_file.read_text()
        assert 'pytest' in content or 'test' in content.lower()


# ===========================================================================
# AC4: None Provider — no CI files
# ===========================================================================

class TestAC4NoneProvider:

    def test_none_provider_no_github_dir(self, tmp_path):
        """provider: none does not create .github directory."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'none'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        assert not (tmp_path / '.github').exists()

    def test_none_provider_no_gitlab_file(self, tmp_path):
        """provider: none does not create .gitlab-ci.yml."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'none'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        assert not (tmp_path / '.gitlab-ci.yml').exists()


# ===========================================================================
# AC5: Invalid Provider Warning
# ===========================================================================

class TestAC5InvalidProviderWarning:

    def test_invalid_provider_emits_warning(self):
        """Invalid ci provider triggers a validation warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        config['ci'] = {'provider': 'jenkins'}
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            validate_config(config)
        msgs = [str(x.message) for x in w]
        assert any('jenkins' in m for m in msgs), (
            f'Expected warning about jenkins, got: {msgs}'
        )

    def test_valid_provider_no_warning(self):
        """Valid ci providers produce no warning."""
        from pactkit.config import get_default_config, validate_config
        config = get_default_config()
        for provider in ('github', 'gitlab', 'none'):
            config['ci'] = {'provider': provider}
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                validate_config(config)
            ci_warnings = [
                str(x.message) for x in w
                if 'ci' in str(x.message).lower() or 'provider' in str(x.message).lower()
            ]
            assert not ci_warnings, f'Unexpected CI warning for {provider}: {ci_warnings}'


# ===========================================================================
# AC6: Backward Compatibility
# ===========================================================================

class TestAC6BackwardCompatibility:

    def test_config_without_ci_loads_ok(self, tmp_path):
        """Config without ci section loads without error."""
        from pactkit.config import load_config
        yaml_path = tmp_path / 'pactkit.yaml'
        yaml_path.write_text('version: "1.0.0"\nstack: python\n')
        config = load_config(yaml_path)
        # ci should default to {provider: none}
        ci = config.get('ci', {'provider': 'none'})
        assert ci.get('provider') == 'none'

    def test_deploy_without_ci_section(self, tmp_path):
        """Deploy with config missing ci section succeeds."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config.pop('ci', None)
        from pactkit.generators.deployer import deploy
        # Should not raise
        deploy(config=config, target=str(tmp_path / '.claude'))
        # No CI files generated
        assert not (tmp_path / '.github').exists()


# ===========================================================================
# AC7: CI File Content Validation
# ===========================================================================

class TestAC7CIContentValidation:

    def test_github_ci_runs_on_ubuntu(self, tmp_path):
        """GitHub workflow uses ubuntu-latest runner."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        content = workflow.read_text()
        assert 'ubuntu-latest' in content

    def test_github_ci_triggers_on_push_and_pr(self, tmp_path):
        """GitHub workflow triggers on push to main and pull_request."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        content = workflow.read_text()
        assert 'push' in content
        assert 'pull_request' in content

    def test_github_ci_has_pytest_command(self, tmp_path):
        """GitHub workflow runs pytest tests/."""
        from pactkit.config import get_default_config
        config = get_default_config()
        config['ci'] = {'provider': 'github'}
        from unittest.mock import patch

        from pactkit.generators.deployer import deploy
        with patch('pactkit.generators.deployer.Path.cwd', return_value=tmp_path):
            deploy(config=config, target=str(tmp_path / '.claude'))
        workflow = tmp_path / '.github' / 'workflows' / 'pactkit.yml'
        content = workflow.read_text()
        assert 'pytest tests/' in content


# ===========================================================================
# VALID_CI_PROVIDERS constant
# ===========================================================================

class TestValidCIProviders:

    def test_valid_ci_providers_defined(self):
        from pactkit.config import VALID_CI_PROVIDERS
        assert 'github' in VALID_CI_PROVIDERS
        assert 'gitlab' in VALID_CI_PROVIDERS
        assert 'none' in VALID_CI_PROVIDERS
