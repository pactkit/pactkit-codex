"""
STORY-001: Config Schema — pactkit.yaml load, validate, defaults.
"""

import warnings
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _config():
    from pactkit import config

    return config


# ===========================================================================
# Scenario 1: Default config when no YAML exists (S1)
# ===========================================================================


class TestGetDefaultConfig:
    def test_returns_dict(self):
        cfg = _config().get_default_config()
        assert isinstance(cfg, dict)

    def test_has_all_top_level_keys(self):
        cfg = _config().get_default_config()
        for key in ("version", "stack", "root", "agents", "commands", "skills", "rules"):
            assert key in cfg, f"Missing key: {key}"

    def test_default_agents_count(self):
        cfg = _config().get_default_config()
        assert len(cfg["agents"]) == 9

    def test_default_commands_count(self):
        # STORY-051: added project-release and project-pr → 11 commands
        cfg = _config().get_default_config()
        assert len(cfg["commands"]) == 11

    def test_default_skills_count(self):
        cfg = _config().get_default_config()
        assert len(cfg["skills"]) == 10

    def test_default_rules_count(self):
        """9 rule modules (added 09-sectional-write)."""
        cfg = _config().get_default_config()
        assert len(cfg["rules"]) == 9

    def test_default_stack_is_auto(self):
        cfg = _config().get_default_config()
        assert cfg["stack"] == "auto"

    def test_default_version(self):
        cfg = _config().get_default_config()
        assert isinstance(cfg["version"], str)

    def test_agents_are_strings(self):
        cfg = _config().get_default_config()
        assert all(isinstance(a, str) for a in cfg["agents"])

    def test_known_agents_present(self):
        cfg = _config().get_default_config()
        expected = {
            "system-architect",
            "senior-developer",
            "qa-engineer",
            "repo-maintainer",
            "system-medic",
            "security-auditor",
            "visual-architect",
            "code-explorer",
            "product-designer",
        }
        assert set(cfg["agents"]) == expected


class TestLoadConfigNoFile:
    """S1: load_config returns defaults when file doesn't exist."""

    def test_missing_file_returns_defaults(self, tmp_path):
        cfg = _config().load_config(tmp_path / "nonexistent.yaml")
        default = _config().get_default_config()
        assert cfg == default

    def test_missing_file_no_error(self, tmp_path):
        # Should not raise
        _config().load_config(tmp_path / "does_not_exist.yaml")


# ===========================================================================
# Scenario 2: Partial config merges with defaults (S2)
# ===========================================================================


class TestPartialConfigMerge:
    def test_partial_agents_only(self, tmp_path):
        yaml_path = tmp_path / "pactkit.yaml"
        yaml_path.write_text("agents:\n  - system-architect\n  - senior-developer\n")

        cfg = _config().load_config(yaml_path)
        assert cfg["agents"] == ["system-architect", "senior-developer"]
        # Other keys inherit defaults
        default = _config().get_default_config()
        assert cfg["commands"] == default["commands"]
        assert cfg["skills"] == default["skills"]
        assert cfg["rules"] == default["rules"]

    def test_partial_commands_only(self, tmp_path):
        yaml_path = tmp_path / "pactkit.yaml"
        yaml_path.write_text("commands:\n  - project-plan\n  - project-act\n")

        cfg = _config().load_config(yaml_path)
        assert cfg["commands"] == ["project-plan", "project-act"]
        default = _config().get_default_config()
        assert cfg["agents"] == default["agents"]

    def test_version_override(self, tmp_path):
        yaml_path = tmp_path / "pactkit.yaml"
        yaml_path.write_text('version: "2.0.0"\n')

        cfg = _config().load_config(yaml_path)
        assert cfg["version"] == "2.0.0"

    def test_stack_override(self, tmp_path):
        yaml_path = tmp_path / "pactkit.yaml"
        yaml_path.write_text("stack: python\n")

        cfg = _config().load_config(yaml_path)
        assert cfg["stack"] == "python"

    def test_empty_yaml_returns_defaults(self, tmp_path):
        yaml_path = tmp_path / "pactkit.yaml"
        yaml_path.write_text("")

        cfg = _config().load_config(yaml_path)
        default = _config().get_default_config()
        assert cfg == default


# ===========================================================================
# Scenario 3: Unknown name produces warning (S3)
# ===========================================================================


