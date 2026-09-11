"""Tests for STORY-006: config.toml Generator for MCP, Sandbox, and Hooks.

2026-08-13 policy change (user directive after two wipe incidents):
an existing config.toml is NEVER modified — PactKit only creates the file
when absent. Older merge/additive tests were replaced accordingly.
"""

import pytest


@pytest.fixture
def codex_root(tmp_path):
    """Temporary codex root directory."""
    d = tmp_path / ".codex"
    d.mkdir()
    return d


# Retired with STORY-slim-20260911b2bbd79889e0 A2/R3+R4: a missing
# config.toml is no longer created (that creation existed to inject MCP
# entries and host-permission scalars). The byte-identical protection for
# existing files is unchanged and pinned below; the no-creation contract
# is pinned in tests/unit/test_a2_no_config_injection.py.

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

    # Retired with STORY-slim-20260911b2bbd79889e0 A2/R3: no creation.
