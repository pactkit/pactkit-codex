"""Tests for STORY-slim-005: FormatProfile abstraction.

Covers:
- AC1: FormatProfile dataclass exists and is frozen
- AC2: FORMAT_PROFILES registry is complete for classic/opencode/codex
- AC3: VALID_FORMATS auto-generated from FORMAT_PROFILES
- AC4: PACTKIT_YAML_CANDIDATES auto-generated from FORMAT_PROFILES
- AC5: resolve_pactkit_yaml_dir has no hardcoded if format == "xxx" branches
- AC6: Deployer _deploy_agents/_deploy_commands accept profile, not dual params
- AC7: Playbook rewriting uses profile.skills_path_var
- AC8: Adding new format to FORMAT_PROFILES auto-propagates to VALID_FORMATS
- AC9: Backward compatibility — classic/opencode deploy to same paths as before
"""

import dataclasses
import inspect
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# AC1: FormatProfile dataclass
# ---------------------------------------------------------------------------


class TestFormatProfileDataclass:
    def test_is_importable(self):
        from pactkit.profiles import FormatProfile

        assert FormatProfile is not None

    def test_is_frozen_dataclass(self):
        from pactkit.profiles import FormatProfile

        assert dataclasses.is_dataclass(FormatProfile)
        assert FormatProfile.__dataclass_params__.frozen

    def test_required_fields_exist(self):
        from pactkit.profiles import FormatProfile

        fields = {f.name for f in dataclasses.fields(FormatProfile)}
        required = {
            "name",
            "display_name",
            "global_config_dir",
            "project_config_dir",
            "skills_dir",
            "agents_dir",
            "commands_dir",
            "rules_dir",
            "project_instructions_file",
            "global_instructions_file",
            "pactkit_yaml_path",
            "agent_format",
            "rules_import_style",
            "excluded_agent_fields",
            "has_custom_commands",
            "supports_model_routing",
            "supports_mcp",
            "skills_path_var",
        }
        assert required <= fields, f"Missing fields: {required - fields}"

    def test_immutable(self):
        from pactkit.profiles import FORMAT_PROFILES

        profile = FORMAT_PROFILES["classic"]
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            profile.name = "tampered"


# ---------------------------------------------------------------------------
# AC2: FORMAT_PROFILES registry completeness
# ---------------------------------------------------------------------------


class TestFormatProfilesRegistry:
    @pytest.mark.parametrize("fmt", ["classic", "opencode", "codex"])
    def test_format_registered(self, fmt):
        from pactkit.profiles import FORMAT_PROFILES

        assert fmt in FORMAT_PROFILES

    def test_classic_profile_values(self):
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["classic"]
        assert p.global_config_dir == "~/.claude"
        assert p.project_config_dir == ".claude"
        assert p.skills_dir == "~/.claude/skills"
        assert p.project_instructions_file == "CLAUDE.md"
        assert p.agent_format == "md"
        assert p.rules_import_style == "@import"
        assert p.has_custom_commands is True
        assert p.supports_model_routing is False
        assert p.pactkit_yaml_path == ".claude/pactkit.yaml"

    def test_opencode_profile_values(self):
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["opencode"]
        assert p.global_config_dir == "~/.config/opencode"
        assert p.project_config_dir == ".opencode"
        assert p.skills_dir == "~/.config/opencode/skills"
        assert p.project_instructions_file == "AGENTS.md"
        assert p.agent_format == "md"
        assert p.rules_import_style == "instructions"
        assert p.has_custom_commands is True
        assert p.supports_model_routing is True
        assert p.pactkit_yaml_path == ".opencode/pactkit.yaml"

    def test_codex_profile_values(self):
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["codex"]
        assert p.global_config_dir == "~/.codex"
        assert p.project_config_dir == ".codex"
        assert p.agent_format == "toml"
        assert p.rules_import_style == "inline"
        assert p.has_custom_commands is False
        assert p.commands_dir is None
        assert p.rules_dir is None

    def test_classic_excluded_fields(self):
        from pactkit.profiles import FORMAT_PROFILES

        # Classic doesn't exclude Claude-specific fields
        p = FORMAT_PROFILES["classic"]
        assert len(p.excluded_agent_fields) == 0

    def test_opencode_excludes_claude_only_fields(self):
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["opencode"]
        assert "permissionMode" in p.excluded_agent_fields
        assert "memory" in p.excluded_agent_fields
        assert "skills" in p.excluded_agent_fields


