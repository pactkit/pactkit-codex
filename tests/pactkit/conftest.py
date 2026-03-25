"""
STORY-041 R5: Shared Test Fixtures

Centralized pytest fixtures for PactKit test suite.
"""
import os
import subprocess
import sys
from unittest.mock import patch

import pytest


@pytest.fixture
def deploy_env(tmp_path):
    """Pre-configured temp directory with Path.home() and Path.cwd() mocking.

    Usage:
        def test_deploy_something(deploy_env):
            with deploy_env as (home, cwd):
                # home and cwd are both tmp_path subdirectories
                deploy(...)
    """
    home_dir = tmp_path / "home"
    cwd_dir = tmp_path / "project"
    home_dir.mkdir()
    cwd_dir.mkdir()
    (cwd_dir / ".claude").mkdir()

    class DeployEnvContext:
        def __init__(self):
            self.home = home_dir
            self.cwd = cwd_dir
            self._patches = []

        def __enter__(self):
            self._patches = [
                patch('pactkit.generators.deployer.Path.home', return_value=self.home),
                patch('pactkit.generators.deployer.Path.cwd', return_value=self.cwd),
            ]
            for p in self._patches:
                p.start()
            return self.home, self.cwd

        def __exit__(self, *args):
            for p in self._patches:
                p.stop()

    return DeployEnvContext()


@pytest.fixture
def sample_config(tmp_path):
    """Writes a default pactkit.yaml to tmp and returns the path.

    Usage:
        def test_with_config(sample_config):
            config_path = sample_config(agents=['senior-developer'])
            # config_path is Path to pactkit.yaml
    """
    def _create_config(
        agents=None,
        commands=None,
        skills=None,
        rules=None,
        **extra
    ):
        from pactkit.config import generate_default_yaml

        # Create directory structure
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        config_path = claude_dir / "pactkit.yaml"

        # Generate default config
        config_content = generate_default_yaml()
        config_path.write_text(config_content)

        return config_path

    return _create_config


@pytest.fixture
def pactkit_cli(tmp_path):
    """Subprocess runner for pactkit CLI with env isolation.

    Usage:
        def test_cli_command(pactkit_cli):
            stdout, stderr, code = pactkit_cli("version")
            assert code == 0
    """
    def _run_cli(*args, cwd=None):
        # Determine how to invoke pactkit
        cmd = [sys.executable, "-m", "pactkit.cli"] + list(args)

        env = os.environ.copy()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or tmp_path,
            env=env,
        )
        return result.stdout, result.stderr, result.returncode

    return _run_cli


@pytest.fixture
def mock_deployer_paths(tmp_path):
    """Context manager that mocks Path.home() and Path.cwd() for deployer tests.

    Simpler alternative to deploy_env for tests that just need path mocking.

    Usage:
        def test_something(mock_deployer_paths):
            with mock_deployer_paths() as paths:
                # paths.home and paths.cwd are mocked
                ...
    """
    class PathMocks:
        def __init__(self):
            self.home = tmp_path / "mock_home"
            self.cwd = tmp_path / "mock_cwd"
            self.home.mkdir(exist_ok=True)
            self.cwd.mkdir(exist_ok=True)
            self._home_patch = None
            self._cwd_patch = None

        def __enter__(self):
            self._home_patch = patch('pactkit.generators.deployer.Path.home', return_value=self.home)
            self._cwd_patch = patch('pactkit.generators.deployer.Path.cwd', return_value=self.cwd)
            self._home_patch.start()
            self._cwd_patch.start()
            return self

        def __exit__(self, *args):
            self._cwd_patch.stop()
            self._home_patch.stop()

    def _create():
        return PathMocks()

    return _create
