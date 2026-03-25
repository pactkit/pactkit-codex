"""
STORY-041 R3: Integration Test Example

Integration tests for deploy() with real filesystem I/O.
These tests are marked with @pytest.mark.integration and can be
excluded from fast test runs with: pytest -m "not integration"
"""
import pytest


@pytest.mark.integration
class TestDeployClassicIntegration:
    """Integration tests for classic format deployment."""

    def test_deploy_creates_directory_structure(self, tmp_path, deploy_env):
        """Deploy creates expected directory structure."""
        from pactkit.generators.deployer import deploy

        with deploy_env as (home, cwd):
            # Write minimal config
            config_path = cwd / ".claude" / "pactkit.yaml"
            config_path.write_text("skills: []\nrules: []\nagents: []\ncommands: []")

            # Deploy to home directory (classic mode)
            deploy(target=str(home / ".claude"))

            # Verify structure
            claude_dir = home / ".claude"
            assert claude_dir.exists()
            assert (claude_dir / "CLAUDE.md").exists()

    def test_deploy_plugin_format(self, tmp_path, deploy_env):
        """Deploy plugin format creates plugin.json."""
        from pactkit.generators.deployer import deploy

        with deploy_env as (home, cwd):
            # Write minimal config
            config_path = cwd / ".claude" / "pactkit.yaml"
            config_path.write_text("skills: []\nrules: []\nagents: []\ncommands: []")

            # Deploy plugin format
            plugin_dir = tmp_path / "plugin_test"
            deploy(target=str(plugin_dir), format="plugin")

            # Verify plugin structure
            assert (plugin_dir / ".claude-plugin" / "plugin.json").exists()

    def test_deploy_marketplace_format(self, tmp_path, deploy_env):
        """Deploy marketplace format creates marketplace.json."""
        from pactkit.generators.deployer import deploy

        with deploy_env as (home, cwd):
            # Write minimal config
            config_path = cwd / ".claude" / "pactkit.yaml"
            config_path.write_text("skills: []\nrules: []\nagents: []\ncommands: []")

            # Deploy marketplace format
            market_dir = tmp_path / "market_test"
            deploy(target=str(market_dir), format="marketplace")

            # Verify marketplace structure
            assert (market_dir / "marketplace.json").exists()
            assert (market_dir / "pactkit-plugin").is_dir()