class TestValidateConfig:
    def test_unknown_agent_warns(self):
        cfg = _config().get_default_config()
        cfg["agents"] = ["unknown-agent"]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            warning_msgs = [str(x.message) for x in w]
            assert any("unknown-agent" in m for m in warning_msgs)

    def test_unknown_command_warns(self):
        cfg = _config().get_default_config()
        cfg["commands"] = ["project-foo"]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            warning_msgs = [str(x.message) for x in w]
            assert any("project-foo" in m for m in warning_msgs)

    def test_unknown_skill_warns(self):
        cfg = _config().get_default_config()
        cfg["skills"] = ["pactkit-unknown"]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            warning_msgs = [str(x.message) for x in w]
            assert any("pactkit-unknown" in m for m in warning_msgs)

    def test_unknown_rule_warns(self):
        cfg = _config().get_default_config()
        cfg["rules"] = ["99-unknown-rule"]
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            warning_msgs = [str(x.message) for x in w]
            assert any("99-unknown-rule" in m for m in warning_msgs)

    def test_valid_config_no_warning(self):
        cfg = _config().get_default_config()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            assert len(w) == 0

    def test_does_not_raise_on_unknown(self):
        cfg = _config().get_default_config()
        cfg["agents"] = ["totally-fake"]
        # Should not raise
        _config().validate_config(cfg)

    def test_invalid_stack_warns(self):
        cfg = _config().get_default_config()
        cfg["stack"] = "rust"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _config().validate_config(cfg)
            warning_msgs = [str(x.message) for x in w]
            assert any("rust" in m for m in warning_msgs)


# ===========================================================================
# Scenario 4: generate_default_yaml produces valid YAML (S4)
# ===========================================================================


class TestGenerateDefaultYaml:
    def test_returns_string(self):
        result = _config().generate_default_yaml()
        assert isinstance(result, str)

    def test_parseable_yaml(self):
        result = _config().generate_default_yaml()
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, dict)

    def test_roundtrip_equals_default(self):
        result = _config().generate_default_yaml()
        parsed = yaml.safe_load(result)
        default = _config().get_default_config()
        assert parsed == default

    def test_contains_comments(self):
        result = _config().generate_default_yaml()
        assert "#" in result


# ===========================================================================
# Scenario 5: Common mode fully removed (S5)
# ===========================================================================


class TestCommonModeRemoved:
    def test_no_common_user_module(self):
        src_dir = Path(__file__).resolve().parent.parent.parent / "src" / "pactkit"
        assert not (src_dir / "common_user.py").exists()

    def test_no_common_user_test(self):
        test_dir = Path(__file__).resolve().parent
        assert not (test_dir / "test_common_user.py").exists()

    def test_cli_no_common_mode_flag(self):
        # Verify common_user mode is not in the CLI
        # Note: --mode exists for visualize (HOTFIX-slim-023), but common_user is removed
        import inspect

        from pactkit.cli import main

        source = inspect.getsource(main)
        assert "common_user" not in source
        assert "common-user" not in source


# ===========================================================================
# Scenario 6: CLI accepts init without --mode (S6)
# ===========================================================================


class TestCLINoMode:
    def test_cli_has_no_mode_argument(self):
        """CLI init subparser should not accept --mode."""
        import inspect

        import pactkit.cli as cli_mod

        source = inspect.getsource(cli_mod)
        assert 'choices=["expert", "common"]' not in source

    def test_cli_no_import_common_user(self):
        import inspect

        import pactkit.cli as cli_mod

        source = inspect.getsource(cli_mod)
        assert "common_user" not in source


# ===========================================================================
# Constants validation
# ===========================================================================


class TestConstants:
    def test_valid_agents_constant_exists(self):
        assert hasattr(_config(), "VALID_AGENTS")
        assert isinstance(_config().VALID_AGENTS, (set, frozenset, list, tuple))

    def test_valid_commands_constant_exists(self):
        assert hasattr(_config(), "VALID_COMMANDS")

    def test_valid_skills_constant_exists(self):
        assert hasattr(_config(), "VALID_SKILLS")

    def test_valid_rules_constant_exists(self):
        assert hasattr(_config(), "VALID_RULES")

    def test_valid_stacks_constant_exists(self):
        assert hasattr(_config(), "VALID_STACKS")
        assert "auto" in _config().VALID_STACKS
        assert "python" in _config().VALID_STACKS
