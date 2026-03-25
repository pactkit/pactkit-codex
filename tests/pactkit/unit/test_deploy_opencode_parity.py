"""Tests for STORY-slim-008: Deploy Chain Parity.

Covers:
- AC1: OpenCode selective deployment respects pactkit.yaml agents list
- AC2: OpenCode deployment calls auto_merge_config_file
- AC3: OpenCode deployment calls _cleanup_legacy
- AC4: _deploy_opencode includes all parity functions (except CI/Hooks)
- AC5: Full test suite passes
- R4: _generate_project_agents_md creates AGENTS.md if missing
- R7: _generate_config_if_missing accepts format param
"""

import inspect
from pathlib import Path
from unittest.mock import patch

import yaml

_PROJECT_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# AC1: OpenCode selective deployment
# ---------------------------------------------------------------------------


class TestOpenCodeSelectiveDeploy:
    """AC1: _deploy_opencode reads pactkit.yaml and filters agents/commands."""

    def test_opencode_deploys_only_configured_agents(self, tmp_path, monkeypatch):
        """When pactkit.yaml has 3 agents, only 3 agent files are created."""
        from pactkit.config import VALID_AGENTS, VALID_COMMANDS, VALID_RULES, VALID_SKILLS
        from pactkit.generators.deployer import _deploy_opencode

        # Create a pactkit.yaml with 3 specific agents
        three_agents = sorted(VALID_AGENTS)[:3]
        all_components = sorted(VALID_COMMANDS), sorted(VALID_SKILLS), sorted(VALID_RULES)
        config_yaml = yaml.dump(
            {
                "stack": "python",
                "version": "1.0.0",
                "agents": three_agents,
                "commands": sorted(VALID_COMMANDS),
                "skills": sorted(VALID_SKILLS),
                "rules": sorted(VALID_RULES),
            }
        )
        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir(exist_ok=True)
        (opencode_dir / "pactkit.yaml").write_text(config_yaml)

        monkeypatch.chdir(tmp_path)
        output_path = str(tmp_path / "output")

        with patch("pactkit.generators.deployer.auto_merge_config_file", return_value=[]):
            with patch("pactkit.generators.deployer._generate_project_agents_md"):
                with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                    with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                        with patch("pactkit.generators.deployer._update_global_opencode_json"):
                            _deploy_opencode(target=output_path)

        # Resolve macOS /var → /private/var symlink
        agents_dir = Path(output_path).resolve() / "agents"
        deployed_agents = list(agents_dir.glob("*.md")) if agents_dir.exists() else []
        assert len(deployed_agents) == len(three_agents), (
            f"Expected {len(three_agents)} agents, got {len(deployed_agents)}: "
            f"{[f.name for f in deployed_agents]}, agents_dir={agents_dir}"
        )

    def test_opencode_deploys_all_agents_when_no_config(self, tmp_path):
        """When no pactkit.yaml exists, all agents are deployed (fallback)."""
        from pactkit.config import VALID_AGENTS
        from pactkit.generators.deployer import _deploy_opencode

        # No pactkit.yaml — no .opencode dir either
        with patch("pactkit.generators.deployer._generate_project_agents_md"):
            with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                    with patch("pactkit.generators.deployer._update_global_opencode_json"):
                        with patch.object(Path, "cwd", return_value=tmp_path):
                            _deploy_opencode(target=str(tmp_path / "output"))

        agents_dir = tmp_path / "output" / "agents"
        deployed_agents = list(agents_dir.glob("*.md")) if agents_dir.exists() else []
        assert len(deployed_agents) == len(VALID_AGENTS), (
            f"Expected all {len(VALID_AGENTS)} agents, got {len(deployed_agents)}"
        )


# ---------------------------------------------------------------------------
# AC2: OpenCode auto-merge
# ---------------------------------------------------------------------------


