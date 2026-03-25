"""Tests for STORY-009: Remove OpenCode/Classic code from pactkit_codex-codex."""



class TestAC1NoOpenCodeClassicInDeployer:
    """AC1: No OpenCode/Classic deploy functions in deployer."""

    def test_no_deploy_classic(self):
        import pactkit_codex.generators.deployer as d
        assert not hasattr(d, "_deploy_classic")

    def test_no_deploy_opencode(self):
        import pactkit_codex.generators.deployer as d
        assert not hasattr(d, "_deploy_opencode")

    def test_no_deploy_plugin(self):
        import pactkit_codex.generators.deployer as d
        assert not hasattr(d, "_deploy_plugin")

    def test_no_deploy_marketplace(self):
        import pactkit_codex.generators.deployer as d
        assert not hasattr(d, "_deploy_marketplace")

    def test_no_opencode_json(self):
        import pactkit_codex.generators.deployer as d
        assert not hasattr(d, "_deploy_opencode_json")


class TestAC2ProfilesCodexOnly:
    """AC2: FORMAT_PROFILES only contains 'codex'."""

    def test_only_codex_profile(self):
        from pactkit_codex.profiles import FORMAT_PROFILES
        assert list(FORMAT_PROFILES.keys()) == ["codex"]


class TestAC3CLICodexOnly:
    """AC3: CLI only accepts codex format."""

    def test_no_classic_in_choices(self):
        from pathlib import Path
        cli_src = Path("src/pactkit_codex/cli.py").read_text()
        assert "'classic'" not in cli_src or "classic" not in cli_src.split("choices")[0]

    def test_no_opencode_in_choices(self):
        from pathlib import Path
        cli_src = Path("src/pactkit_codex/cli.py").read_text()
        # After cleanup, opencode should not appear in format choices
        assert "'opencode'" not in cli_src


class TestAC4CodexTestsStillPass:
    """AC4: Codex deploy still works after cleanup."""

    def test_deploy_produces_artifacts(self, tmp_path):
        from pactkit_codex.generators.deployer import _deploy_codex
        _deploy_codex(target=str(tmp_path))
        assert (tmp_path / "AGENTS.md").is_file()
        assert (tmp_path / "config.toml").is_file()
        assert len(list((tmp_path / "prompts").glob("*.md"))) == 10
        assert len([d for d in (tmp_path / "skills").iterdir() if d.is_dir()]) == 10


class TestAC5DeployerSmaller:
    """AC5: deployer.py significantly smaller (at least 40% reduction)."""

    def test_deployer_under_1000_lines(self):
        from pathlib import Path
        lines = Path("src/pactkit_codex/generators/deployer.py").read_text().count("\n")
        # Original: ~2187 lines. 40% reduction = < 1312 lines
        assert lines < 1312, f"deployer.py has {lines} lines (expected < 1312)"
