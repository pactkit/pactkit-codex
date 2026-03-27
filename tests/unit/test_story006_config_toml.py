"""Tests for STORY-006: config.toml Generator for MCP, Sandbox, and Hooks."""

import tomllib

import pytest


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    d = tmp_path / ".codex"
    d.mkdir()
    return d


class TestConfigToml:
    """AC1-AC5: config.toml generation for Codex CLI."""

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

    def test_ac2_user_model_preserved_on_update(self, codex_root):
        """AC2: User's model choice is preserved on update."""
        config_path = codex_root / "config.toml"
        config_path.write_text('model = "gpt-4o"\n')

        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        data = tomllib.loads(config_path.read_text())
        assert data["model"] == "gpt-4o"  # User value preserved
        assert "mcp_servers" in data  # MCP added

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

    def test_r4_merge_preserves_user_keys(self, codex_root):
        """R4: Merge is additive-only for user fields."""
        config_path = codex_root / "config.toml"
        config_path.write_text(
            'model = "gpt-4o"\n'
            'my_custom_key = "preserved"\n'
            'approval_policy = "auto-edit"\n'
        )

        from pactkit_codex.deployer import CodexDeployer

        CodexDeployer.generate_codex_config_toml(codex_root)
        data = tomllib.loads(config_path.read_text())
        assert data["model"] == "gpt-4o"
        assert data["my_custom_key"] == "preserved"
        assert data["approval_policy"] == "auto-edit"
        # Missing keys added
        assert data["sandbox_mode"] == "workspace-write"

    def test_r6_pactkit_managed_markers(self, codex_root):
        """R6: PactKit-managed comment markers present."""
        config_path = self._generate(codex_root)
        content = config_path.read_text()
        assert "[pactkit:managed]" in content
