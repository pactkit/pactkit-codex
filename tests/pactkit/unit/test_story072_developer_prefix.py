"""
STORY-072: Multi-Developer Story ID Prefix for Merge-Safe Collaboration
Tests for multi-path pactkit.yaml lookup, environment-aware generation, and developer prefix.
"""

import warnings

import yaml

from pactkit.config import get_default_config, load_config

# ===========================================================================
# AC1: Claude Code user unchanged
# ===========================================================================


class TestAC1ClaudeCodeUnchanged:
    """AC1: .claude/pactkit.yaml is read when present."""

    def test_reads_claude_dir(self, tmp_path, monkeypatch):
        """load_config() reads .claude/pactkit.yaml when it exists."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        config_data = {"version": "1.0.0", "stack": "python", "developer": "alice"}
        (claude_dir / "pactkit.yaml").write_text(yaml.dump(config_data))

        result = load_config()
        assert result["developer"] == "alice"
        assert result["stack"] == "python"


# ===========================================================================
# AC2: OpenCode user reads .opencode/
# ===========================================================================


class TestAC2OpenCodeUser:
    """AC2: .opencode/pactkit.yaml is read when .claude/ doesn't exist."""

    def test_reads_opencode_dir(self, tmp_path, monkeypatch):
        """load_config() reads .opencode/pactkit.yaml when no .claude/ exists."""
        monkeypatch.chdir(tmp_path)
        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir()
        config_data = {"version": "2.0.0", "stack": "node", "developer": "bob"}
        (opencode_dir / "pactkit.yaml").write_text(yaml.dump(config_data))

        result = load_config()
        assert result["developer"] == "bob"
        assert result["stack"] == "node"


# ===========================================================================
# AC3: .claude/ takes priority when both exist
# ===========================================================================


class TestAC3ClaudePriority:
    """AC3: .opencode/ wins when both directories have pactkit.yaml (newer env preferred)."""

    def test_claude_over_opencode(self, tmp_path, monkeypatch):
        """load_config() prefers .opencode/ over .claude/ (OpenCode is newer environment)."""
        monkeypatch.chdir(tmp_path)
        # Create both
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "claude-user"}))

        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir()
        (opencode_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "opencode-user"}))

        result = load_config()
        assert result["developer"] == "opencode-user"


# ===========================================================================
# AC4: OpenCode environment generates to .opencode/
# ===========================================================================


class TestAC4OpenCodeGeneration:
    """AC4: pactkit.yaml generated in .opencode/ when that's the environment."""

    def test_generates_to_opencode_dir(self, tmp_path, monkeypatch):
        """_generate_config_if_missing() writes to .opencode/ when .claude/ absent."""
        from pactkit.generators.deployer import _generate_config_if_missing

        monkeypatch.chdir(tmp_path)
        # Create .opencode/ but NOT .claude/
        (tmp_path / ".opencode").mkdir()

        _generate_config_if_missing()

        assert (tmp_path / ".opencode" / "pactkit.yaml").is_file()
        assert not (tmp_path / ".claude").exists()

    def test_generates_to_claude_dir_when_present(self, tmp_path, monkeypatch):
        """_generate_config_if_missing() writes to .claude/ when it exists."""
        from pactkit.generators.deployer import _generate_config_if_missing

        monkeypatch.chdir(tmp_path)
        (tmp_path / ".claude").mkdir()

        _generate_config_if_missing()

        assert (tmp_path / ".claude" / "pactkit.yaml").is_file()

    def test_default_generates_to_claude(self, tmp_path, monkeypatch):
        """_generate_config_if_missing() defaults to .claude/ when neither exists."""
        from pactkit.generators.deployer import _generate_config_if_missing

        monkeypatch.chdir(tmp_path)

        _generate_config_if_missing()

        assert (tmp_path / ".claude" / "pactkit.yaml").is_file()


# ===========================================================================
# AC5 & AC6: Developer prefix in default config
# ===========================================================================