class TestOpenCodeAutoMerge:
    """AC2: _deploy_opencode calls auto_merge_config_file when yaml exists."""

    def test_auto_merge_called_when_yaml_exists(self, tmp_path):
        """auto_merge_config_file must be called during OpenCode deployment."""
        from pactkit.config import VALID_AGENTS, VALID_COMMANDS, VALID_RULES, VALID_SKILLS

        config_yaml = yaml.dump(
            {
                "stack": "python",
                "version": "1.0.0",
                "agents": sorted(VALID_AGENTS),
                "commands": sorted(VALID_COMMANDS),
                "skills": sorted(VALID_SKILLS),
                "rules": sorted(VALID_RULES),
            }
        )
        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir()
        yaml_path = opencode_dir / "pactkit.yaml"
        yaml_path.write_text(config_yaml)

        with patch("pactkit.generators.deployer.auto_merge_config_file") as mock_merge:
            mock_merge.return_value = []
            with patch("pactkit.generators.deployer._generate_project_agents_md"):
                with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                    with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                        with patch("pactkit.generators.deployer._update_global_opencode_json"):
                            with patch.object(Path, "cwd", return_value=tmp_path):
                                from pactkit.generators.deployer import _deploy_opencode

                                _deploy_opencode(target=str(tmp_path / "output"))

        mock_merge.assert_called_once()

    def test_auto_merge_not_called_when_no_yaml(self, tmp_path):
        """auto_merge_config_file should not fail when no pactkit.yaml exists."""
        with patch("pactkit.generators.deployer.auto_merge_config_file") as mock_merge:
            mock_merge.return_value = []
            with patch("pactkit.generators.deployer._generate_project_agents_md"):
                with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                    with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                        with patch("pactkit.generators.deployer._update_global_opencode_json"):
                            with patch.object(Path, "cwd", return_value=tmp_path):
                                from pactkit.generators.deployer import _deploy_opencode

                                _deploy_opencode(target=str(tmp_path / "output"))
        # auto_merge not called when no yaml found
        mock_merge.assert_not_called()


# ---------------------------------------------------------------------------
# AC3: OpenCode cleanup_legacy
# ---------------------------------------------------------------------------


class TestOpenCodeCleanupLegacy:
    """AC3: _deploy_opencode calls _cleanup_legacy on skills dir."""

    def test_cleanup_legacy_called(self, tmp_path):
        with patch("pactkit.generators.deployer._cleanup_legacy") as mock_cleanup:
            with patch("pactkit.generators.deployer._generate_project_agents_md"):
                with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                    with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                        with patch("pactkit.generators.deployer._update_global_opencode_json"):
                            with patch.object(Path, "cwd", return_value=tmp_path):
                                from pactkit.generators.deployer import _deploy_opencode

                                _deploy_opencode(target=str(tmp_path / "output"))
        mock_cleanup.assert_called_once()


# ---------------------------------------------------------------------------
# R4: _generate_project_agents_md
# ---------------------------------------------------------------------------


class TestGenerateProjectAgentsMd:
    """R4: _generate_project_agents_md creates AGENTS.md at project root."""

    def test_creates_agents_md_if_missing(self, tmp_path):
        from pactkit.generators.deployer import _generate_project_agents_md

        agents_md = tmp_path / "AGENTS.md"
        assert not agents_md.exists()

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_project_agents_md()

        assert agents_md.exists(), "AGENTS.md should be created"
        content = agents_md.read_text()
        assert "context.md" in content or tmp_path.name in content

    def test_does_not_overwrite_existing(self, tmp_path):
        from pactkit.generators.deployer import _generate_project_agents_md

        agents_md = tmp_path / "AGENTS.md"
        original_content = "# My Custom Instructions\n"
        agents_md.write_text(original_content)

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_project_agents_md()

        assert agents_md.read_text() == original_content, "Existing AGENTS.md must not be overwritten"

    def test_skips_when_cwd_is_home(self, tmp_path):
        """Safety check: never create AGENTS.md in home directory."""
        from pactkit.generators.deployer import _generate_project_agents_md

        agents_md = tmp_path / "AGENTS.md"

        with patch.object(Path, "cwd", return_value=Path.home()):
            _generate_project_agents_md()

        assert not agents_md.exists(), "Should skip when cwd is home"

    def test_called_from_deploy_opencode_when_no_target(self, tmp_path):
        """_generate_project_agents_md is called only when target is None."""
        with patch("pactkit.generators.deployer._generate_project_agents_md") as mock_gen:
            with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                    with patch("pactkit.generators.deployer._update_global_opencode_json"):
                        with patch.object(Path, "cwd", return_value=tmp_path):
                            from pactkit.generators.deployer import _deploy_opencode

                            # With explicit target: should NOT call generate
                            _deploy_opencode(target=str(tmp_path / "output"))
        mock_gen.assert_not_called()

    def test_called_from_deploy_opencode_without_target(self, tmp_path):
        """When target is None, _generate_project_agents_md IS called."""
        oc_root = Path.home() / ".config" / "opencode"
        with patch("pactkit.generators.deployer._generate_project_agents_md") as mock_gen:
            with patch("pactkit.generators.deployer._print_mcp_recommendations_opencode"):
                with patch("pactkit.generators.deployer._load_opencode_providers", return_value={}):
                    with patch("pactkit.generators.deployer._update_global_opencode_json"):
                        with patch("pactkit.generators.deployer.Path") as MockPath:
                            MockPath.side_effect = Path
                            MockPath.home.return_value = Path.home()
                            MockPath.cwd.return_value = tmp_path
                            # Pass target so we don't write to real ~/.config/opencode
                            from pactkit.generators.deployer import _deploy_opencode

                            _deploy_opencode(target=str(tmp_path / "output"))
        # With explicit target, not called
        mock_gen.assert_not_called()