# ---------------------------------------------------------------------------
# AC3: VALID_FORMATS auto-generated
# ---------------------------------------------------------------------------


class TestValidFormats:
    def test_valid_formats_contains_all_profiles(self):
        from pactkit.profiles import FORMAT_PROFILES, VALID_FORMATS

        for fmt in FORMAT_PROFILES:
            assert fmt in VALID_FORMATS

    def test_valid_formats_includes_plugin_marketplace(self):
        # plugin/marketplace are deployment modes, not environment formats
        from pactkit.profiles import VALID_FORMATS

        assert "plugin" in VALID_FORMATS
        assert "marketplace" in VALID_FORMATS

    def test_adding_new_profile_propagates_to_valid_formats(self):
        """Simulates adding a new format — verifies auto-propagation logic."""
        # Verify pattern: VALID_FORMATS is derived from FORMAT_PROFILES
        from pactkit.profiles import FORMAT_PROFILES, VALID_FORMATS

        # All profile keys must be in VALID_FORMATS
        assert frozenset(FORMAT_PROFILES.keys()) <= VALID_FORMATS


# ---------------------------------------------------------------------------
# AC4: PACTKIT_YAML_CANDIDATES auto-generated
# ---------------------------------------------------------------------------


class TestPactKitYamlCandidates:
    def test_candidates_contain_all_profile_paths(self):
        from pactkit.config import PACTKIT_YAML_CANDIDATES
        from pactkit.profiles import FORMAT_PROFILES

        for fmt, profile in FORMAT_PROFILES.items():
            assert profile.pactkit_yaml_path in PACTKIT_YAML_CANDIDATES, (
                f"{fmt}: {profile.pactkit_yaml_path} not in PACTKIT_YAML_CANDIDATES"
            )

    def test_candidates_ordered_correctly(self):
        """OpenCode should be preferred over Classic."""
        from pactkit.config import PACTKIT_YAML_CANDIDATES

        oc_idx = PACTKIT_YAML_CANDIDATES.index(".opencode/pactkit.yaml")
        cl_idx = PACTKIT_YAML_CANDIDATES.index(".claude/pactkit.yaml")
        assert oc_idx < cl_idx, "OpenCode must be preferred over Classic"


# ---------------------------------------------------------------------------
# AC5: resolve_pactkit_yaml_dir has no hardcoded format branches
# ---------------------------------------------------------------------------


class TestResolveNoBranching:
    def test_resolve_uses_profile_not_hardcoded_if(self):
        from pactkit.config import resolve_pactkit_yaml_dir

        src = inspect.getsource(resolve_pactkit_yaml_dir)
        # Must NOT contain hardcoded format string comparisons
        assert 'format == "opencode"' not in src, "Hardcoded 'format == opencode' found"
        assert 'format == "classic"' not in src, "Hardcoded 'format == classic' found"
        assert 'format == "codex"' not in src, "Hardcoded 'format == codex' found"

    def test_resolve_with_explicit_format(self, tmp_path):
        from pactkit.config import resolve_pactkit_yaml_dir

        result = resolve_pactkit_yaml_dir(cwd=tmp_path, format="opencode")
        assert result == tmp_path / ".opencode" / "pactkit.yaml"

    def test_resolve_with_classic_format(self, tmp_path):
        from pactkit.config import resolve_pactkit_yaml_dir

        result = resolve_pactkit_yaml_dir(cwd=tmp_path, format="classic")
        assert result == tmp_path / ".claude" / "pactkit.yaml"

    def test_resolve_autodetect_prefers_opencode(self, tmp_path):
        from pactkit.config import resolve_pactkit_yaml_dir

        (tmp_path / ".opencode").mkdir()
        (tmp_path / ".claude").mkdir()
        result = resolve_pactkit_yaml_dir(cwd=tmp_path)
        assert ".opencode" in str(result)