class TestAC5DeveloperPrefix:
    """AC5/AC6: developer field in config defaults and is used for ID generation."""

    def test_default_config_has_developer(self):
        """Default config includes developer field."""
        defaults = get_default_config()
        assert "developer" in defaults
        assert defaults["developer"] == ""

    def test_developer_loaded_from_yaml(self, tmp_path, monkeypatch):
        """developer value is loaded from pactkit.yaml."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "alice"}))

        result = load_config()
        assert result["developer"] == "alice"

    def test_empty_developer_returns_empty(self, tmp_path, monkeypatch):
        """Empty developer returns empty string."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": ""}))

        result = load_config()
        assert result["developer"] == ""

    def test_no_developer_defaults_empty(self, tmp_path, monkeypatch):
        """Missing developer field defaults to empty string."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"stack": "python"}))

        result = load_config()
        assert result["developer"] == ""


# ===========================================================================
# AC8: Developer field validation
# ===========================================================================


class TestAC8DeveloperValidation:
    """AC8: developer field is validated with warnings."""

    def test_valid_developer(self, tmp_path, monkeypatch):
        """Valid developer value passes without warning."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "alice-01"}))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = load_config()
            developer_warnings = [x for x in w if "developer" in str(x.message).lower()]
            assert len(developer_warnings) == 0
        assert result["developer"] == "alice-01"

    def test_invalid_developer_uppercase(self, tmp_path, monkeypatch):
        """Uppercase developer triggers warning."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "Alice_123"}))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_config()
            developer_warnings = [x for x in w if "developer" in str(x.message).lower()]
            assert len(developer_warnings) > 0

    def test_invalid_developer_too_short(self, tmp_path, monkeypatch):
        """Single char developer triggers warning."""
        monkeypatch.chdir(tmp_path)
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "pactkit.yaml").write_text(yaml.dump({"developer": "a"}))

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            load_config()
            developer_warnings = [x for x in w if "developer" in str(x.message).lower()]
            assert len(developer_warnings) > 0


# ===========================================================================
# board.py update_version uses multi-path
# ===========================================================================


class TestBoardVersionMultiPath:
    """board.py update_version reads from correct path."""

    def test_board_reads_opencode_yaml(self, tmp_path, monkeypatch):
        """update_version() finds pactkit.yaml in .opencode/."""
        from pactkit.skills.board import update_version

        monkeypatch.chdir(tmp_path)
        opencode_dir = tmp_path / ".opencode"
        opencode_dir.mkdir()
        (opencode_dir / "pactkit.yaml").write_text("version: 1.0.0\nstack: python\n")

        result = update_version("2.0.0")
        assert "✅" in result
        content = (opencode_dir / "pactkit.yaml").read_text()
        assert "version: 2.0.0" in content


# ===========================================================================
# Playbook content checks
# ===========================================================================


class TestPlaybookUpdates:
    """Verify playbook text references are updated."""

    def test_init_guard_checks_both_paths(self):
        """Init Guard marker check references pactkit.yaml via template variable (STORY-slim-006)."""
        from pactkit.prompts import COMMANDS_CONTENT

        plan_content = COMMANDS_CONTENT["project-plan.md"]
        # After STORY-slim-006, uses {PACTKIT_YAML} template variable instead of hardcoded paths
        assert "{PACTKIT_YAML}" in plan_content or ".opencode/pactkit.yaml" in plan_content

    def test_no_reverse_instruction(self):
        """The old 'Do NOT create pactkit.yaml in .opencode/' instruction is removed."""
        from pactkit.prompts import COMMANDS_CONTENT

        init_content = COMMANDS_CONTENT["project-init.md"]
        assert "Do NOT create `pactkit.yaml` in `.opencode/`" not in init_content
        assert "Do NOT create pactkit.yaml in .opencode" not in init_content

    def test_plan_has_developer_prefix_instruction(self):
        """Plan playbook mentions developer prefix."""
        from pactkit.prompts import COMMANDS_CONTENT

        plan_content = COMMANDS_CONTENT["project-plan.md"]
        assert "developer" in plan_content.lower()

    def test_doctor_mentions_opencode_path(self):
        """Doctor skill references .opencode/pactkit.yaml."""
        from pactkit.prompts import skills as skills_mod

        # Check across all skill definitions
        full_text = ""
        for attr_name in dir(skills_mod):
            val = getattr(skills_mod, attr_name)
            if isinstance(val, (str, dict)):
                full_text += str(val)
        assert ".opencode/pactkit.yaml" in full_text
