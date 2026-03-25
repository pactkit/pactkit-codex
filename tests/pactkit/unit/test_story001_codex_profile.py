"""STORY-001: Codex FormatProfile and Deploy Orchestrator.

Tests for:
- AC1: CLI routes to _deploy_codex
- AC2: FormatProfile fields are correct
- AC3: "codex" is a valid format
- AC4: .codex/pactkit.yaml is a candidate path
- AC5: Existing deploy functions are unmodified (verified by no regression)
"""

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))


class TestCodexFormatProfile:
    """AC2: FormatProfile fields are correct."""

    def test_codex_global_config_dir(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].global_config_dir == "~/.codex"

    def test_codex_project_config_dir(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].project_config_dir == ".codex"

    def test_codex_skills_dir(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].skills_dir == "~/.codex/skills"

    def test_codex_commands_dir_is_none(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].commands_dir is None

    def test_codex_rules_dir_is_none(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].rules_dir is None

    def test_codex_prompts_dir(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].prompts_dir == "~/.codex/prompts"

    def test_codex_project_instructions_file(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].project_instructions_file == "AGENTS.md"

    def test_codex_rules_import_style(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].rules_import_style == "inline"

    def test_codex_has_custom_commands_true(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].has_custom_commands is True

    def test_codex_supports_mcp(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].supports_mcp is True

    def test_codex_display_name(self):
        from pactkit.profiles import FORMAT_PROFILES

        assert FORMAT_PROFILES["codex"].display_name == "Codex CLI"


class TestCodexValidFormat:
    """AC3: "codex" is a valid format."""

    def test_codex_in_valid_formats(self):
        from pactkit.profiles import VALID_FORMATS

        assert "codex" in VALID_FORMATS

    def test_get_profile_codex(self):
        from pactkit.profiles import get_profile

        profile = get_profile("codex")
        assert profile.name == "codex"


class TestCodexYamlCandidate:
    """AC4: .codex/pactkit.yaml is a candidate path."""

    def test_codex_yaml_in_candidates(self):
        from pactkit.profiles import PACTKIT_YAML_CANDIDATES

        assert ".codex/pactkit.yaml" in PACTKIT_YAML_CANDIDATES


class TestDeployCodexRouting:
    """AC1: CLI routes to _deploy_codex."""

    def test_deploy_codex_called(self):
        from pactkit.generators.deployer import deploy

        with patch("pactkit.generators.deployer._deploy_codex") as mock_deploy:
            deploy(format="codex", target="/tmp/test-codex")
            mock_deploy.assert_called_once_with("/tmp/test-codex")

    def test_deploy_codex_creates_directories(self, tmp_path):
        """_deploy_codex creates expected directory structure."""
        from pactkit.generators.deployer import _deploy_codex

        _deploy_codex(target=str(tmp_path))

        assert (tmp_path / "skills").is_dir()
        assert (tmp_path / "prompts").is_dir()

    def test_deploy_codex_writes_agents_md(self, tmp_path):
        """_deploy_codex generates AGENTS.md."""
        from pactkit.generators.deployer import _deploy_codex

        _deploy_codex(target=str(tmp_path))

        assert (tmp_path / "AGENTS.md").is_file()


class TestDeployCodexOCP:
    """AC5: Existing deploy functions are unmodified — verified via no regression."""

    def test_classic_deploy_still_works(self, tmp_path):
        from pactkit.generators.deployer import deploy

        deploy(format="classic", target=str(tmp_path))
        assert (tmp_path / "agents").is_dir()
        assert (tmp_path / "skills").is_dir()

    def test_opencode_deploy_still_works(self, tmp_path):
        from pactkit.generators.deployer import deploy

        deploy(format="opencode", target=str(tmp_path))
        assert (tmp_path / "agents").is_dir()
        assert (tmp_path / "skills").is_dir()
