"""Tests for STORY-006: config.toml Generator for MCP, Sandbox, and Hooks.

2026-08-13 policy change (user directive after two wipe incidents):
an existing config.toml is NEVER modified — PactKit only creates the file
when absent. Older merge/additive tests were replaced accordingly.
"""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import pytest


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    d = tmp_path / ".codex"
    d.mkdir()
    return d


class TestConfigToml:
    """AC1-AC5: config.toml creation for Codex CLI (file absent case)."""

    def _generate(self, codex_root):
        """Helper to generate config.toml."""
        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        return codex_root / "config.toml"

    def test_ac1_config_created_when_absent(self, codex_root):
        """AC1: config.toml created with sandbox_mode, approval_policy, and MCP (model left to Codex)."""
        config_path = self._generate(codex_root)
        assert config_path.exists()
        data = tomllib.loads(config_path.read_text())
        # model not set — Codex CLI fills it after login
        assert "sandbox_mode" in data
        assert "approval_policy" in data
        assert "mcp_servers" in data
        assert "context7" in data["mcp_servers"]

    def test_ac3_valid_toml(self, codex_root):
        """AC3: Output is valid TOML."""
        config_path = self._generate(codex_root)
        # tomllib.loads raises on invalid TOML
        data = tomllib.loads(config_path.read_text())
        assert isinstance(data, dict)

    def test_ac4_context7_url(self, codex_root):
        """AC4: Context7 MCP section has correct URL."""
        config_path = self._generate(codex_root)
        data = tomllib.loads(config_path.read_text())
        assert data["mcp_servers"]["context7"]["url"] == "https://mcp.context7.com/mcp"

    def test_ac5_no_secrets(self, codex_root):
        """AC5: No secrets written."""
        config_path = self._generate(codex_root)
        content = config_path.read_text()
        assert "api_key" not in content
        assert "OPENAI_API_KEY" not in content
        assert "organization" not in content

    def test_r3_defaults(self, codex_root):
        """R3: Default values match spec (model left to Codex CLI)."""
        config_path = self._generate(codex_root)
        data = tomllib.loads(config_path.read_text())
        # model not set by pactkit — Codex CLI fills it after login
        assert "model" not in data
        assert data["sandbox_mode"] == "workspace-write"
        assert data["approval_policy"] == "on-request"

    def test_r6_pactkit_managed_markers(self, codex_root):
        """R6: PactKit-managed comment markers present."""
        config_path = self._generate(codex_root)
        content = config_path.read_text()
        assert "[pactkit:managed]" in content


class TestNeverTouchExisting:
    """2026-08-13 user directive after two wipe incidents: an existing
    config.toml must stay byte-identical no matter what it contains."""

    def test_existing_file_byte_identical(self, codex_root):
        config_path = codex_root / "config.toml"
        original = (
            '# my hand-written config\n'
            'model = "gpt-5.6-sol"\n'
            '\n'
            '[mcp_servers.playwright]\n'
            'args = ["--yes", "@playwright/mcp@latest", "--headless"]\n'
            'command = "npx"\n'
        )
        config_path.write_text(original)

        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        assert config_path.read_text() == original  # byte-identical

    def test_user_model_and_custom_keys_untouched(self, codex_root):
        """Former R4 merge test: user values are preserved by not writing at all."""
        config_path = codex_root / "config.toml"
        original = 'model = "gpt-4o"\nmy_custom_key = "preserved"\napproval_policy = "auto-edit"\n'
        config_path.write_text(original)

        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        assert config_path.read_text() == original

    def test_unparsable_file_untouched(self, codex_root):
        config_path = codex_root / "config.toml"
        config_path.write_text("this is = not [ valid toml")

        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        assert config_path.read_text() == "this is = not [ valid toml"

    def test_missing_file_created_with_managed_sections(self, codex_root):
        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        content = (codex_root / "config.toml").read_text()
        assert "[pactkit:managed]" in content
        assert 'sandbox_mode = "workspace-write"' in content
        assert "[mcp_servers.context7]" in content