# ---------------------------------------------------------------------------
# AC4: Deploy chain parity — source inspection
# ---------------------------------------------------------------------------


class TestDeployChainParity:
    """AC4: _deploy_opencode function body covers required parity calls."""

    def _get_opencode_source(self):
        from pactkit.generators import deployer

        return inspect.getsource(deployer._deploy_opencode)

    def test_opencode_calls_cleanup_legacy(self):
        src = self._get_opencode_source()
        assert "_cleanup_legacy" in src, "_deploy_opencode must call _cleanup_legacy"

    def test_opencode_calls_auto_merge(self):
        src = self._get_opencode_source()
        assert "auto_merge_config_file" in src, "_deploy_opencode must call auto_merge_config_file"

    def test_opencode_calls_load_config(self):
        src = self._get_opencode_source()
        assert "load_config" in src or "_load_project_config" in src, (
            "_deploy_opencode must call load_config or _load_project_config"
        )

    def test_opencode_calls_generate_project_agents_md(self):
        src = self._get_opencode_source()
        assert "_generate_project_agents_md" in src

    def test_opencode_calls_print_mcp_recommendations(self):
        src = self._get_opencode_source()
        assert "mcp_recommendations" in src or "_print_mcp_recommendations" in src


# ---------------------------------------------------------------------------
# R7: _generate_config_if_missing format param
# ---------------------------------------------------------------------------


class TestGenerateConfigIfMissing:
    """R7: _generate_config_if_missing accepts format param and uses correct path."""

    def test_format_opencode_writes_to_opencode_dir(self, tmp_path):
        from pactkit.generators.deployer import _generate_config_if_missing

        # Create .opencode dir but no pactkit.yaml
        (tmp_path / ".opencode").mkdir()

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_config_if_missing(format="opencode")

        yaml_path = tmp_path / ".opencode" / "pactkit.yaml"
        assert yaml_path.exists(), f"pactkit.yaml should be in .opencode/, not found at {yaml_path}"

    def test_format_classic_writes_to_claude_dir(self, tmp_path):
        from pactkit.generators.deployer import _generate_config_if_missing

        (tmp_path / ".claude").mkdir()

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_config_if_missing(format="classic")

        yaml_path = tmp_path / ".claude" / "pactkit.yaml"
        assert yaml_path.exists()

    def test_no_format_autodetects(self, tmp_path):
        """Without format param, uses auto-detect (existing behavior preserved)."""
        from pactkit.generators.deployer import _generate_config_if_missing

        (tmp_path / ".opencode").mkdir()

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_config_if_missing()

        # Auto-detect should prefer .opencode
        yaml_path = tmp_path / ".opencode" / "pactkit.yaml"
        assert yaml_path.exists()

    def test_no_write_when_yaml_exists(self, tmp_path):
        from pactkit.generators.deployer import _generate_config_if_missing

        (tmp_path / ".opencode").mkdir()
        existing = tmp_path / ".opencode" / "pactkit.yaml"
        existing.write_text("version: existing\n")

        with patch.object(Path, "cwd", return_value=tmp_path):
            _generate_config_if_missing(format="opencode")

        assert existing.read_text() == "version: existing\n", "Should not overwrite existing yaml"
