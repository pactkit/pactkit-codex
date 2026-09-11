"""A missing Codex config is no longer an invitation to inject (A2/R3+R4).

STORY-slim-20260911b2bbd79889e0. `generate_codex_config_toml` created a fresh
config.toml whenever one was missing, seeding it with host-permission scalars
(`sandbox_mode`, `approval_policy`) and a `context7` MCP server. The umbrella
spec retires that: a missing config MUST NOT be created for the purpose of
injecting MCP entries or host-permission defaults. The user starts their own
config; PactKit's job is to say what it would have suggested, not to write it.

The existing-file byte-identical protection (2026-08-13 directive) is pinned
by test_story006 and unchanged.
"""

from __future__ import annotations


from pactkit_codex.deployer import CodexDeployer


class TestMissingConfigNotCreated:
    def test_missing_config_toml_is_not_created(self, tmp_path):
        CodexDeployer.generate_codex_config_toml(tmp_path)

        assert not (tmp_path / "config.toml").exists(), (
            "a missing config must stay missing — creating it for injection "
            "purposes is the retired behavior"
        )

    def test_missing_config_gets_a_suggestion_not_a_file(self, tmp_path, capsys):
        CodexDeployer.generate_codex_config_toml(tmp_path)

        out = capsys.readouterr().out
        assert "config.toml" in out
        assert "sandbox" in out.lower() or "workspace-write" in out

    def test_existing_config_stays_byte_identical(self, tmp_path):
        original = "# my config\nmodel = \"gpt-5.6\"\n"
        (tmp_path / "config.toml").write_text(original, encoding="utf-8")

        CodexDeployer.generate_codex_config_toml(tmp_path)

        assert (tmp_path / "config.toml").read_text(encoding="utf-8") == original

    def test_no_mcp_url_is_written_anywhere(self, tmp_path):
        """The suggestion may mention settings; it must not write a file, and
        nothing under the target may gain the injected MCP server."""
        CodexDeployer.generate_codex_config_toml(tmp_path)

        for path in tmp_path.rglob("*"):
            if path.is_file():
                assert "mcp.context7.com" not in path.read_text(encoding="utf-8"), path