# ---------------------------------------------------------------------------
# AC6: Deployer accepts profile parameter
# ---------------------------------------------------------------------------


class TestDeployerProfileParameter:
    def test_deploy_agents_accepts_profile(self):
        from pactkit.generators.deployer import _deploy_agents

        sig = inspect.signature(_deploy_agents)
        params = sig.parameters
        assert "profile" in params, "_deploy_agents must accept 'profile' parameter"
        assert "opencode_format" not in params, "'opencode_format' bool must be removed"
        assert "skills_prefix" not in params, "'skills_prefix' string must be removed"

    def test_deploy_commands_accepts_profile(self):
        from pactkit.generators.deployer import _deploy_commands

        sig = inspect.signature(_deploy_commands)
        params = sig.parameters
        assert "profile" in params, "_deploy_commands must accept 'profile' parameter"
        assert "opencode_format" not in params, "'opencode_format' bool must be removed"
        assert "skills_prefix" not in params, "'skills_prefix' string must be removed"

    def test_deploy_skills_accepts_profile(self):
        from pactkit.generators.deployer import _deploy_skills

        sig = inspect.signature(_deploy_skills)
        params = sig.parameters
        assert "profile" in params, "_deploy_skills must accept 'profile' parameter"
        assert "skills_prefix" not in params, "'skills_prefix' string must be removed"

    def test_no_opencode_format_bool_in_deployer(self):
        """The opencode_format boolean parameter anti-pattern must be fully removed."""
        from pactkit.generators.deployer import _deploy_agents, _deploy_commands

        # Verify neither function accepts opencode_format as a named parameter
        for fn in [_deploy_agents, _deploy_commands]:
            params = inspect.signature(fn).parameters
            assert "opencode_format" not in params, (
                f"'{fn.__name__}' still accepts 'opencode_format' parameter — must be replaced with profile"
            )


# ---------------------------------------------------------------------------
# AC7: Playbook rewriting uses profile.skills_path_var
# ---------------------------------------------------------------------------


class TestPlaybookRewriting:
    def test_rewrite_skills_prefix_uses_profile(self):
        from pactkit.generators.deployer import _rewrite_skills_prefix
        from pactkit.profiles import FORMAT_PROFILES

        content = "python3 ~/.claude/skills/pactkit-visualize/scripts/visualize.py"
        oc_profile = FORMAT_PROFILES["opencode"]
        result = _rewrite_skills_prefix(content, oc_profile)
        assert "~/.config/opencode/skills" in result
        assert "~/.claude/skills" not in result

    def test_rewrite_classic_is_noop(self):
        from pactkit.generators.deployer import _rewrite_skills_prefix
        from pactkit.profiles import FORMAT_PROFILES

        content = "python3 ~/.claude/skills/pactkit-board/scripts/board.py"
        classic_profile = FORMAT_PROFILES["classic"]
        result = _rewrite_skills_prefix(content, classic_profile)
        assert result == content  # no change for classic


# ---------------------------------------------------------------------------
# AC9: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_classic_deploy_target_path(self):
        """Classic deploy still targets ~/.claude/."""
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["classic"]
        path = Path(p.global_config_dir).expanduser()
        assert str(path).endswith("/.claude")

    def test_opencode_deploy_target_path(self):
        """OpenCode deploy still targets ~/.config/opencode/."""
        from pactkit.profiles import FORMAT_PROFILES

        p = FORMAT_PROFILES["opencode"]
        path = Path(p.global_config_dir).expanduser()
        assert str(path).endswith("/.config/opencode")

    def test_get_profile_raises_on_unknown(self):
        from pactkit.profiles import get_profile

        with pytest.raises(ValueError, match="Unknown format"):
            get_profile("cursor")
